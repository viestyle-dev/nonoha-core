import numpy as np
import logging

from nonoha_core.node import (
    BaseNode,
    NodeDoc,
    PropertyDataType,
    replace_node_output_port,
)
from nonoha_core.port import (
    PortValue,
    StaticTypeInputPort,
    StaticTypeOutputPort,
)
from nonoha_core.data_type import DataType, PortValueType, name_to_port_value_type

logger = logging.getLogger(__name__)


class RandomUniformNode(BaseNode):
    @classmethod
    def describe(cls, properties=None):
        return NodeDoc(
            description="Generate random values from a uniform distribution",
            category="Random",
            inputs={"dispatch": ""},
            outputs={"random": ""},
        )

    def __init__(self, name: str):
        super().__init__(name, "RandomUniform")

        input_dispatch = StaticTypeInputPort("dispatch", [PortValueType(DataType.Any)])
        input_dispatch.subscribe(id(self), self._on_input_dispatch)

        out_type = PortValueType(DataType.Float32)

        output_random = StaticTypeOutputPort("random", [out_type])

        self._low = 0.0
        self._high = 1.0
        self._input_dispatch = input_dispatch
        self._output_random = output_random
        self._rng = np.random.default_rng()
        self._out_type = out_type

        self.inputs[input_dispatch.name] = input_dispatch
        self.outputs[output_random.name] = output_random

        self.properties["low"] = self._low
        self.properties["high"] = self._high
        self.properties["shape"] = out_type.shape_str

    def set_properties(self, properties: dict[str, PropertyDataType]):
        low = self._low
        if "low" in properties:
            low = float(properties["low"])

        high = self._high
        if "high" in properties:
            high = float(properties["high"])

        out_type = self._out_type
        if "shape" in properties:
            shape_str = properties["shape"]
            out_type = name_to_port_value_type(f"f32{shape_str}")

        new_out_random = self._output_random
        if out_type != self._out_type:
            new_out_random = StaticTypeOutputPort("random", [out_type])

        if new_out_random != self._output_random:
            replace_node_output_port(self, self._output_random, new_out_random)
            self._output_random = new_out_random

        self._low = low
        self._high = high
        self._out_type = out_type

        self.properties["low"] = low
        self.properties["high"] = high
        self.properties["shape"] = out_type.shape_str

        if self.parent_graph is not None:
            self.parent_graph.notify_node_updated(self)

    def _on_input_dispatch(self, values: list[PortValue]):
        length = len(values[0])
        shape = (length, *self._out_type.shape)

        out = self._rng.uniform(self._low, self._high, shape)

        self._output_random.dispatch([out])


# class RandomNormalNode(BaseNode):
#     def __init__(self, name: str):
#         super().__init__(name, "RandomNormal")

#         input_dispatch = StaticTypeInputPort("dispatch", [PortValueType(DataType.Any)])
#         input_dispatch.subscribe(id(self), self._on_input_dispatch)

#         output_random = StaticTypeOutputPort(
#             "random", [PortValueType(DataType.Float32)]
#         )

#         self._input_dispatch = input_dispatch
#         self._output_random = output_random
#         self._rng = np.random.default_rng()

#         self._mean = 0.0
#         self._std = 1.0

#         self.inputs[input_dispatch.name] = input_dispatch
#         self.outputs[output_random.name] = output_random

#         self.properties["mean"] = self._mean
#         self.properties["std"] = self._std

#     def set_properties(self, properties: dict[str, PropertyDataType]):
#         mean = self._mean
#         if "mean" in properties:
#             mean = float(properties["mean"])

#         std = self._std
#         if "std" in properties:
#             std = float(properties["std"])

#         self._mean = mean
#         self._std = std
#         self.properties["mean"] = mean
#         self.properties["std"] = std

#         if self.parent_graph is not None:
#             self.parent_graph.notify_properties_changed(self)

#     def _on_input_dispatch(self, values: list[Any]):
#         dispatch_length = len(values[0])

#         random_values = self._rng.normal(self._mean, self._std, dispatch_length)

#         self._output_random.dispatch([random_values])


# class PerlinNoiseNode(BaseNode):
#     def __init__(self, name: str):
#         super().__init__(name, "PerlinNoise")

#         input_dispatch = StaticTypeInputPort("dispatch", [PortValueType(DataType.Any)])
#         input_dispatch.subscribe(id(self), self._on_input_dispatch)

#         output_noise = StaticTypeOutputPort("noise", [PortValueType(DataType.Float32)])

#         self._input_dispatch = input_dispatch
#         self._output_noise = output_noise
#         self._rng = np.random.default_rng()

#         # Perlin noise parameters
#         self._scale = 0.1  # スケール（高いほど細かい）
#         self._octaves = 1  # オクターブ数（高いほど詳細が増す）
#         self._persistence = 0.5  # 各オクターブの振幅の減衰率
#         self._lacunarity = 2.0  # 各オクターブの周波数の増加率
#         self._seed = 0  # シード値

#         self.inputs[input_dispatch.name] = input_dispatch
#         self.outputs[output_noise.name] = output_noise

#         self.properties["scale"] = self._scale
#         self.properties["octaves"] = self._octaves
#         self.properties["persistence"] = self._persistence
#         self.properties["lacunarity"] = self._lacunarity
#         self.properties["seed"] = self._seed

#     def set_properties(self, properties: dict[str, PropertyDataType]):
#         if "scale" in properties:
#             self._scale = float(properties["scale"])

#         if "octaves" in properties:
#             self._octaves = int(properties["octaves"])

#         if "persistence" in properties:
#             self._persistence = float(properties["persistence"])

#         if "lacunarity" in properties:
#             self._lacunarity = float(properties["lacunarity"])

#         if "seed" in properties:
#             self._seed = int(properties["seed"])
#             # シード値が変更されたら乱数生成器を再初期化
#             self._rng = np.random.default_rng(self._seed)

#         # プロパティを更新
#         self.properties["scale"] = self._scale
#         self.properties["octaves"] = self._octaves
#         self.properties["persistence"] = self._persistence
#         self.properties["lacunarity"] = self._lacunarity
#         self.properties["seed"] = self._seed

#         if self.parent_graph is not None:
#             self.parent_graph.notify_properties_changed(self)

#     def _generate_perlin_noise(self, x):
#         """
#         1次元Perlinノイズを生成する簡易実装
#         """
#         # 格子点の値を生成（シード値に基づく）
#         grid_size = int(np.ceil(x.max() / self._scale) + 1)
#         grid = self._rng.uniform(-1, 1, grid_size)

#         # 各点のノイズ値を計算
#         x_scaled = x * self._scale
#         x0 = np.floor(x_scaled).astype(int)
#         x1 = x0 + 1
#         t = x_scaled - x0

#         # 補間のための関数（スムーズステップ）
#         t = t * t * (3 - 2 * t)  # スムーズステップ補間

#         # 格子点の値を取得して補間
#         # np.takeを修正
#         y0 = grid[x0 % grid_size]
#         y1 = grid[x1 % grid_size]

#         return y0 + t * (y1 - y0)  # 線形補間

#     def _generate_fractal_noise(self, x):
#         """
#         フラクタルノイズ（複数のオクターブを組み合わせたPerlinノイズ）を生成
#         """
#         noise = np.zeros_like(x, dtype=float)
#         amplitude = 1.0
#         frequency = 1.0
#         max_value = 0.0  # 正規化のため

#         # 複数のオクターブを合成
#         for i in range(self._octaves):
#             noise += amplitude * self._generate_perlin_noise(x * frequency)
#             max_value += amplitude
#             amplitude *= self._persistence
#             frequency *= self._lacunarity

#         # -1から1の範囲に正規化
#         return noise / max_value if max_value > 0 else noise

#     def _on_input_dispatch(self, values: list[Any]):
#         dispatch_length = len(values[0])

#         # 入力サイズに基づいて線形にスケールされた値を生成
#         x = np.linspace(0, dispatch_length, dispatch_length)

#         # Perlinノイズを生成
#         noise_values = self._generate_fractal_noise(x)

#         # 結果をディスパッチ
#         self._output_noise.dispatch([noise_values])
