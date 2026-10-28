window.BENCHMARK_DATA = {
  "lastUpdate": 1793155061731,
  "repoUrl": "https://github.com/viestyle-dev/nonoha-core",
  "entries": {
    "nonoha-core Benchmark (macos-latest)": [
      {
        "commit": {
          "author": {
            "email": "fivetwothreesix@gmail.com",
            "name": "IOE",
            "username": "ContentsViewer"
          },
          "committer": {
            "email": "fivetwothreesix@gmail.com",
            "name": "IOE",
            "username": "ContentsViewer"
          },
          "distinct": true,
          "id": "8398b8c4f777e11808753c21601d2af0f24b4777",
          "message": "publish",
          "timestamp": "2026-10-14T12:42:58+09:00",
          "tree_id": "f4924a3b92d58a5b7694df5292eb455c88572644",
          "url": "https://github.com/viestyle-dev/nonoha-core-pub/commit/8398b8c4f777e11808753c21601d2af0f24b4777"
        },
        "date": 1793155060142,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_endian_conversion.py::test_frombuffer_big_to_native",
            "value": 103072.0034700843,
            "unit": "iter/sec",
            "range": "stddev: 0.00005386163566909367",
            "extra": "mean: 9.70195558768042 usec\nrounds: 145455"
          },
          {
            "name": "benchmarks/test_endian_conversion.py::test_astype_native_to_big",
            "value": 100903.53424831721,
            "unit": "iter/sec",
            "range": "stddev: 0.00002034450505847351",
            "extra": "mean: 9.91045563913612 usec\nrounds: 150944"
          },
          {
            "name": "benchmarks/test_endian_conversion.py::test_total_cost_convert_once",
            "value": 5201.25071679328,
            "unit": "iter/sec",
            "range": "stddev: 0.000019118998582641305",
            "extra": "mean: 192.26144911094164 usec\nrounds: 5905"
          },
          {
            "name": "benchmarks/test_node_compute.py::test_add_node",
            "value": 1057855.3279560148,
            "unit": "iter/sec",
            "range": "stddev: 1.2602079629929535e-7",
            "extra": "mean: 945.3088466568078 nsec\nrounds: 116496"
          },
          {
            "name": "benchmarks/test_node_compute.py::test_fft_node",
            "value": 127130.81021848632,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012716064528690903",
            "extra": "mean: 7.865913843240717 usec\nrounds: 139548"
          },
          {
            "name": "benchmarks/test_node_compute.py::test_values_buffer_node",
            "value": 248.84604408150884,
            "unit": "iter/sec",
            "range": "stddev: 0.00010644864607886766",
            "extra": "mean: 4.018548913208574 msec\nrounds: 265"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_10_callbacks",
            "value": 1745032.7237174336,
            "unit": "iter/sec",
            "range": "stddev: 6.49091164001113e-8",
            "extra": "mean: 573.0551561631501 nsec\nrounds: 192013"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_100_callbacks",
            "value": 415526.6508706746,
            "unit": "iter/sec",
            "range": "stddev: 1.1559948715392617e-7",
            "extra": "mean: 2.4065845064443443 usec\nrounds: 42934"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_large_payload",
            "value": 1933367.0217491216,
            "unit": "iter/sec",
            "range": "stddev: 4.3552290794936555e-8",
            "extra": "mean: 517.2323665148122 nsec\nrounds: 186047"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_receive_value_with_index",
            "value": 10748573.410429033,
            "unit": "iter/sec",
            "range": "stddev: 5.586015897052336e-9",
            "extra": "mean: 93.03560219717242 nsec\nrounds: 111633"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_chain_10",
            "value": 245499.8889361858,
            "unit": "iter/sec",
            "range": "stddev: 5.065125138692267e-7",
            "extra": "mean: 4.073321598365104 usec\nrounds: 133334"
          },
          {
            "name": "benchmarks/test_port_subscribe.py::test_subscribe_1000",
            "value": 375.15919025072213,
            "unit": "iter/sec",
            "range": "stddev: 0.00019735633966505117",
            "extra": "mean: 2.6655351274526726 msec\nrounds: 408"
          },
          {
            "name": "benchmarks/test_port_subscribe.py::test_unsubscribe_middle",
            "value": 1231.465838784951,
            "unit": "iter/sec",
            "range": "stddev: 0.00006482434755591013",
            "extra": "mean: 812.0403900011297 usec\nrounds: 100"
          },
          {
            "name": "benchmarks/test_port_subscribe.py::test_subscribe_unsubscribe_cycle",
            "value": 14437.669231828084,
            "unit": "iter/sec",
            "range": "stddev: 0.00000272793447898443",
            "extra": "mean: 69.26325738197986 usec\nrounds: 14935"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_f32_small",
            "value": 942327.34768693,
            "unit": "iter/sec",
            "range": "stddev: 7.542700983822108e-8",
            "extra": "mean: 1.061202354420442 usec\nrounds: 98368"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_f32_large",
            "value": 179346.40350550375,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010204061648828516",
            "extra": "mean: 5.575801802846368 usec\nrounds: 117648"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_multi_value",
            "value": 243684.4378366305,
            "unit": "iter/sec",
            "range": "stddev: 2.505368960858673e-7",
            "extra": "mean: 4.103667878333758 usec\nrounds: 128337"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_string",
            "value": 237191.16154420597,
            "unit": "iter/sec",
            "range": "stddev: 3.028390689244803e-7",
            "extra": "mean: 4.2160086973292525 usec\nrounds: 123717"
          }
        ]
      }
    ]
  }
}