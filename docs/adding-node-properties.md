# Adding New Properties to Nodes

This guide explains how to add new configurable properties to existing nodes in the nonoha-core system.

## Overview

Node properties are configurable parameters that can be modified through the editor's Properties panel. When you add a property to a node, it becomes:

1. **Visible** in the editor's Properties panel
2. **Editable** by users through the UI
3. **Persistent** when the graph is saved
4. **Reactive** - changes trigger node updates
5. **Connectable** - it gets an input port (`@name`), so another node's output can set it

## Implementation Steps

Follow these steps to add a new property to an existing node. We'll use the `MeanNode` from `statistics_nodes.py` as a reference for the typical pattern.

### Step 1: Declare the Property in PROPERTIES

Declare every property in the class's `PROPERTIES`, with these three fields:

```python
class MeanNode(BaseNode):
    PROPERTIES = {
        "in_type": {
            "description": "Input type (e.g. 'f32', 'f32[3]')",
            "data_type": "str",
            "default_value": "f32",
        },
        "axis": {
            "description": "Axis to reduce (0 = batch dimension)",
            "data_type": "i32",
            "default_value": 0,
        },
    }
```

- `description`: one short phrase: what it is, with its unit, format or allowed values. It is shown in the node catalog.
- `data_type`: the type of the property's input port (see "Property Data Types"). The node gets an input port `@axis` of this type.
- `default_value`: the initial value. `BaseNode.__init__` puts it in `self.properties`; it is the only place that states it.

The order of `PROPERTIES` is the order the editor shows.

### Step 2: Read the Default in the Constructor

Take the initial value from `self.properties`, not from a second literal:

```python
    def __init__(self, name: str):
        super().__init__(name, "Mean")

        in_type = name_to_port_value_type(str(self.properties["in_type"]))
        axis: int | None = int(self.properties["axis"])
```

### Step 3: Store Property in Instance Variables

Store the value in an instance variable for internal use (the processing path reads these, never the dictionary):

```python
        self._in_type = in_type
        self._axis = axis
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

Choose the `data_type` of the property's port to match:

| Property value | `data_type` |
| --- | --- |
| real number | `f64` (its port accepts every numeric sender) |
| integer | `i32` (the nodes that emit integers emit `i32`) |
| true or false | `bool` |
| text: a type name such as `f32[3]`, a comma-separated list, a choice, a path, a format | `str` |

A value that arrives through the port is a numpy scalar, so convert in `set_properties` (`int()`, `float()`, `bool()`, `str()`) before storing it: properties are saved as JSON. The type does not check values set from the editor or the API, so `set_properties` validates the range in every case.

`nonoha_core._testing` has two checks for a plugin's tests: `assert_all_properties_declared(registry)` and `assert_property_ports_apply(registry)`.

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
2. **Set Reasonable Defaults**: Provide sensible default values, in `default_value` only
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
