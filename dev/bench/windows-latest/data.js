window.BENCHMARK_DATA = {
  "lastUpdate": 1795182379070,
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
      },
      {
        "commit": {
          "author": {
            "email": "fivetwothreesix@gmail.com",
            "name": "IOE",
            "username": "ContentsViewer"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "bd7854e1e3d2b31947542bc9e037b6445ec9fea7",
          "message": "Feature/inspector (#1)\n\n* feat: inspector\n\n* fix: update version to 1.1.0.dev0 in pyproject.toml\n\n* feat: add environment management and node documentation\n\n* improve performance\n\n* feat: enhance ClockNode and add WaveGeneratorNode with comprehensive tests\n\n* Enhance nonoha-core with various improvements and fixes\n\n- Refactor `reduce_values` in `reduce.py` to improve memory management and ensure proper handling of array ownership during reductions.\n- Introduce `ErrorLog` in `time_nodes.py` to capture and log errors without halting the clock node's operation.\n- Add checks for NaN and infinite values in `wave_generator.py` to prevent invalid states from persisting in the integral calculations.\n- Optimize byte serialization in `port.py` for numeric types, reducing unnecessary copies and improving performance.\n- Extend tests in `test_environment.py` to cover additional reserved environment variable names.\n- Implement new tests for `ErrorLog` functionality in `test_error_log.py`, ensuring proper logging behavior under error conditions.\n- Enhance `test_inspection.py` with scenarios to validate sample dispatching and buffer reuse in the inspector.\n- Add tests in `test_time_nodes.py` to verify that clock functionality remains intact despite downstream node failures.\n- Introduce tests in `test_wave_generator.py` to ensure that NaN values in frequency modulation do not affect subsequent calculations.\n- Update version in `uv.lock` to 1.1.0.dev0 to reflect the latest changes and improvements.\n\n* Refactor port encoding and add comprehensive tests for inspection\n\n- Renamed internal constants for clarity: _WIRE_DTYPES to WIRE_DTYPES and _SHAPE_STRUCTS to SHAPE_STRUCTS.\n- Updated the `port_values_to_bytes` function to use the new constant names.\n- Introduced a new reference test suite in `inspection_reference.py` to ensure the encoding consistency of reduced values.\n- Enhanced existing tests in `test_inspection.py` to validate the behavior of the reduction process and added checks for flags.\n- Created a new test file `test_inspection_encoding.py` to verify that the encoded frames match expected byte sequences for various input cases.\n- Added tests for handling large data, dimensionality issues, and ensuring that owned values are not unnecessarily copied during processing.\n\n* Refactor probe and reduce modules for improved sample handling and memory management\n\n- Introduced state management for probe entries with IDLE, ASKED, and HELD states.\n- Replaced 'armed' flag with state management in the Probe class.\n- Enhanced the Accumulator class to track item sizes and calculate held bytes.\n- Refactored reduce_values function to utilize a new _Slot class for better organization of sample data.\n- Implemented common stride calculation for efficient memory usage in reduce_values.\n- Improved error handling for oversized samples with detailed reporting on dimensions and sizes.",
          "timestamp": "2026-11-18T23:40:04+09:00",
          "tree_id": "b2aed50f6cf892c2d90689f333df81f72a892f6c",
          "url": "https://github.com/viestyle-dev/nonoha-core/commit/bd7854e1e3d2b31947542bc9e037b6445ec9fea7"
        },
        "date": 1795013016001,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_endian_conversion.py::test_frombuffer_big_to_native",
            "value": 19315.913530718437,
            "unit": "iter/sec",
            "range": "stddev: 0.000008357856266639876",
            "extra": "mean: 51.77078466465914 usec\nrounds: 21232"
          },
          {
            "name": "benchmarks/test_endian_conversion.py::test_astype_native_to_big",
            "value": 18247.308433135076,
            "unit": "iter/sec",
            "range": "stddev: 0.000021853415574165723",
            "extra": "mean: 54.80260300659529 usec\nrounds: 21552"
          },
          {
            "name": "benchmarks/test_endian_conversion.py::test_total_cost_convert_once",
            "value": 1488.5333945800594,
            "unit": "iter/sec",
            "range": "stddev: 0.00007362591128310316",
            "extra": "mean: 671.8021937842495 usec\nrounds: 1641"
          },
          {
            "name": "benchmarks/test_node_compute.py::test_add_node",
            "value": 464240.8719344674,
            "unit": "iter/sec",
            "range": "stddev: 5.287761015244344e-7",
            "extra": "mean: 2.154054199995471 usec\nrounds: 50000"
          },
          {
            "name": "benchmarks/test_node_compute.py::test_fft_node",
            "value": 54862.45203413552,
            "unit": "iter/sec",
            "range": "stddev: 0.000008645678572696857",
            "extra": "mean: 18.227402584518064 usec\nrounds: 60976"
          },
          {
            "name": "benchmarks/test_node_compute.py::test_values_buffer_node",
            "value": 58.65086285514705,
            "unit": "iter/sec",
            "range": "stddev: 0.0005522110320068214",
            "extra": "mean: 17.050047540984178 msec\nrounds: 61"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_10_callbacks",
            "value": 934088.3275265909,
            "unit": "iter/sec",
            "range": "stddev: 2.787790081919132e-7",
            "extra": "mean: 1.070562569439161 usec\nrounds: 99010"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_100_callbacks",
            "value": 212368.59976434137,
            "unit": "iter/sec",
            "range": "stddev: 0.000001973187302272225",
            "extra": "mean: 4.708794054816333 usec\nrounds: 112360"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_large_payload",
            "value": 939411.0365026455,
            "unit": "iter/sec",
            "range": "stddev: 2.607835711692956e-7",
            "extra": "mean: 1.064496755033782 usec\nrounds: 100001"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_receive_value_with_index",
            "value": 5073535.025424732,
            "unit": "iter/sec",
            "range": "stddev: 3.1696133506711905e-8",
            "extra": "mean: 197.10123119062987 nsec\nrounds: 52632"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_chain_10",
            "value": 123928.0125600529,
            "unit": "iter/sec",
            "range": "stddev: 0.0000042615704262758524",
            "extra": "mean: 8.069200654012112 usec\nrounds: 133334"
          },
          {
            "name": "benchmarks/test_port_subscribe.py::test_subscribe_1000",
            "value": 238.1650120895788,
            "unit": "iter/sec",
            "range": "stddev: 0.00015219534688809766",
            "extra": "mean: 4.198769547324942 msec\nrounds: 243"
          },
          {
            "name": "benchmarks/test_port_subscribe.py::test_unsubscribe_middle",
            "value": 726.841908250842,
            "unit": "iter/sec",
            "range": "stddev: 0.00022328743824193104",
            "extra": "mean: 1.3758149999998182 msec\nrounds: 100"
          },
          {
            "name": "benchmarks/test_port_subscribe.py::test_subscribe_unsubscribe_cycle",
            "value": 7399.691604406656,
            "unit": "iter/sec",
            "range": "stddev: 0.00001876475764351153",
            "extra": "mean: 135.1407671374414 usec\nrounds: 7717"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_f32_small",
            "value": 412255.5352843058,
            "unit": "iter/sec",
            "range": "stddev: 5.233652670079692e-7",
            "extra": "mean: 2.4256799834362623 usec\nrounds: 43479"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_f32_large",
            "value": 100363.38356230801,
            "unit": "iter/sec",
            "range": "stddev: 0.000004731260500210412",
            "extra": "mean: 9.963793213280578 usec\nrounds: 109891"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_multi_value",
            "value": 125830.35454359505,
            "unit": "iter/sec",
            "range": "stddev: 0.000002602233027286765",
            "extra": "mean: 7.947207997840784 usec\nrounds: 135136"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_string",
            "value": 148513.29982305798,
            "unit": "iter/sec",
            "range": "stddev: 0.0000025567542746831403",
            "extra": "mean: 6.733403682979383 usec\nrounds: 158731"
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
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "388cf207f851c48c6dfffd4471a0455e31e8610f",
          "message": "Merge pull request #2 from viestyle-dev/feature/editor-tuning\n\nInspector: Enhance activity reporting with rate calculations and stop…",
          "timestamp": "2026-11-19T13:28:29+09:00",
          "tree_id": "5685aa697c8899d581619856ce1e7822b9a2b35e",
          "url": "https://github.com/viestyle-dev/nonoha-core/commit/388cf207f851c48c6dfffd4471a0455e31e8610f"
        },
        "date": 1795062718706,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_endian_conversion.py::test_frombuffer_big_to_native",
            "value": 32641.42700681723,
            "unit": "iter/sec",
            "range": "stddev: 0.0000026922090913368357",
            "extra": "mean: 30.635915512858794 usec\nrounds: 35461"
          },
          {
            "name": "benchmarks/test_endian_conversion.py::test_astype_native_to_big",
            "value": 32674.73191492595,
            "unit": "iter/sec",
            "range": "stddev: 0.0000033358566288980204",
            "extra": "mean: 30.604688742471247 usec\nrounds: 35212"
          },
          {
            "name": "benchmarks/test_endian_conversion.py::test_total_cost_convert_once",
            "value": 2743.590381240384,
            "unit": "iter/sec",
            "range": "stddev: 0.000020455345497987126",
            "extra": "mean: 364.4858965965238 usec\nrounds: 3056"
          },
          {
            "name": "benchmarks/test_node_compute.py::test_add_node",
            "value": 854859.7320745058,
            "unit": "iter/sec",
            "range": "stddev: 2.880354731525928e-7",
            "extra": "mean: 1.169782553183692 usec\nrounds: 90091"
          },
          {
            "name": "benchmarks/test_node_compute.py::test_fft_node",
            "value": 109100.43185222687,
            "unit": "iter/sec",
            "range": "stddev: 0.0000013805902032346308",
            "extra": "mean: 9.165866560037715 usec\nrounds: 114943"
          },
          {
            "name": "benchmarks/test_node_compute.py::test_values_buffer_node",
            "value": 198.8244003066276,
            "unit": "iter/sec",
            "range": "stddev: 0.00046262388924941326",
            "extra": "mean: 5.029563768117981 msec\nrounds: 207"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_10_callbacks",
            "value": 1899629.6411934292,
            "unit": "iter/sec",
            "range": "stddev: 7.295618424611953e-8",
            "extra": "mean: 526.418401942022 nsec\nrounds: 185186"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_100_callbacks",
            "value": 424775.3761034578,
            "unit": "iter/sec",
            "range": "stddev: 2.062765217510039e-7",
            "extra": "mean: 2.354185426597049 usec\nrounds: 44643"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_large_payload",
            "value": 1888154.4481188366,
            "unit": "iter/sec",
            "range": "stddev: 8.599093504530133e-8",
            "extra": "mean: 529.617691495036 nsec\nrounds: 185186"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_receive_value_with_index",
            "value": 10327345.553286014,
            "unit": "iter/sec",
            "range": "stddev: 1.2506484205930819e-8",
            "extra": "mean: 96.8303030861931 nsec\nrounds: 107527"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_chain_10",
            "value": 259184.10629532908,
            "unit": "iter/sec",
            "range": "stddev: 5.054930964920108e-7",
            "extra": "mean: 3.858261273399779 usec\nrounds: 138889"
          },
          {
            "name": "benchmarks/test_port_subscribe.py::test_subscribe_1000",
            "value": 478.9804923381347,
            "unit": "iter/sec",
            "range": "stddev: 0.00012447019093607327",
            "extra": "mean: 2.0877676982595217 msec\nrounds: 517"
          },
          {
            "name": "benchmarks/test_port_subscribe.py::test_unsubscribe_middle",
            "value": 1516.537078571966,
            "unit": "iter/sec",
            "range": "stddev: 0.00010029558885060004",
            "extra": "mean: 659.3970000005811 usec\nrounds: 100"
          },
          {
            "name": "benchmarks/test_port_subscribe.py::test_subscribe_unsubscribe_cycle",
            "value": 14904.115630896933,
            "unit": "iter/sec",
            "range": "stddev: 0.0000051375729473952094",
            "extra": "mean: 67.09556103597002 usec\nrounds: 15409"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_f32_small",
            "value": 751427.683515947,
            "unit": "iter/sec",
            "range": "stddev: 1.55802230647928e-7",
            "extra": "mean: 1.330800051604914 usec\nrounds: 77520"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_f32_large",
            "value": 206340.81904689092,
            "unit": "iter/sec",
            "range": "stddev: 6.499089312421856e-7",
            "extra": "mean: 4.846350831692445 usec\nrounds: 108696"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_multi_value",
            "value": 227345.1140105607,
            "unit": "iter/sec",
            "range": "stddev: 6.262466596902115e-7",
            "extra": "mean: 4.398599038963941 usec\nrounds: 121952"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_string",
            "value": 268379.994269807,
            "unit": "iter/sec",
            "range": "stddev: 6.200308494838584e-7",
            "extra": "mean: 3.7260601436435046 usec\nrounds: 142858"
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
          "id": "690f9e8d3af6a456c5d28b14cf9d509d3cfcd197",
          "message": "README.md: Update ecosystem section with detailed layers and links; pyproject.toml and uv.lock: bump version to 1.1.0",
          "timestamp": "2026-11-20T02:56:53+09:00",
          "tree_id": "045a2d1c72227b7f23ca4a829321c18cab9752ae",
          "url": "https://github.com/viestyle-dev/nonoha-core/commit/690f9e8d3af6a456c5d28b14cf9d509d3cfcd197"
        },
        "date": 1795111235557,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_endian_conversion.py::test_frombuffer_big_to_native",
            "value": 20056.01332986907,
            "unit": "iter/sec",
            "range": "stddev: 0.00001759988829234945",
            "extra": "mean: 49.86035776665133 usec\nrounds: 21187"
          },
          {
            "name": "benchmarks/test_endian_conversion.py::test_astype_native_to_big",
            "value": 20632.545677220136,
            "unit": "iter/sec",
            "range": "stddev: 0.000006815528380742945",
            "extra": "mean: 48.46711674091067 usec\nrounds: 21552"
          },
          {
            "name": "benchmarks/test_endian_conversion.py::test_total_cost_convert_once",
            "value": 1894.6548731200287,
            "unit": "iter/sec",
            "range": "stddev: 0.0001358215570590922",
            "extra": "mean: 527.8006111758217 usec\nrounds: 3436"
          },
          {
            "name": "benchmarks/test_node_compute.py::test_add_node",
            "value": 482698.6491119772,
            "unit": "iter/sec",
            "range": "stddev: 5.920034661639849e-7",
            "extra": "mean: 2.0716859304241817 usec\nrounds: 52084"
          },
          {
            "name": "benchmarks/test_node_compute.py::test_fft_node",
            "value": 57930.83374912489,
            "unit": "iter/sec",
            "range": "stddev: 0.000005131403999760815",
            "extra": "mean: 17.261964575386525 usec\nrounds: 62894"
          },
          {
            "name": "benchmarks/test_node_compute.py::test_values_buffer_node",
            "value": 58.253912266973956,
            "unit": "iter/sec",
            "range": "stddev: 0.0009624046363448142",
            "extra": "mean: 17.16622903225905 msec\nrounds: 62"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_10_callbacks",
            "value": 934556.326914394,
            "unit": "iter/sec",
            "range": "stddev: 3.2598353963220023e-7",
            "extra": "mean: 1.0700264619700655 usec\nrounds: 99010"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_100_callbacks",
            "value": 207478.62961773813,
            "unit": "iter/sec",
            "range": "stddev: 0.0000037859851618317445",
            "extra": "mean: 4.819773495913365 usec\nrounds: 112360"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_large_payload",
            "value": 937961.1768757495,
            "unit": "iter/sec",
            "range": "stddev: 2.498448301449155e-7",
            "extra": "mean: 1.0661422078585172 usec\nrounds: 99010"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_receive_value_with_index",
            "value": 5005945.181646487,
            "unit": "iter/sec",
            "range": "stddev: 2.8703683782443583e-8",
            "extra": "mean: 199.76247515987887 nsec\nrounds: 54348"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_chain_10",
            "value": 121669.20169186148,
            "unit": "iter/sec",
            "range": "stddev: 0.000002195048581570857",
            "extra": "mean: 8.219006832415918 usec\nrounds: 131579"
          },
          {
            "name": "benchmarks/test_port_subscribe.py::test_subscribe_1000",
            "value": 235.70617374855922,
            "unit": "iter/sec",
            "range": "stddev: 0.00035618685563038917",
            "extra": "mean: 4.242570247934003 msec\nrounds: 242"
          },
          {
            "name": "benchmarks/test_port_subscribe.py::test_unsubscribe_middle",
            "value": 744.8650863104405,
            "unit": "iter/sec",
            "range": "stddev: 0.00007598087262385896",
            "extra": "mean: 1.3425250000014444 msec\nrounds: 100"
          },
          {
            "name": "benchmarks/test_port_subscribe.py::test_subscribe_unsubscribe_cycle",
            "value": 7583.4977762455355,
            "unit": "iter/sec",
            "range": "stddev: 0.000011140998434962693",
            "extra": "mean: 131.8652723987589 usec\nrounds: 7746"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_f32_small",
            "value": 424909.99220498523,
            "unit": "iter/sec",
            "range": "stddev: 4.4358233687280663e-7",
            "extra": "mean: 2.3534395950789877 usec\nrounds: 45046"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_f32_large",
            "value": 110356.28567376947,
            "unit": "iter/sec",
            "range": "stddev: 0.0000024252842715835452",
            "extra": "mean: 9.06155905750722 usec\nrounds: 117648"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_multi_value",
            "value": 129406.903273103,
            "unit": "iter/sec",
            "range": "stddev: 0.0000023267194757284997",
            "extra": "mean: 7.727563017944873 usec\nrounds: 138889"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_string",
            "value": 152616.37671705903,
            "unit": "iter/sec",
            "range": "stddev: 0.0000017613884178369016",
            "extra": "mean: 6.5523767600244875 usec\nrounds: 161291"
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
          "id": "c51e63a19c23265c6ee2525dcdbd22721d3041a3",
          "message": "Enhance node properties and initialization across various mathematical, random, script, statistics, string, time, trigonometric, and window nodes\n\n- Introduced `PROPERTIES` for nodes to define input types, shapes, and other parameters.\n- Updated constructors to initialize properties from the `PROPERTIES` dictionary.\n- Removed redundant property assignments after initialization.\n- Added tests to ensure all built-in nodes declare their properties correctly.\n- Bumped version to 1.2.0 in `uv.lock`.",
          "timestamp": "2026-11-20T14:13:50+09:00",
          "tree_id": "d37c6edfeffa61ad2ee83ca10195f69f0106b6b9",
          "url": "https://github.com/viestyle-dev/nonoha-core/commit/c51e63a19c23265c6ee2525dcdbd22721d3041a3"
        },
        "date": 1795151847801,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_endian_conversion.py::test_frombuffer_big_to_native",
            "value": 23762.417219299437,
            "unit": "iter/sec",
            "range": "stddev: 0.0000037259591895370825",
            "extra": "mean: 42.08326075462629 usec\nrounds: 24571"
          },
          {
            "name": "benchmarks/test_endian_conversion.py::test_astype_native_to_big",
            "value": 24072.983029091734,
            "unit": "iter/sec",
            "range": "stddev: 0.0000036759812962395303",
            "extra": "mean: 41.54034416056869 usec\nrounds: 24814"
          },
          {
            "name": "benchmarks/test_endian_conversion.py::test_total_cost_convert_once",
            "value": 1980.6804174254805,
            "unit": "iter/sec",
            "range": "stddev: 0.00006904584496649746",
            "extra": "mean: 504.87700650860967 usec\nrounds: 2305"
          },
          {
            "name": "benchmarks/test_node_compute.py::test_add_node",
            "value": 594478.3061721259,
            "unit": "iter/sec",
            "range": "stddev: 2.3349947869283897e-7",
            "extra": "mean: 1.6821471694048458 usec\nrounds: 64103"
          },
          {
            "name": "benchmarks/test_node_compute.py::test_fft_node",
            "value": 80055.02377751633,
            "unit": "iter/sec",
            "range": "stddev: 0.000002351017581357064",
            "extra": "mean: 12.49140844401139 usec\nrounds: 84746"
          },
          {
            "name": "benchmarks/test_node_compute.py::test_values_buffer_node",
            "value": 91.58908784710547,
            "unit": "iter/sec",
            "range": "stddev: 0.0012290480688067842",
            "extra": "mean: 10.918331249999488 msec\nrounds: 96"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_10_callbacks",
            "value": 1278274.714042753,
            "unit": "iter/sec",
            "range": "stddev: 1.740342310910681e-7",
            "extra": "mean: 782.3044522547608 nsec\nrounds: 136987"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_100_callbacks",
            "value": 267491.6594964208,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012991571361844462",
            "extra": "mean: 3.738434319345125 usec\nrounds: 142858"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_large_payload",
            "value": 1285459.7700149023,
            "unit": "iter/sec",
            "range": "stddev: 1.5289606008533447e-7",
            "extra": "mean: 777.9317745500248 nsec\nrounds: 136987"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_receive_value_with_index",
            "value": 6326050.346516827,
            "unit": "iter/sec",
            "range": "stddev: 2.3203826395621453e-8",
            "extra": "mean: 158.076516186934 nsec\nrounds: 65790"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_chain_10",
            "value": 163925.10994850204,
            "unit": "iter/sec",
            "range": "stddev: 0.000001706826967535897",
            "extra": "mean: 6.100346678517742 usec\nrounds: 185186"
          },
          {
            "name": "benchmarks/test_port_subscribe.py::test_subscribe_1000",
            "value": 293.02248776087316,
            "unit": "iter/sec",
            "range": "stddev: 0.0002465855061117663",
            "extra": "mean: 3.4127073578600897 msec\nrounds: 299"
          },
          {
            "name": "benchmarks/test_port_subscribe.py::test_unsubscribe_middle",
            "value": 930.6680242024137,
            "unit": "iter/sec",
            "range": "stddev: 0.00008079466986143855",
            "extra": "mean: 1.0744969999984733 msec\nrounds: 100"
          },
          {
            "name": "benchmarks/test_port_subscribe.py::test_subscribe_unsubscribe_cycle",
            "value": 9923.413715647257,
            "unit": "iter/sec",
            "range": "stddev: 0.00000863364731305922",
            "extra": "mean: 100.77177357054038 usec\nrounds: 10352"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_f32_small",
            "value": 547167.9843131119,
            "unit": "iter/sec",
            "range": "stddev: 2.7395325026580537e-7",
            "extra": "mean: 1.8275923092525976 usec\nrounds: 58824"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_f32_large",
            "value": 137270.69732635096,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012978702598549649",
            "extra": "mean: 7.284875938399101 usec\nrounds: 144928"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_multi_value",
            "value": 167947.95968025827,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012253188805528932",
            "extra": "mean: 5.954225355900807 usec\nrounds: 181819"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_string",
            "value": 189390.39912180218,
            "unit": "iter/sec",
            "range": "stddev: 8.699472450910508e-7",
            "extra": "mean: 5.280098698967694 usec\nrounds: 100001"
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
          "id": "08e7dff6fb22fa487383c384147f202f116a8bb9",
          "message": "Bump version to 1.2.1 and enhance GraphProxyNode input/output synchronization",
          "timestamp": "2026-11-20T22:42:36+09:00",
          "tree_id": "83f75a979596f5f0a0a6231003e2099f39043caf",
          "url": "https://github.com/viestyle-dev/nonoha-core/commit/08e7dff6fb22fa487383c384147f202f116a8bb9"
        },
        "date": 1795182376856,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_endian_conversion.py::test_frombuffer_big_to_native",
            "value": 32487.538138591146,
            "unit": "iter/sec",
            "range": "stddev: 0.000004146625854513217",
            "extra": "mean: 30.78103350687951 usec\nrounds: 35336"
          },
          {
            "name": "benchmarks/test_endian_conversion.py::test_astype_native_to_big",
            "value": 33412.16789070567,
            "unit": "iter/sec",
            "range": "stddev: 0.000002519717261103606",
            "extra": "mean: 29.929216304404243 usec\nrounds: 35843"
          },
          {
            "name": "benchmarks/test_endian_conversion.py::test_total_cost_convert_once",
            "value": 2722.9373610094462,
            "unit": "iter/sec",
            "range": "stddev: 0.000021932186415575013",
            "extra": "mean: 367.250460594246 usec\nrounds: 2931"
          },
          {
            "name": "benchmarks/test_node_compute.py::test_add_node",
            "value": 884804.7190689389,
            "unit": "iter/sec",
            "range": "stddev: 1.3966419166316396e-7",
            "extra": "mean: 1.1301928871404652 usec\nrounds: 92593"
          },
          {
            "name": "benchmarks/test_node_compute.py::test_fft_node",
            "value": 108710.8961907544,
            "unit": "iter/sec",
            "range": "stddev: 0.0000024298446990030096",
            "extra": "mean: 9.19870992734073 usec\nrounds: 113637"
          },
          {
            "name": "benchmarks/test_node_compute.py::test_values_buffer_node",
            "value": 195.54177967388708,
            "unit": "iter/sec",
            "range": "stddev: 0.0006971961305846492",
            "extra": "mean: 5.113996618358186 msec\nrounds: 207"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_10_callbacks",
            "value": 1844991.332980365,
            "unit": "iter/sec",
            "range": "stddev: 9.645985398282013e-8",
            "extra": "mean: 542.0079661747668 nsec\nrounds: 196079"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_100_callbacks",
            "value": 400667.9681364876,
            "unit": "iter/sec",
            "range": "stddev: 3.4453687338248734e-7",
            "extra": "mean: 2.49583215910897 usec\nrounds: 43291"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_large_payload",
            "value": 1800619.1700061897,
            "unit": "iter/sec",
            "range": "stddev: 9.713657278996788e-8",
            "extra": "mean: 555.3645194151387 nsec\nrounds: 192308"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_receive_value_with_index",
            "value": 9827412.336970057,
            "unit": "iter/sec",
            "range": "stddev: 2.3101177837400995e-8",
            "extra": "mean: 101.75618623811118 nsec\nrounds: 102041"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_chain_10",
            "value": 250837.13096555267,
            "unit": "iter/sec",
            "range": "stddev: 6.001337574389828e-7",
            "extra": "mean: 3.9866506053177964 usec\nrounds: 131579"
          },
          {
            "name": "benchmarks/test_port_subscribe.py::test_subscribe_1000",
            "value": 478.1969235438976,
            "unit": "iter/sec",
            "range": "stddev: 0.00018392827775116233",
            "extra": "mean: 2.091188693956961 msec\nrounds: 513"
          },
          {
            "name": "benchmarks/test_port_subscribe.py::test_unsubscribe_middle",
            "value": 1562.1289943645309,
            "unit": "iter/sec",
            "range": "stddev: 0.000026519634349203355",
            "extra": "mean: 640.1519999997163 usec\nrounds: 100"
          },
          {
            "name": "benchmarks/test_port_subscribe.py::test_subscribe_unsubscribe_cycle",
            "value": 15086.573564424461,
            "unit": "iter/sec",
            "range": "stddev: 0.000005700467178500459",
            "extra": "mean: 66.28410326106736 usec\nrounds: 15456"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_f32_small",
            "value": 726059.5613113666,
            "unit": "iter/sec",
            "range": "stddev: 1.7729861855221577e-7",
            "extra": "mean: 1.377297474319676 usec\nrounds: 76336"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_f32_large",
            "value": 204201.0607624468,
            "unit": "iter/sec",
            "range": "stddev: 0.0000012762423067051061",
            "extra": "mean: 4.897134208148556 usec\nrounds: 107527"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_multi_value",
            "value": 219750.23160051816,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011896521846521122",
            "extra": "mean: 4.550620915011778 usec\nrounds: 116280"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_string",
            "value": 266527.5866197048,
            "unit": "iter/sec",
            "range": "stddev: 0.0000019082685486377665",
            "extra": "mean: 3.751956833747387 usec\nrounds: 144928"
          }
        ]
      }
    ]
  }
}