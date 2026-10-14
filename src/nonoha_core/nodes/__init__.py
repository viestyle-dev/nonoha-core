from . import (
    adapter_nodes,
    arithmetic_operation_nodes,
    array_manipulation_nodes,
    bit_wise_operation_nodes,
    buffer_nodes,
    bytes_nodes,
    fft_nodes,
    filter_nodes,
    flow_control_nodes,
    graph_nodes,
    indexing_nodes,
    logic_function_nodes,
    mathematical_function_nodes,
    random_nodes,
    script_nodes,
    statistics_nodes,
    string_nodes,
    time_nodes,
    trigonometric_nodes,
    value_nodes,
    wave_generator,
    window_nodes,
)

from nonoha_core.node_registry import NodeRegistry


def register_nodes(registry: NodeRegistry):
    # Bytes
    registry.register_node("BytesValue", bytes_nodes.BytesValueNode)
    registry.register_node("BytesInplaceInsert", bytes_nodes.BytesInplaceInsertNode)
    registry.register_node("ToBytes", bytes_nodes.ToBytesNode)
    registry.register_node("ToBytesString", bytes_nodes.ToBytesStringNode)

    # Filter (numpy-based only)
    registry.register_node("EmaFilter", filter_nodes.EmaFilterNode)

    # Statistics
    registry.register_node("Mean", statistics_nodes.MeanNode)
    registry.register_node("IncrementalMean", statistics_nodes.IncrementalMeanNode)

    # String
    registry.register_node("StringFormat", string_nodes.StringFormatNode)

    # FFT
    registry.register_node("Stft", fft_nodes.StftNode)
    registry.register_node("Istft", fft_nodes.IstftNode)
    registry.register_node("Fft", fft_nodes.FftNode)
    registry.register_node("Mfcc", fft_nodes.MfccNode)

    # Adapter
    registry.register_node("Compose", adapter_nodes.ComposeNode)
    registry.register_node("Decompose", adapter_nodes.DecomposeNode)

    # Array Manipulation
    registry.register_node("ColumnStack", array_manipulation_nodes.ColumnStackNode)
    registry.register_node("ColumnUnstack", array_manipulation_nodes.ColumnUnstackNode)
    registry.register_node("Stack", array_manipulation_nodes.StackNode)
    registry.register_node("Unstack", array_manipulation_nodes.UnstackNode)
    registry.register_node("Roll", array_manipulation_nodes.RollNode)
    registry.register_node("Reshape", array_manipulation_nodes.ReshapeNode)

    # Bit-wise Operations
    registry.register_node("Packbits", bit_wise_operation_nodes.PackbitsNode)

    # Arithmetic Operators
    registry.register_node("Add", arithmetic_operation_nodes.AddNode)
    registry.register_node("Subtract", arithmetic_operation_nodes.SubtractNode)
    registry.register_node("Multiply", arithmetic_operation_nodes.MultiplyNode)
    registry.register_node("Divide", arithmetic_operation_nodes.DivideNode)
    registry.register_node("Reciprocal", arithmetic_operation_nodes.ReciprocalNode)
    registry.register_node("Negative", arithmetic_operation_nodes.NegativeNode)

    # Indexing
    registry.register_node("MaskAssign", indexing_nodes.MaskAssignNode)
    registry.register_node("Extract", indexing_nodes.ExtractNode)

    # Clock (logical clocks, defined in time_nodes.py)
    registry.register_node("Clock", time_nodes.ClockNode)
    registry.register_node("TickClock", time_nodes.TickClockNode)

    # Wave Generator
    registry.register_node("WaveGenerator", wave_generator.WaveGeneratorNode)

    # Window
    registry.register_node("Window", window_nodes.WindowNode)

    # Time
    registry.register_node("SystemTime", time_nodes.SystemTimeNode)
    registry.register_node("TimeStringify", time_nodes.TimeStringifyNode)
    registry.register_node("TimeDecompose", time_nodes.TimeDecomposeNode)
    registry.register_node("TimeDailyRangeWithin", time_nodes.TimeDailyRangeWithinNode)

    # Random
    registry.register_node("RandomUniform", random_nodes.RandomUniformNode)

    # Mathematical Functions
    registry.register_node("Abs", mathematical_function_nodes.AbsNode)
    registry.register_node("Sum", mathematical_function_nodes.SumNode)
    registry.register_node("Min", mathematical_function_nodes.MinNode)
    registry.register_node("Max", mathematical_function_nodes.MaxNode)
    registry.register_node("Interpolate", mathematical_function_nodes.InterpolateNode)
    registry.register_node("Sqrt", mathematical_function_nodes.SqrtNode)

    # Trigonometric Functions
    registry.register_node("Sin", trigonometric_nodes.SinNode)
    registry.register_node("Cos", trigonometric_nodes.CosNode)
    registry.register_node("Tan", trigonometric_nodes.TanNode)
    registry.register_node("Asin", trigonometric_nodes.AsinNode)
    registry.register_node("Acos", trigonometric_nodes.AcosNode)
    registry.register_node("Atan", trigonometric_nodes.AtanNode)
    registry.register_node("Atan2", trigonometric_nodes.Atan2Node)
    registry.register_node("Deg2Rad", trigonometric_nodes.Deg2RadNode)
    registry.register_node("Rad2Deg", trigonometric_nodes.Rad2DegNode)

    # Buffer
    registry.register_node("ValuesBuffer", buffer_nodes.ValuesBufferNode)
    registry.register_node("SlidingWindow", buffer_nodes.SlidingWindowNode)
    registry.register_node("SeriesShift", buffer_nodes.SeriesShiftNode)
    registry.register_node("ValuesRingBuffer", buffer_nodes.ValuesRingBufferNode)

    # Value
    registry.register_node("RealNumberValue", value_nodes.RealNumberValueNode)
    registry.register_node("ComplexNumberValue", value_nodes.ComplexNumberValueNode)
    registry.register_node("StringValue", value_nodes.StringValueNode)
    registry.register_node("EmptyValue", value_nodes.EmptyValueNode)
    registry.register_node("ArrayValue", value_nodes.ArrayValueNode)
    registry.register_node("ValueCounter", value_nodes.ValueCounterNode)
    registry.register_node("ValueAccumulator", value_nodes.ValueAccumulatorNode)
    registry.register_node("Enumerate", value_nodes.EnumerateNode)
    registry.register_node("ValuesGetLast", value_nodes.ValuesGetLastNode)
    registry.register_node("AsType", value_nodes.AsTypeNode)
    registry.register_node("FullLike", value_nodes.FullLikeNode)

    # Logic Functions
    registry.register_node("Equal", logic_function_nodes.EqualNode)
    registry.register_node("NotEqual", logic_function_nodes.NotEqualNode)
    registry.register_node("Less", logic_function_nodes.LessNode)
    registry.register_node("Greater", logic_function_nodes.GreaterNode)
    registry.register_node("WithinRange", logic_function_nodes.WithinRangeNode)
    registry.register_node("LogicalAnd", logic_function_nodes.LogicalAndNode)
    registry.register_node("LogicalOr", logic_function_nodes.LogicalOrNode)
    registry.register_node("LogicalNot", logic_function_nodes.LogicalNotNode)
    registry.register_node("All", logic_function_nodes.AllNode)
    registry.register_node("Any", logic_function_nodes.AnyNode)

    # Flow Control
    registry.register_node("OneShotGate", flow_control_nodes.OneShotGateNode)
    registry.register_node("Sequence", flow_control_nodes.SequenceNode)
    registry.register_node("Yield", flow_control_nodes.YieldNode)
    registry.register_node("ValuesLatch", flow_control_nodes.ValuesLatchNode)
    registry.register_node("ValuesDelay", flow_control_nodes.ValuesDelayNode)
    registry.register_node("ValueChanged", flow_control_nodes.ValueChangedNode)
    registry.register_node("BoolBranch", flow_control_nodes.BoolBranchNode)
    registry.register_node("SwitchBranch", flow_control_nodes.SwitchBranchNode)
    registry.register_node("ValuesBranch", flow_control_nodes.ValuesBranchNode)
    registry.register_node("ValuesGate", flow_control_nodes.ValuesGateNode)
    registry.register_node("Transition", flow_control_nodes.TransitionNode)
    registry.register_node("BoolEdge", flow_control_nodes.BoolEdgeNode)

    # Graph
    registry.register_node("GraphProxy", graph_nodes.GraphProxyNode)
    registry.register_node(
        "GraphPropertiesChanged", graph_nodes.GraphPropertiesChangedNode
    )
    registry.register_node("GraphLoaded", graph_nodes.GraphLoadedNode)

    # Script
    registry.register_node("PureScript", script_nodes.PureScriptNode)
