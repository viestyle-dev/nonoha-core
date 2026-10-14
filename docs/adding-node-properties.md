# Adding New Properties to Nodes

This guide explains how to add new configurable properties to existing nodes in the nonoha-core system.

## Overview

Node properties are configurable parameters that can be modified through the editor's Properties panel. When you add a property to a node, it becomes:

1. **Visible** in the editor's Properties panel
2. **Editable** by users through the UI
3. **Persistent** when the graph is saved
4. **Reactive** - changes trigger node updates

## Implementation Steps

Follow these steps to add a new property to an existing node. We'll use the `MeanNode` from `statistics_nodes.py` as a reference for the typical pattern.

### Step 1: Add Property Variable to Constructor

Add your new property as a local variable in the node's `__init__` method:

```python
class MeanNode(BaseNode):
    def __init__(self, name: str):
        super().__init__(name, "Mean")

        # Property variables
        in_type = PortValueType(DataType.Float32)
        axis: int | None = 0  # Property variable
```

### Step 2: Store Property in Instance Variables

Store the property value in an instance variable for internal use:

```python
        self._in_type = in_type
        self._axis = axis
```

### Step 3: Export Property to Properties Dictionary

Add the property to the `self.properties` dictionary to make it visible in the editor:

```python
        self.properties["in_type"] = in_type.name
        self.properties["axis"] = axis
```

### Step 4: Handle Property Updates in set_properties

The `set_properties` method follows a specific pattern. Here's the typical implementation from `statistics_nodes.py`:

```python
def set_properties(self, properties: dict[str, PropertyDataType]):
    # 1. Extract properties
    in_type = self._in_type
    if "in_type" in properties:
        in_type_str = properties["in_type"]
        if not isinstance(in_type_str, str):
            raise ValueError("In type must be a string")

        in_type = name_to_port_value_type(in_type_str)

        if in_type.data_type not in [DataType.Float32, DataType.Float64]:
            raise ValueError("In type must be Float32 or Float64")

    axis = self._axis
    if "axis" in properties:
        axis = None if (val := properties.get("axis", "")) == "" else int(val)

    # 2. Validate and prepare new ports (pure operations only)
    new_input_in = self._input_in
    if in_type != self._in_type:
        new_input_in = StaticTypeInputPort("in", [in_type])

    new_output_out = self._output_out
    if in_type != self._in_type or axis != self._axis:
        out_type = self._get_out_type(in_type, axis)
        new_output_out = StaticTypeOutputPort("out", [out_type])

    # 3. Update internal state
    #   3a. Replace ports
    if new_input_in != self._input_in:
        replace_node_input_port(
            self, self._input_in, new_input_in, self._on_input_in
        )
        self._input_in = new_input_in

    if new_output_out != self._output_out:
        replace_node_output_port(self, self._output_out, new_output_out)
        self._output_out = new_output_out

    #   3b. Update state variables and properties dictionary
    self._in_type = in_type
    self._axis = axis
    self.properties["in_type"] = in_type.name
    self.properties["axis"] = axis if axis is not None else ""

    # 4. Notify graph
    if self.parent_graph is not None:
        self.parent_graph.notify_node_updated(self)
```

### Key Points of the set_properties Pattern

1. **Extract properties with defaults**: Always start with the current value as default
2. **Validate and prepare**: Check types/ranges, create new port instances (pure, no side effects)
3. **Update internal state**: Replace ports, then update state variables and properties dictionary
4. **Notify graph**: Always call `notify_node_updated` at the end

## Property Data Types

Properties support the following data types as defined in `PropertyDataType`:

- `int` - Integer values
- `float` - Floating-point values
- `str` - String values
- `bool` - Boolean values

Choose the appropriate type for your property and ensure consistent type conversion in `set_properties`.

## Deployment Process

After implementing the property changes:

### Reinstall the Package

The node code is installed as a Python package. After making changes, reinstall it:

```bash
uv sync --reinstall
```

This rebuilds and reinstalls the `nonoha-core` package with your changes.

## Best Practices

1. **Use Descriptive Names**: Choose clear, descriptive property names
2. **Set Reasonable Defaults**: Provide sensible default values
3. **Add Validation**: Always validate property values in `set_properties`
4. **Handle Port Updates**: When properties affect port types, recreate and replace them properly
5. **Notify Graph**: Always call `notify_node_updated` to inform the graph of changes

## Example: IncrementalMeanNode

Here's another example from `statistics_nodes.py` showing how to handle internal state reset when properties change:

```python
def set_properties(self, properties: dict[str, PropertyDataType]):
    # 1. Extract properties
    in_type = self._in_type

    if "in_type" in properties:
        in_type_str = properties["in_type"]
        if not isinstance(in_type_str, str):
            raise ValueError("In type must be a string")

        in_type = name_to_port_value_type(in_type_str)

        if in_type.data_type not in [DataType.Float32, DataType.Float64]:
            raise ValueError("In type must be Float32 or Float64")

    # 2. Prepare new ports
    new_input_in = self._input_in
    new_output_out = self._output_out
    if in_type != self._in_type:
        new_input_in = StaticTypeInputPort("in", [in_type])
        new_output_out = StaticTypeOutputPort("out", [in_type])

    # 3. Update internal state
    if new_input_in != self._input_in:
        replace_node_input_port(
            self, self._input_in, new_input_in, self._on_input_in
        )
        self._input_in = new_input_in

    if new_output_out != self._output_out:
        replace_node_output_port(self, self._output_out, new_output_out)
        self._output_out = new_output_out

    if in_type != self._in_type:
        self._mean = np.zeros(in_type.shape)
        self._c_mean = np.zeros(in_type.shape)
        self._n = 0

    self._in_type = in_type
    self.properties["in_type"] = in_type.name

    # 4. Notify graph
    if self.parent_graph is not None:
        self.parent_graph.notify_node_updated(self)
```

This pattern shows how stateful nodes reset internal buffers/accumulators when the port type changes.
