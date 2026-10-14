"""Conservative compile-time folding of RF-DETR's constant spatial-shape graph.

ML dependencies are imported only in the isolated conversion interpreter. No
model input or learned computation is approximated, sampled or made constant.
"""
from __future__ import annotations

import copy

SPATIAL_SHAPES_TENSOR = "/transformer/ScatterND_1_output_0"
_SHAPE_OPERATORS = frozenset({
    "Constant", "Cast", "Shape", "Slice", "Concat", "Reshape", "ConstantOfShape",
    "Mul", "Equal", "Where", "Expand", "Add", "Tile", "Unsqueeze", "ScatterND",
    "Gather", "Squeeze", "Split", "Sub", "Div", "ReduceProd", "Transpose",
})


def resolve_static_shape_gathers(model, tensor_name: str):
    """Resolve selected, proven integer dimensions without freezing batch symbols.

    Only Shape -> Gather ancestors of the requested shape tensor are considered.
    Symbolic inference proves dimensions from ONNX operators and declared input
    shapes; no sample input, learned activation or inferred batch value is used.
    The inferred graph itself is never returned, preserving source metadata.
    """
    import numpy as np
    import onnx
    from onnx import numpy_helper
    from onnxruntime.tools.symbolic_shape_infer import SymbolicShapeInference

    producers = {output: node for node in model.graph.node for output in node.output}
    graph_inputs = {value.name for value in model.graph.input}
    constants = {value.name: numpy_helper.to_array(value) for value in model.graph.initializer
                 if value.name not in graph_inputs}
    for node in model.graph.node:
        if (node.op_type == "Constant" and node.domain in ("", "ai.onnx") and
                len(node.output) == 1 and node.output[0] not in graph_inputs):
            value = next((attribute for attribute in node.attribute if attribute.name == "value"), None)
            if value is not None:
                constants[node.output[0]] = numpy_helper.to_array(value.t)

    ancestors = set()
    def visit(name):
        if name in ancestors or name not in producers:
            return
        ancestors.add(name)
        node = producers[name]
        # Shape reads dimensions; following its data input would traverse learned
        # computation and consider unrelated gathers outside this shape graph.
        if node.op_type != "Shape":
            for source in node.input:
                visit(source)
    visit(tensor_name)
    inferred = SymbolicShapeInference.infer_shapes(copy.deepcopy(model), auto_merge=True,
                                                    guess_output_rank=False, verbose=0)
    dimensions = {
        value.name: [dimension.dim_value if dimension.HasField("dim_value") else None
                     for dimension in value.type.tensor_type.shape.dim]
        for value in (*inferred.graph.input, *inferred.graph.value_info, *inferred.graph.output)
        if value.type.HasField("tensor_type") and value.type.tensor_type.HasField("shape")
    }
    replacements, reports = {}, []
    for name in sorted(ancestors):
        node = producers[name]
        if node.op_type != "Gather" or node.domain not in ("", "ai.onnx") or len(node.output) != 1:
            continue
        shape = producers.get(node.input[0])
        if (shape is None or shape.op_type != "Shape" or shape.domain not in ("", "ai.onnx") or
                shape.attribute or any(attribute.name != "axis" or attribute.i != 0 for attribute in node.attribute)):
            continue
        values, indices = dimensions.get(shape.input[0]), constants.get(node.input[1])
        if values is None or indices is None or indices.dtype.kind not in "iu":
            continue
        try:
            selected = np.asarray(values, dtype=object)[indices]
        except IndexError:
            continue
        selected = np.asarray(selected, dtype=object)
        if any(value is None for value in selected.flat):
            continue
        replacements[name] = np.asarray(selected, dtype=np.int64)
        reports.append({"tensor": name, "shapeInput": shape.input[0], "indices": indices.tolist(),
                        "constant": replacements[name].tolist()})
    resolved = copy.deepcopy(model)
    retained = [node for node in resolved.graph.node if not any(name in replacements for name in node.output)]
    del resolved.graph.node[:]
    resolved.graph.node.extend(retained)
    for name, value in replacements.items():
        resolved.graph.initializer.append(numpy_helper.from_array(value, name))
    onnx.checker.check_model(resolved)
    return resolved, sorted(reports, key=lambda item: item["tensor"])


def fold_constant(model, tensor_name: str, *, resolve_static_dimensions: bool = False):
    """Evaluate an allowlisted, input-independent subgraph or raise ValueError."""
    import onnx
    import onnxruntime as ort
    from onnx import numpy_helper

    if resolve_static_dimensions:
        resolved, dimensions = resolve_static_shape_gathers(model, tensor_name)
        folded, report = fold_constant(resolved, tensor_name)
        return folded, {**report, "resolvedStaticDimensions": dimensions}

    producers = {output: node for node in model.graph.node for output in node.output}
    initializers = {item.name: item for item in model.graph.initializer}
    graph_inputs = {item.name for item in model.graph.input}
    required, roots = set(), set()

    def visit(name):
        if name in required or not name:
            return
        required.add(name)
        # An initializer can also be an overridable graph input; never freeze it.
        if name in graph_inputs:
            roots.add(name)
            return
        if name in initializers:
            return
        node = producers.get(name)
        if node is None:
            roots.add(name)
            return
        if node.domain not in ("", "ai.onnx") or node.op_type not in _SHAPE_OPERATORS:
            raise ValueError(f"Constant shape folding excludes operator {node.domain}:{node.op_type}")
        for source in node.input:
            visit(source)

    visit(tensor_name)
    if roots or tensor_name not in producers:
        raise ValueError(f"Cannot fold {tensor_name}: graph input dependencies {sorted(roots)}")
    nodes = [node for node in model.graph.node if any(name in required for name in node.output)]
    constant_graph = onnx.helper.make_graph(nodes, "constant-shapes", [],
        [onnx.helper.make_empty_tensor_value_info(tensor_name)],
        [value for name, value in initializers.items() if name in required])
    submodel = onnx.helper.make_model(constant_graph, opset_imports=model.opset_import, ir_version=model.ir_version)
    submodel = onnx.shape_inference.infer_shapes(submodel)
    onnx.checker.check_model(submodel)
    options = ort.SessionOptions()
    options.intra_op_num_threads = 2
    session = ort.InferenceSession(submodel.SerializeToString(), sess_options=options, providers=["CPUExecutionProvider"])
    value = session.run([tensor_name], {})[0]
    if len(producers[tensor_name].output) != 1:
        raise ValueError("Target producer has multiple outputs; explicit handling required")
    folded = copy.deepcopy(model)
    retained = [node for node in folded.graph.node if tensor_name not in node.output]
    del folded.graph.node[:]
    folded.graph.node.extend(retained)
    folded.graph.initializer.append(numpy_helper.from_array(value, tensor_name))
    onnx.checker.check_model(folded)
    return folded, {"tensor": tensor_name, "constant": value.tolist(), "dtype": str(value.dtype),
                    "ancestorTensors": len(required), "inputDependencies": []}


def fold_rfdetr_spatial_shapes(model):
    """Optional optimization: unfamiliar or unsafe RF-DETR exports are a no-op."""
    if not any(SPATIAL_SHAPES_TENSOR in node.output for node in model.graph.node):
        return model, {"folded": False, "reason": "No matching RF-DETR spatial-shape subgraph"}
    try:
        folded, report = fold_constant(model, SPATIAL_SHAPES_TENSOR)
    except ValueError as exc:
        return model, {"folded": False, "reason": str(exc)}
    return folded, {"folded": True, **report}
