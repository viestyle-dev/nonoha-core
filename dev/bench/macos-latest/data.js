window.BENCHMARK_DATA = {
  "lastUpdate": 1795111158364,
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
        "date": 1793751020910,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_endian_conversion.py::test_frombuffer_big_to_native",
            "value": 75728.65475151085,
            "unit": "iter/sec",
            "range": "stddev: 0.00004084871100953017",
            "extra": "mean: 13.205041120581228 usec\nrounds: 123077"
          },
          {
            "name": "benchmarks/test_endian_conversion.py::test_astype_native_to_big",
            "value": 85529.1870957835,
            "unit": "iter/sec",
            "range": "stddev: 0.000012453881843968036",
            "extra": "mean: 11.691915169030047 usec\nrounds: 131874"
          },
          {
            "name": "benchmarks/test_endian_conversion.py::test_total_cost_convert_once",
            "value": 4111.266312748901,
            "unit": "iter/sec",
            "range": "stddev: 0.000045499660370649405",
            "extra": "mean: 243.234060731856 usec\nrounds: 5302"
          },
          {
            "name": "benchmarks/test_node_compute.py::test_add_node",
            "value": 866253.4908059275,
            "unit": "iter/sec",
            "range": "stddev: 6.660678765026628e-7",
            "extra": "mean: 1.154396502425254 usec\nrounds: 101699"
          },
          {
            "name": "benchmarks/test_node_compute.py::test_fft_node",
            "value": 86512.72474943106,
            "unit": "iter/sec",
            "range": "stddev: 0.000021957603628534378",
            "extra": "mean: 11.558993233611872 usec\nrounds: 120005"
          },
          {
            "name": "benchmarks/test_node_compute.py::test_values_buffer_node",
            "value": 125.15646969021307,
            "unit": "iter/sec",
            "range": "stddev: 0.0033224341611578167",
            "extra": "mean: 7.989998459330126 msec\nrounds: 209"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_10_callbacks",
            "value": 1133512.4028936578,
            "unit": "iter/sec",
            "range": "stddev: 0.0000022148607722788485",
            "extra": "mean: 882.2135491831928 nsec\nrounds: 172682"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_100_callbacks",
            "value": 209385.46609673183,
            "unit": "iter/sec",
            "range": "stddev: 0.00001791411673359491",
            "extra": "mean: 4.775880669473116 usec\nrounds: 183218"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_large_payload",
            "value": 971077.5635563913,
            "unit": "iter/sec",
            "range": "stddev: 0.0000019203049152263753",
            "extra": "mean: 1.029783858189133 usec\nrounds: 172682"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_receive_value_with_index",
            "value": 4638169.0386382565,
            "unit": "iter/sec",
            "range": "stddev: 3.3422069483384296e-7",
            "extra": "mean: 215.6023188610509 nsec\nrounds: 91601"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_chain_10",
            "value": 114726.64631962265,
            "unit": "iter/sec",
            "range": "stddev: 0.00001543441282438734",
            "extra": "mean: 8.716370887492435 usec\nrounds: 112158"
          },
          {
            "name": "benchmarks/test_port_subscribe.py::test_subscribe_1000",
            "value": 171.42819949489657,
            "unit": "iter/sec",
            "range": "stddev: 0.0020627186563605257",
            "extra": "mean: 5.833345989437228 msec\nrounds: 284"
          },
          {
            "name": "benchmarks/test_port_subscribe.py::test_unsubscribe_middle",
            "value": 605.6290238066721,
            "unit": "iter/sec",
            "range": "stddev: 0.0005695244031100955",
            "extra": "mean: 1.6511758200003612 msec\nrounds: 100"
          },
          {
            "name": "benchmarks/test_port_subscribe.py::test_subscribe_unsubscribe_cycle",
            "value": 6169.003573046495,
            "unit": "iter/sec",
            "range": "stddev: 0.00012164285061689453",
            "extra": "mean: 162.1007328264783 usec\nrounds: 11311"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_f32_small",
            "value": 340315.9787661777,
            "unit": "iter/sec",
            "range": "stddev: 0.000007270660256475223",
            "extra": "mean: 2.938445628164561 usec\nrounds: 75712"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_f32_large",
            "value": 92024.35759454408,
            "unit": "iter/sec",
            "range": "stddev: 0.00001743800630180978",
            "extra": "mean: 10.86668819146734 usec\nrounds: 109099"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_multi_value",
            "value": 125833.16656029916,
            "unit": "iter/sec",
            "range": "stddev: 0.000034851876998642655",
            "extra": "mean: 7.947030400135411 usec\nrounds: 101266"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_string",
            "value": 146239.4899431501,
            "unit": "iter/sec",
            "range": "stddev: 0.000007407058420187967",
            "extra": "mean: 6.838098248214248 usec\nrounds: 107147"
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
        "date": 1795012937126,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_endian_conversion.py::test_frombuffer_big_to_native",
            "value": 67006.85619866592,
            "unit": "iter/sec",
            "range": "stddev: 0.000027593940002482355",
            "extra": "mean: 14.923845957421738 usec\nrounds: 127666"
          },
          {
            "name": "benchmarks/test_endian_conversion.py::test_astype_native_to_big",
            "value": 92472.81794915286,
            "unit": "iter/sec",
            "range": "stddev: 0.000019360883161636102",
            "extra": "mean: 10.813988609602665 usec\nrounds: 128354"
          },
          {
            "name": "benchmarks/test_endian_conversion.py::test_total_cost_convert_once",
            "value": 3444.952492882057,
            "unit": "iter/sec",
            "range": "stddev: 0.0001557422769839076",
            "extra": "mean: 290.27976497968984 usec\nrounds: 5157"
          },
          {
            "name": "benchmarks/test_node_compute.py::test_add_node",
            "value": 694787.9303472087,
            "unit": "iter/sec",
            "range": "stddev: 0.0000013074038177003302",
            "extra": "mean: 1.4392880997519353 usec\nrounds: 103897"
          },
          {
            "name": "benchmarks/test_node_compute.py::test_fft_node",
            "value": 86204.9466090409,
            "unit": "iter/sec",
            "range": "stddev: 0.000018038465803813353",
            "extra": "mean: 11.600262390222548 usec\nrounds: 120599"
          },
          {
            "name": "benchmarks/test_node_compute.py::test_values_buffer_node",
            "value": 177.50121611467614,
            "unit": "iter/sec",
            "range": "stddev: 0.0015101040868595321",
            "extra": "mean: 5.6337642180093095 msec\nrounds: 211"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_10_callbacks",
            "value": 1336217.5247415593,
            "unit": "iter/sec",
            "range": "stddev: 0.000001734550635939938",
            "extra": "mean: 748.3811441506115 nsec\nrounds: 172652"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_100_callbacks",
            "value": 311263.85484243726,
            "unit": "iter/sec",
            "range": "stddev: 0.0000017550591969219853",
            "extra": "mean: 3.2127083965666468 usec\nrounds: 183218"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_large_payload",
            "value": 1361057.6828061114,
            "unit": "iter/sec",
            "range": "stddev: 4.807377226980446e-7",
            "extra": "mean: 734.7227179516448 nsec\nrounds: 172652"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_receive_value_with_index",
            "value": 7879045.368585127,
            "unit": "iter/sec",
            "range": "stddev: 6.250293329197612e-8",
            "extra": "mean: 126.91892903516369 nsec\nrounds: 91609"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_chain_10",
            "value": 196418.00220261313,
            "unit": "iter/sec",
            "range": "stddev: 0.000021582902097152655",
            "extra": "mean: 5.091183032034199 usec\nrounds: 112677"
          },
          {
            "name": "benchmarks/test_port_subscribe.py::test_subscribe_1000",
            "value": 213.39810370829878,
            "unit": "iter/sec",
            "range": "stddev: 0.004177726523401131",
            "extra": "mean: 4.68607725477699 msec\nrounds: 314"
          },
          {
            "name": "benchmarks/test_port_subscribe.py::test_unsubscribe_middle",
            "value": 663.6764547023091,
            "unit": "iter/sec",
            "range": "stddev: 0.0005840313378488579",
            "extra": "mean: 1.506758289999226 msec\nrounds: 100"
          },
          {
            "name": "benchmarks/test_port_subscribe.py::test_subscribe_unsubscribe_cycle",
            "value": 7602.711200598597,
            "unit": "iter/sec",
            "range": "stddev: 0.00020829118685505288",
            "extra": "mean: 131.53202503881315 usec\nrounds: 12221"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_f32_small",
            "value": 739494.2228332591,
            "unit": "iter/sec",
            "range": "stddev: 0.000006151114352645664",
            "extra": "mean: 1.3522756082781633 usec\nrounds: 94118"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_f32_large",
            "value": 191252.18340065068,
            "unit": "iter/sec",
            "range": "stddev: 0.00005265321326792037",
            "extra": "mean: 5.228698476634478 usec\nrounds: 166667"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_multi_value",
            "value": 208411.1722393038,
            "unit": "iter/sec",
            "range": "stddev: 0.000019621742456830815",
            "extra": "mean: 4.798207261421527 usec\nrounds: 146349"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_string",
            "value": 199178.51585484532,
            "unit": "iter/sec",
            "range": "stddev: 0.0000036695929384690724",
            "extra": "mean: 5.020621806062491 usec\nrounds: 121833"
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
        "date": 1795062654547,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_endian_conversion.py::test_frombuffer_big_to_native",
            "value": 73286.16945535508,
            "unit": "iter/sec",
            "range": "stddev: 0.000019627616283327393",
            "extra": "mean: 13.64513942305562 usec\nrounds: 123717"
          },
          {
            "name": "benchmarks/test_endian_conversion.py::test_astype_native_to_big",
            "value": 95013.91224829323,
            "unit": "iter/sec",
            "range": "stddev: 0.000009306711418886461",
            "extra": "mean: 10.524774491831993 usec\nrounds: 129033"
          },
          {
            "name": "benchmarks/test_endian_conversion.py::test_total_cost_convert_once",
            "value": 2761.623980980378,
            "unit": "iter/sec",
            "range": "stddev: 0.00031321051830055966",
            "extra": "mean: 362.10577793614016 usec\nrounds: 4913"
          },
          {
            "name": "benchmarks/test_node_compute.py::test_add_node",
            "value": 624511.3345726389,
            "unit": "iter/sec",
            "range": "stddev: 0.0000021093872079312517",
            "extra": "mean: 1.6012519623591652 usec\nrounds: 100848"
          },
          {
            "name": "benchmarks/test_node_compute.py::test_fft_node",
            "value": 100685.92930521978,
            "unit": "iter/sec",
            "range": "stddev: 0.000007200890470715356",
            "extra": "mean: 9.931874363185303 usec\nrounds: 123077"
          },
          {
            "name": "benchmarks/test_node_compute.py::test_values_buffer_node",
            "value": 160.50651929801202,
            "unit": "iter/sec",
            "range": "stddev: 0.004435384984223416",
            "extra": "mean: 6.230276529411885 msec\nrounds: 204"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_10_callbacks",
            "value": 1216683.5538054162,
            "unit": "iter/sec",
            "range": "stddev: 8.623128359886168e-7",
            "extra": "mean: 821.9064002898416 nsec\nrounds: 173914"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_100_callbacks",
            "value": 297288.5849276104,
            "unit": "iter/sec",
            "range": "stddev: 0.0000021041150820653725",
            "extra": "mean: 3.3637349387077857 usec\nrounds: 183218"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_large_payload",
            "value": 1351520.634614539,
            "unit": "iter/sec",
            "range": "stddev: 0.00000406296575348693",
            "extra": "mean: 739.9073120960901 nsec\nrounds: 176461"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_receive_value_with_index",
            "value": 7889263.87010267,
            "unit": "iter/sec",
            "range": "stddev: 3.141263217544278e-7",
            "extra": "mean: 126.75453837838236 nsec\nrounds: 91601"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_chain_10",
            "value": 174135.94081392497,
            "unit": "iter/sec",
            "range": "stddev: 0.000005054666404887253",
            "extra": "mean: 5.742639889995838 usec\nrounds: 120005"
          },
          {
            "name": "benchmarks/test_port_subscribe.py::test_subscribe_1000",
            "value": 219.8695906912846,
            "unit": "iter/sec",
            "range": "stddev: 0.0014537186364564471",
            "extra": "mean: 4.5481505507693605 msec\nrounds: 325"
          },
          {
            "name": "benchmarks/test_port_subscribe.py::test_unsubscribe_middle",
            "value": 709.8489504605627,
            "unit": "iter/sec",
            "range": "stddev: 0.0005051842360620491",
            "extra": "mean: 1.408750410000863 msec\nrounds: 100"
          },
          {
            "name": "benchmarks/test_port_subscribe.py::test_subscribe_unsubscribe_cycle",
            "value": 8008.406097072273,
            "unit": "iter/sec",
            "range": "stddev: 0.00024123741162760236",
            "extra": "mean: 124.86879260101229 usec\nrounds: 12353"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_f32_small",
            "value": 623670.5906847923,
            "unit": "iter/sec",
            "range": "stddev: 0.000002332001182562258",
            "extra": "mean: 1.6034105422576492 usec\nrounds: 93756"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_f32_large",
            "value": 196190.05893858644,
            "unit": "iter/sec",
            "range": "stddev: 0.000012127582494948764",
            "extra": "mean: 5.097098218992996 usec\nrounds: 169005"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_multi_value",
            "value": 181499.63292149297,
            "unit": "iter/sec",
            "range": "stddev: 0.000011276913187228138",
            "extra": "mean: 5.509653016392305 usec\nrounds: 145455"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_string",
            "value": 176544.08282537563,
            "unit": "iter/sec",
            "range": "stddev: 0.000012194146396503175",
            "extra": "mean: 5.664307656174045 usec\nrounds: 118218"
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
        "date": 1795111157251,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_endian_conversion.py::test_frombuffer_big_to_native",
            "value": 66198.94307091946,
            "unit": "iter/sec",
            "range": "stddev: 0.00005323542259515965",
            "extra": "mean: 15.105981358776258 usec\nrounds: 124348"
          },
          {
            "name": "benchmarks/test_endian_conversion.py::test_astype_native_to_big",
            "value": 61259.268546176776,
            "unit": "iter/sec",
            "range": "stddev: 0.00010514731788701398",
            "extra": "mean: 16.324060403140585 usec\nrounds: 129033"
          },
          {
            "name": "benchmarks/test_endian_conversion.py::test_total_cost_convert_once",
            "value": 3053.730471023192,
            "unit": "iter/sec",
            "range": "stddev: 0.00019471443588168203",
            "extra": "mean: 327.4683242312924 usec\nrounds: 4944"
          },
          {
            "name": "benchmarks/test_node_compute.py::test_add_node",
            "value": 669333.055112007,
            "unit": "iter/sec",
            "range": "stddev: 0.0000024445799017460146",
            "extra": "mean: 1.494024525402619 usec\nrounds: 103456"
          },
          {
            "name": "benchmarks/test_node_compute.py::test_fft_node",
            "value": 82901.03342764925,
            "unit": "iter/sec",
            "range": "stddev: 0.00001671310432689533",
            "extra": "mean: 12.062575804591583 usec\nrounds: 121833"
          },
          {
            "name": "benchmarks/test_node_compute.py::test_values_buffer_node",
            "value": 109.60318238980446,
            "unit": "iter/sec",
            "range": "stddev: 0.004342796855416726",
            "extra": "mean: 9.123822668246012 msec\nrounds: 211"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_10_callbacks",
            "value": 1328612.2820918509,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011886326382064293",
            "extra": "mean: 752.6650276223462 nsec\nrounds: 172682"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_100_callbacks",
            "value": 269331.298491169,
            "unit": "iter/sec",
            "range": "stddev: 0.00000291666703293016",
            "extra": "mean: 3.7128993384806654 usec\nrounds: 183218"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_large_payload",
            "value": 1111593.3316940924,
            "unit": "iter/sec",
            "range": "stddev: 0.000008373152683989202",
            "extra": "mean: 899.6095707735012 nsec\nrounds: 172682"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_receive_value_with_index",
            "value": 6328048.343900372,
            "unit": "iter/sec",
            "range": "stddev: 4.2531753352365774e-7",
            "extra": "mean: 158.02660562223394 nsec\nrounds: 91955"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_chain_10",
            "value": 147863.93301099807,
            "unit": "iter/sec",
            "range": "stddev: 0.000006689040356186968",
            "extra": "mean: 6.762974443034871 usec\nrounds: 111633"
          },
          {
            "name": "benchmarks/test_port_subscribe.py::test_subscribe_1000",
            "value": 212.65992204239012,
            "unit": "iter/sec",
            "range": "stddev: 0.0023089907681183835",
            "extra": "mean: 4.7023434900002785 msec\nrounds: 300"
          },
          {
            "name": "benchmarks/test_port_subscribe.py::test_unsubscribe_middle",
            "value": 726.0400274725065,
            "unit": "iter/sec",
            "range": "stddev: 0.0005455938985943407",
            "extra": "mean: 1.3773345299999562 msec\nrounds: 100"
          },
          {
            "name": "benchmarks/test_port_subscribe.py::test_subscribe_unsubscribe_cycle",
            "value": 7829.1674140214645,
            "unit": "iter/sec",
            "range": "stddev: 0.0001059346111470256",
            "extra": "mean: 127.72750244286173 usec\nrounds: 11462"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_f32_small",
            "value": 656792.5320308973,
            "unit": "iter/sec",
            "range": "stddev: 0.0000018411961124147496",
            "extra": "mean: 1.5225508074945555 usec\nrounds: 94118"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_f32_large",
            "value": 192079.98190405895,
            "unit": "iter/sec",
            "range": "stddev: 0.000017993880987476705",
            "extra": "mean: 5.206164588767428 usec\nrounds: 176461"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_multi_value",
            "value": 208895.65938047497,
            "unit": "iter/sec",
            "range": "stddev: 0.000010544664717377677",
            "extra": "mean: 4.787078884097999 usec\nrounds: 147254"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_string",
            "value": 159116.3108162317,
            "unit": "iter/sec",
            "range": "stddev: 0.00005504464582003858",
            "extra": "mean: 6.28471081858434 usec\nrounds: 118232"
          }
        ]
      }
    ]
  }
}