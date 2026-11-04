window.BENCHMARK_DATA = {
  "lastUpdate": 1793751103266,
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
      },
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
          "id": "592bfd54de8fcfb64cbb0f7bcac705dc0304dbcf",
          "message": "Release v1.0.0",
          "timestamp": "2026-11-04T09:07:51+09:00",
          "tree_id": "49687d99694fd826331f9758ce0d1e8a9e5c9890",
          "url": "https://github.com/viestyle-dev/nonoha-core/commit/592bfd54de8fcfb64cbb0f7bcac705dc0304dbcf"
        },
        "date": 1793751100573,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_endian_conversion.py::test_frombuffer_big_to_native",
            "value": 24622.311297742104,
            "unit": "iter/sec",
            "range": "stddev: 0.000005621145307327743",
            "extra": "mean: 40.613571484318825 usec\nrounds: 25642"
          },
          {
            "name": "benchmarks/test_endian_conversion.py::test_astype_native_to_big",
            "value": 24819.027126811303,
            "unit": "iter/sec",
            "range": "stddev: 0.000006202971589464962",
            "extra": "mean: 40.29166795662702 usec\nrounds: 25840"
          },
          {
            "name": "benchmarks/test_endian_conversion.py::test_total_cost_convert_once",
            "value": 1210.9903959907476,
            "unit": "iter/sec",
            "range": "stddev: 0.00004706538539194698",
            "extra": "mean: 825.7703804346606 usec\nrounds: 1472"
          },
          {
            "name": "benchmarks/test_node_compute.py::test_add_node",
            "value": 534147.8500366465,
            "unit": "iter/sec",
            "range": "stddev: 4.2410832855277844e-7",
            "extra": "mean: 1.8721408312911394 usec\nrounds: 61350"
          },
          {
            "name": "benchmarks/test_node_compute.py::test_fft_node",
            "value": 68342.8415480036,
            "unit": "iter/sec",
            "range": "stddev: 0.0000033578267058228837",
            "extra": "mean: 14.632110362247756 usec\nrounds: 74627"
          },
          {
            "name": "benchmarks/test_node_compute.py::test_values_buffer_node",
            "value": 109.08277746566604,
            "unit": "iter/sec",
            "range": "stddev: 0.0017322509437909831",
            "extra": "mean: 9.16735000000116 msec\nrounds: 116"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_10_callbacks",
            "value": 931752.0119117041,
            "unit": "iter/sec",
            "range": "stddev: 2.5231624350705357e-7",
            "extra": "mean: 1.0732469446974144 usec\nrounds: 109891"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_100_callbacks",
            "value": 223347.4573794552,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010172648968979624",
            "extra": "mean: 4.477328785082403 usec\nrounds: 121952"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_large_payload",
            "value": 927517.5977985526,
            "unit": "iter/sec",
            "range": "stddev: 2.3349392419100606e-7",
            "extra": "mean: 1.0781466598298517 usec\nrounds: 105264"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_receive_value_with_index",
            "value": 5794520.698131082,
            "unit": "iter/sec",
            "range": "stddev: 3.418188585737189e-8",
            "extra": "mean: 172.57682767828845 nsec\nrounds: 62894"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_chain_10",
            "value": 125385.44899701679,
            "unit": "iter/sec",
            "range": "stddev: 0.000001955952445872193",
            "extra": "mean: 7.975407098664154 usec\nrounds: 144928"
          },
          {
            "name": "benchmarks/test_port_subscribe.py::test_subscribe_1000",
            "value": 260.09110124301867,
            "unit": "iter/sec",
            "range": "stddev: 0.000420626107705357",
            "extra": "mean: 3.844806666667308 msec\nrounds: 270"
          },
          {
            "name": "benchmarks/test_port_subscribe.py::test_unsubscribe_middle",
            "value": 859.4254912482002,
            "unit": "iter/sec",
            "range": "stddev: 0.00005869549030136851",
            "extra": "mean: 1.1635679999992021 msec\nrounds: 100"
          },
          {
            "name": "benchmarks/test_port_subscribe.py::test_subscribe_unsubscribe_cycle",
            "value": 8355.24495372057,
            "unit": "iter/sec",
            "range": "stddev: 0.00001270405399802332",
            "extra": "mean: 119.6853001364972 usec\nrounds: 8796"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_f32_small",
            "value": 426284.8380649744,
            "unit": "iter/sec",
            "range": "stddev: 5.548092666435103e-7",
            "extra": "mean: 2.345849325862179 usec\nrounds: 46949"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_f32_large",
            "value": 108140.6833278901,
            "unit": "iter/sec",
            "range": "stddev: 0.0000036930334191307034",
            "extra": "mean: 9.2472136223509 usec\nrounds: 116280"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_multi_value",
            "value": 107393.10356514639,
            "unit": "iter/sec",
            "range": "stddev: 0.000002835839584610854",
            "extra": "mean: 9.31158488583379 usec\nrounds: 121952"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_string",
            "value": 135906.9142230749,
            "unit": "iter/sec",
            "range": "stddev: 0.000002116182524525204",
            "extra": "mean: 7.35797737529836 usec\nrounds: 151516"
          }
        ]
      }
    ]
  }
}