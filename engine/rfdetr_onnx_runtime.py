"""CPU executor for full RF-DETR ONNX exports (dets, labels, optional masks).

Input is RGB NCHW with ImageNet normalization, as in RF-DETR export inference.
No torch import or host-to-GPU transfer is needed on this path.
"""
from pathlib import Path
import json


class RFDETRONNXRuntime:
    def __init__(self, model_path: Path, image_size: int = 0, threads: int = 0):
        try:
            import onnxruntime as ort
        except ImportError as exc:
            raise RuntimeError("ONNX Runtime is not installed. Install onnxruntime in the VisoNode AI runtime.") from exc
        if threads < 0:
            raise RuntimeError("ONNX CPU thread count must be zero (automatic) or a positive integer.")
        options = ort.SessionOptions()
        options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        options.intra_op_num_threads = threads
        # Cached sessions can coexist for multiple nodes: idle pools should not
        # consume cores while another model or the preview is processing.
        options.add_session_config_entry("session.intra_op.allow_spinning", "0")
        self.session = ort.InferenceSession(str(model_path), sess_options=options, providers=["CPUExecutionProvider"])
        metadata = self.session.get_modelmeta().custom_metadata_map
        self.class_names = []
        if metadata.get("visonode.classes"):
            try:
                names = json.loads(metadata["visonode.classes"])
                if isinstance(names, list):
                    self.class_names = [str(name) for name in names]
            except (ValueError, TypeError):
                pass
        inputs = self.session.get_inputs()
        if len(inputs) != 1 or len(inputs[0].shape) != 4:
            raise RuntimeError("RF-DETR ONNX requires one NCHW image input.")
        model_input = inputs[0]
        if model_input.type != "tensor(float)":
            raise RuntimeError("CPU RF-DETR ONNX requires an FP32 image input. Export the model for CPU again.")
        shape = model_input.shape
        if shape[1] != 3:
            raise RuntimeError(f"RF-DETR ONNX requires three RGB channels, got {shape}.")
        self.batch_size = shape[0] if isinstance(shape[0], int) and shape[0] > 0 else 0
        self.height, self.width = [dim if isinstance(dim, int) and dim > 0 else image_size for dim in shape[2:]]
        if self.height <= 0 or self.width <= 0:
            raise RuntimeError("This ONNX model has dynamic spatial dimensions; select an explicit RF-DETR image size.")
        self.input_shape = (self.batch_size or 1, 3, self.height, self.width)
        self.input_name = model_input.name
        names = [output.name for output in self.session.get_outputs()]
        self.dets_name = next((name for name in names if name.lower() in ("dets", "boxes", "pred_boxes")), None)
        self.labels_name = next((name for name in names if name.lower() in ("labels", "logits", "pred_logits")), None)
        self.masks_name = next((name for name in names if name.lower() in ("masks", "mask", "pred_masks")), None)
        if not self.dets_name or not self.labels_name:
            raise RuntimeError(f"Select a full RF-DETR ONNX export with 'dets' and 'labels' outputs; found {names}.")
        self.output_names = [self.dets_name, self.labels_name] + ([self.masks_name] if self.masks_name else [])

    def _preprocess(self, frames):
        import cv2
        import numpy as np
        batch = np.empty((len(frames), 3, self.height, self.width), dtype=np.float32)
        mean = np.asarray((0.485, 0.456, 0.406), dtype=np.float32).reshape(3, 1, 1)
        std = np.asarray((0.229, 0.224, 0.225), dtype=np.float32).reshape(3, 1, 1)
        for index, frame in enumerate(frames):
            resized = cv2.resize(frame, (self.width, self.height), interpolation=cv2.INTER_LINEAR)
            batch[index] = resized[:, :, ::-1].transpose(2, 0, 1)
        batch /= 255.0
        batch -= mean
        batch /= std
        return batch

    def infer(self, frames):
        import numpy as np
        if not frames:
            return [], [], None
        chunk_size = self.batch_size or len(frames)
        collected = [[] for _ in self.output_names]
        for offset in range(0, len(frames), chunk_size):
            chunk = frames[offset:offset + chunk_size]
            count = len(chunk)
            if self.batch_size and count < chunk_size:
                chunk = chunk + [chunk[-1]] * (chunk_size - count)
            outputs = self.session.run(self.output_names, {self.input_name: self._preprocess(chunk)})
            for target, output in zip(collected, outputs):
                if output.shape[0] != len(chunk):
                    raise RuntimeError("RF-DETR ONNX output batch does not match its image input.")
                target.append(output[:count])
        outputs = [parts[0] if len(parts) == 1 else np.concatenate(parts) for parts in collected]
        return outputs[0], outputs[1], outputs[2] if self.masks_name else None
