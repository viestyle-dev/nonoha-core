window.BENCHMARK_DATA = {
  "lastUpdate": 1793155199582,
  "repoUrl": "https://github.com/viestyle-dev/nonoha-core",
  "entries": {
    "nonoha-core Benchmark (windows-latest)": [
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
        "date": 1793155186690,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_endian_conversion.py::test_frombuffer_big_to_native",
            "value": 14285.11710191843,
            "unit": "iter/sec",
            "range": "stddev: 0.00014566297259114796",
            "extra": "mean: 70.00292632292839 usec\nrounds: 21187"
          },
          {
            "name": "benchmarks/test_endian_conversion.py::test_astype_native_to_big",
            "value": 14058.033019359738,
            "unit": "iter/sec",
            "range": "stddev: 0.0003969023778089276",
            "extra": "mean: 71.1337068722822 usec\nrounds: 21506"
          },
          {
            "name": "benchmarks/test_endian_conversion.py::test_total_cost_convert_once",
            "value": 1049.661148129573,
            "unit": "iter/sec",
            "range": "stddev: 0.0026878274322546716",
            "extra": "mean: 952.6884002346227 usec\nrounds: 3388"
          },
          {
            "name": "benchmarks/test_node_compute.py::test_add_node",
            "value": 248099.90861540477,
            "unit": "iter/sec",
            "range": "stddev: 0.00003877234537979626",
            "extra": "mean: 4.030634293985689 usec\nrounds: 30396"
          },
          {
            "name": "benchmarks/test_node_compute.py::test_fft_node",
            "value": 29243.06146325867,
            "unit": "iter/sec",
            "range": "stddev: 0.0003598260986836585",
            "extra": "mean: 34.196146024465044 usec\nrounds: 60976"
          },
          {
            "name": "benchmarks/test_node_compute.py::test_values_buffer_node",
            "value": 37.45685282693428,
            "unit": "iter/sec",
            "range": "stddev: 0.010639653475536498",
            "extra": "mean: 26.697384444454052 msec\nrounds: 45"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_10_callbacks",
            "value": 471419.5248360489,
            "unit": "iter/sec",
            "range": "stddev: 0.00003110789075522578",
            "extra": "mean: 2.121252827505736 usec\nrounds: 64103"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_100_callbacks",
            "value": 98988.80940263657,
            "unit": "iter/sec",
            "range": "stddev: 0.0001680358414352991",
            "extra": "mean: 10.102152011269316 usec\nrounds: 112360"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_large_payload",
            "value": 493979.96640390804,
            "unit": "iter/sec",
            "range": "stddev: 0.000027548420420632293",
            "extra": "mean: 2.024373594095172 usec\nrounds: 61350"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_receive_value_with_index",
            "value": 4642848.3367303535,
            "unit": "iter/sec",
            "range": "stddev: 6.05700705585005e-7",
            "extra": "mean: 215.3850239063131 nsec\nrounds: 52911"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_chain_10",
            "value": 52194.17199621191,
            "unit": "iter/sec",
            "range": "stddev: 0.00025760618614368815",
            "extra": "mean: 19.1592272039985 usec\nrounds: 133334"
          },
          {
            "name": "benchmarks/test_port_subscribe.py::test_subscribe_1000",
            "value": 190.76134841244928,
            "unit": "iter/sec",
            "range": "stddev: 0.002938338261768272",
            "extra": "mean: 5.242152083334398 msec\nrounds: 240"
          },
          {
            "name": "benchmarks/test_port_subscribe.py::test_unsubscribe_middle",
            "value": 480.8732658484886,
            "unit": "iter/sec",
            "range": "stddev: 0.0007204197413636094",
            "extra": "mean: 2.079550000009931 msec\nrounds: 100"
          },
          {
            "name": "benchmarks/test_port_subscribe.py::test_subscribe_unsubscribe_cycle",
            "value": 2718.616362198074,
            "unit": "iter/sec",
            "range": "stddev: 0.0014918327841128203",
            "extra": "mean: 367.83417252424437 usec\nrounds: 7825"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_f32_small",
            "value": 114552.58952131408,
            "unit": "iter/sec",
            "range": "stddev: 0.000159855320271475",
            "extra": "mean: 8.729614967053505 usec\nrounds: 169492"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_f32_large",
            "value": 38706.46838093316,
            "unit": "iter/sec",
            "range": "stddev: 0.0003141829623216135",
            "extra": "mean: 25.83547509833268 usec\nrounds: 68028"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_multi_value",
            "value": 35844.37766626962,
            "unit": "iter/sec",
            "range": "stddev: 0.0003887573900064096",
            "extra": "mean: 27.898378075092737 usec\nrounds: 60607"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_string",
            "value": 51206.5502242253,
            "unit": "iter/sec",
            "range": "stddev: 0.0003071964571763707",
            "extra": "mean: 19.52875160738538 usec\nrounds: 129871"
          }
        ]
      }
    ]
  }
}