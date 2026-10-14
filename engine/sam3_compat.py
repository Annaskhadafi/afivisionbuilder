"""Compatibility for SAM3 on CPU, Metal, and NVIDIA GPUs without BF16.

SAM3's image builder imports a CUDA-only tracking utility, precomputes CUDA
caches even for CPU, and uses several operators unavailable on Metal. Keep
the fixes local to SAM3; never replace torch operations or pretend that Triton
is installed.
"""
from __future__ import annotations

from contextlib import contextmanager, nullcontext
import importlib
import importlib.util
import sys
from types import FunctionType, MethodType, ModuleType


def _edt_cpu(data):
    """Equivalent batched EDT for the optional SAM interactive tracker."""
    import cv2
    import numpy as np
    import torch

    if data.ndim != 3:
        raise ValueError("SAM3 EDT expects a B x H x W tensor")
    masks = data.detach().cpu().numpy().astype(np.uint8)
    result = np.stack([
        cv2.distanceTransform(mask, cv2.DIST_L2, cv2.DIST_MASK_PRECISE)
        for mask in masks
    ]) if len(masks) else np.empty(masks.shape, dtype=np.float32)
    return torch.from_numpy(result).to(device=data.device)


def sam3_requires_portable_cuda(device):
    """Pre-Ampere GPUs cannot execute SAM3's forced BF16 operations."""
    if not str(device).startswith("cuda"):
        return False
    import torch
    return torch.cuda.get_device_capability(device)[0] < 8


def sam3_autocast(device):
    import torch
    if str(device).startswith("cuda") and not sam3_requires_portable_cuda(device):
        return torch.autocast(device_type="cuda", dtype=torch.bfloat16)
    return nullcontext()


def prepare_sam3_import(device=None):
    """Supply the tracking-only EDT without importing unavailable Triton."""
    if importlib.util.find_spec("triton") is None:
        name = "sam3.model.edt"
        if name not in sys.modules:
            module = ModuleType(name)
            module.edt_triton = _edt_cpu
            sys.modules[name] = module
    elif device is not None and str(device).startswith("cuda"):
        # Dispatch per input, so loading models on old and new GPUs in either
        # order does not force the modern GPU's tracking work onto the CPU.
        module = importlib.import_module("sam3.model.edt")
        original = module.edt_triton
        if not getattr(original, "_visonode_portable_edt", False):
            def compatible_edt(data):
                if data.device.type != "cuda" or sam3_requires_portable_cuda(data.device):
                    return _edt_cpu(data)
                return original(data)
            compatible_edt._visonode_portable_edt = True
            module.edt_triton = compatible_edt


@contextmanager
def sam3_build_device(builder, device):
    """Disable CUDA-only eager caches; normal forwards fill them lazily.

    The caller must hold its model construction lock for this temporary change.
    """
    if str(device).startswith("cuda"):
        yield
        return
    position_encoding = builder.PositionEmbeddingSine
    decoder = builder.TransformerDecoder

    def lazy_position_encoding(*args, **kwargs):
        kwargs["precompute_resolution"] = None
        return position_encoding(*args, **kwargs)

    def lazy_decoder(*args, **kwargs):
        kwargs["resolution"] = None
        return decoder(*args, **kwargs)

    builder.PositionEmbeddingSine = lazy_position_encoding
    builder.TransformerDecoder = lazy_decoder
    try:
        yield
    finally:
        builder.PositionEmbeddingSine = position_encoding
        builder.TransformerDecoder = decoder


def prepare_sam3_mps(model):
    """Use upstream real-valued rotary attention before moving buffers to MPS."""
    from sam3.model.vitdet import Attention

    for module in model.modules():
        if isinstance(module, Attention) and module.use_rope and not module.use_ve_rope:
            frequencies = module.freqs_cis
            if frequencies is not None and frequencies.is_complex():
                module.register_buffer("freqs_cis_real", frequencies.real.contiguous())
                module.register_buffer("freqs_cis_imag", frequencies.imag.contiguous())
                # Upstream checks this buffer for None, but the real path only
                # uses the two real buffers. A real placeholder can move to MPS.
                module.freqs_cis = frequencies.real.contiguous()
                module.use_rope_real = True


def _portable_mlp_forward(self, inputs):
    # Upstream fuses linear+GELU with a CUDA-oriented aten op and forces BF16.
    # Separate operators preserve FP32 on CPU, Metal, and pre-Ampere CUDA GPUs.
    output = self.act(self.fc1(inputs))
    output = self.norm(self.drop1(output))
    return self.drop2(self.fc2(output))


def _encode_boxes_without_empty_pooling(self, boxes, boxes_mask, boxes_labels, img_feats):
    # VisoNode uses text prompts, so there are no geometric boxes. Upstream
    # still pins a CPU scale tensor and calls ROIAlign on an empty batch;
    # neither operation is needed to produce the empty embedding sequence.
    if boxes.shape[0] == 0:
        return boxes.new_empty((0, boxes.shape[1], self.d_model)), boxes_mask
    from sam3.model.geometry_encoders import SequenceGeometryEncoder
    return SequenceGeometryEncoder._encode_boxes(self, boxes, boxes_mask, boxes_labels, img_feats)


def _mps_concat_padded_sequences(seq1, mask1, seq2, mask2, return_index=False):
    """SAM3's padded concatenation with synchronous Metal-compatible checks."""
    import torch

    length1, batch, hidden = seq1.shape
    length2 = seq2.shape[0]
    assert seq2.shape[1:] == (batch, hidden)
    assert mask1.shape == (batch, length1) and mask2.shape == (batch, length2)
    for mask in (mask1, mask2):
        if mask.shape[1] > 1 and bool((mask[:, :-1] & ~mask[:, 1:]).any().item()):
            raise AssertionError("SAM3 sequence masks must be right padded")
    actual1 = (~mask1).sum(-1)
    lengths = actual1 + (~mask2).sum(-1)
    mask = torch.arange(length1 + length2, device=seq2.device)[None] >= lengths[:, None]
    output = seq2.new_zeros((length1 + length2, batch, hidden))
    output[:length1] = seq1
    index = torch.arange(length2, device=seq2.device)[:, None] + actual1[None]
    output = output.scatter(0, index[:, :, None].expand(-1, -1, hidden), seq2)
    return (output, mask, index) if return_index else (output, mask)


def _bounded_attention(query, key, value, *args, **kwargs):
    import torch
    from torch.nn.functional import scaled_dot_product_attention

    # Each query attends to all keys; slicing queries changes no attention
    # semantics and avoids multi-GB intermediate matrices on Metal.
    if query.device.type == "mps" and query.shape[-2] > 256 and not args and not kwargs:
        return torch.cat([
            scaled_dot_product_attention(query[..., start:start + 256, :], key, value)
            for start in range(0, query.shape[-2], 256)
        ], dim=-2)
    return scaled_dot_product_attention(query, key, value, *args, **kwargs)


def _bind_forward_namespace(module, original, replacements):
    namespace = dict(original.__globals__)
    namespace.update(replacements)
    forward = FunctionType(
        original.__code__, namespace, original.__name__,
        original.__defaults__, original.__closure__,
    )
    forward.__kwdefaults__ = original.__kwdefaults__
    module.forward = MethodType(forward, module)


class _CpuImageTransform:
    def __init__(self, transform):
        self.transform = transform

    def __call__(self, image):
        # torchvision's uint8 resize rounds differently on CPU and MPS. A
        # one-level pixel difference can materially change SAM3's presence
        # confidence. Preprocess consistently, then run the network on Metal.
        return self.transform(image.cpu()).to(image.device)


def prepare_sam3_processor(processor, device):
    if str(device) == "mps" and not isinstance(processor.transform, _CpuImageTransform):
        processor.transform = _CpuImageTransform(processor.transform)


def prepare_sam3_model(model, device):
    """Adapt this model when its device lacks SAM3's native fused operators."""
    portable_cuda = sam3_requires_portable_cuda(device)
    if str(device).startswith("cuda") and not portable_cuda:
        return
    from sam3.model.vitdet import Attention, Mlp
    from sam3.model.geometry_encoders import SequenceGeometryEncoder

    for module in model.modules():
        if isinstance(module, Mlp):
            module.forward = MethodType(_portable_mlp_forward, module)
        elif isinstance(module, SequenceGeometryEncoder) and not portable_cuda:
            module._encode_boxes = MethodType(_encode_boxes_without_empty_pooling, module)
            if str(device) == "mps":
                # Give this model's forward its own global namespace so other
                # SAM3 instances (especially CUDA) keep the upstream function.
                _bind_forward_namespace(module, SequenceGeometryEncoder.forward, {
                    "concat_padded_sequences": _mps_concat_padded_sequences,
                })
        elif isinstance(module, Attention) and str(device) == "mps":
            import torch.nn.functional as functional
            scoped_functional = ModuleType("sam3_mps_functional")
            scoped_functional.__dict__.update(vars(functional))
            scoped_functional.scaled_dot_product_attention = _bounded_attention
            _bind_forward_namespace(module, Attention.forward, {"F": scoped_functional})
    if str(device) == "mps":
        prepare_sam3_mps(model)
