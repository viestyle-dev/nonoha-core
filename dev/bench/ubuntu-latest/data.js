window.BENCHMARK_DATA = {
  "lastUpdate": 1793154993085,
  "repoUrl": "https://github.com/viestyle-dev/nonoha-core",
  "entries": {
    "nonoha-core Benchmark (ubuntu-latest)": [
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
        "date": 1793154991998,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_endian_conversion.py::test_frombuffer_big_to_native",
            "value": 39300.27286478183,
            "unit": "iter/sec",
            "range": "stddev: 0.00000549994438341736",
            "extra": "mean: 25.445115952264302 usec\nrounds: 40922"
          },
          {
            "name": "benchmarks/test_endian_conversion.py::test_astype_native_to_big",
            "value": 39591.589438799725,
            "unit": "iter/sec",
            "range": "stddev: 0.00000145293053960405",
            "extra": "mean: 25.257889722911724 usec\nrounds: 41432"
          },
          {
            "name": "benchmarks/test_endian_conversion.py::test_total_cost_convert_once",
            "value": 6606.80561867628,
            "unit": "iter/sec",
            "range": "stddev: 0.000004688517092432933",
            "extra": "mean: 151.35907694532068 usec\nrounds: 6849"
          },
          {
            "name": "benchmarks/test_node_compute.py::test_add_node",
            "value": 892437.4471915637,
            "unit": "iter/sec",
            "range": "stddev: 8.609049424750443e-8",
            "extra": "mean: 1.1205267138295398 usec\nrounds: 92877"
          },
          {
            "name": "benchmarks/test_node_compute.py::test_fft_node",
            "value": 129336.59670590803,
            "unit": "iter/sec",
            "range": "stddev: 6.776849882635375e-7",
            "extra": "mean: 7.731763672998522 usec\nrounds: 134572"
          },
          {
            "name": "benchmarks/test_node_compute.py::test_values_buffer_node",
            "value": 267.93521664203115,
            "unit": "iter/sec",
            "range": "stddev: 0.000060191544764280134",
            "extra": "mean: 3.732245475353199 msec\nrounds: 284"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_10_callbacks",
            "value": 1893510.1858690323,
            "unit": "iter/sec",
            "range": "stddev: 1.1006722239724409e-7",
            "extra": "mean: 528.1196834655375 nsec\nrounds: 195428"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_100_callbacks",
            "value": 494814.1676050232,
            "unit": "iter/sec",
            "range": "stddev: 1.3851376317922357e-7",
            "extra": "mean: 2.0209607272163774 usec\nrounds: 51099"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_large_payload",
            "value": 1856647.8833711653,
            "unit": "iter/sec",
            "range": "stddev: 6.2555161261566e-8",
            "extra": "mean: 538.6050898268129 nsec\nrounds: 196156"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_receive_value_with_index",
            "value": 11473967.030309191,
            "unit": "iter/sec",
            "range": "stddev: 7.410438095854673e-9",
            "extra": "mean: 87.15381501081468 nsec\nrounds: 119575"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_chain_10",
            "value": 243519.57722064113,
            "unit": "iter/sec",
            "range": "stddev: 4.652685618588443e-7",
            "extra": "mean: 4.106446025462459 usec\nrounds: 131562"
          },
          {
            "name": "benchmarks/test_port_subscribe.py::test_subscribe_1000",
            "value": 508.13736991466766,
            "unit": "iter/sec",
            "range": "stddev: 0.0000505378134775255",
            "extra": "mean: 1.9679717714285245 msec\nrounds: 525"
          },
          {
            "name": "benchmarks/test_port_subscribe.py::test_unsubscribe_middle",
            "value": 1174.845431464311,
            "unit": "iter/sec",
            "range": "stddev: 0.00004655304385845203",
            "extra": "mean: 851.1757999974634 usec\nrounds: 100"
          },
          {
            "name": "benchmarks/test_port_subscribe.py::test_subscribe_unsubscribe_cycle",
            "value": 14573.578903015825,
            "unit": "iter/sec",
            "range": "stddev: 0.00000317130394365741",
            "extra": "mean: 68.61732499990529 usec\nrounds: 15440"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_f32_small",
            "value": 648294.1039594203,
            "unit": "iter/sec",
            "range": "stddev: 3.4944112709551646e-7",
            "extra": "mean: 1.5425097866732749 usec\nrounds: 68297"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_f32_large",
            "value": 191823.93893870682,
            "unit": "iter/sec",
            "range": "stddev: 5.330190500492447e-7",
            "extra": "mean: 5.213113678786089 usec\nrounds: 103467"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_multi_value",
            "value": 172487.74513297834,
            "unit": "iter/sec",
            "range": "stddev: 0.000002815253968829949",
            "extra": "mean: 5.7975133203176625 usec\nrounds: 184230"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_string",
            "value": 237712.97872734122,
            "unit": "iter/sec",
            "range": "stddev: 9.965789458786242e-7",
            "extra": "mean: 4.206753898561881 usec\nrounds: 126072"
          }
        ]
      }
    ]
  }
}