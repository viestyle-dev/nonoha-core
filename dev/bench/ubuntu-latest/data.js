window.BENCHMARK_DATA = {
  "lastUpdate": 1795111078315,
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
        "date": 1793750936377,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_endian_conversion.py::test_frombuffer_big_to_native",
            "value": 26319.001989136425,
            "unit": "iter/sec",
            "range": "stddev: 0.000004059319233306739",
            "extra": "mean: 37.99536169391094 usec\nrounds: 28502"
          },
          {
            "name": "benchmarks/test_endian_conversion.py::test_astype_native_to_big",
            "value": 26927.193284124496,
            "unit": "iter/sec",
            "range": "stddev: 0.0000031239786488683347",
            "extra": "mean: 37.13717911289222 usec\nrounds: 29032"
          },
          {
            "name": "benchmarks/test_endian_conversion.py::test_total_cost_convert_once",
            "value": 2949.443983212774,
            "unit": "iter/sec",
            "range": "stddev: 0.00001554396745537822",
            "extra": "mean: 339.04695450792 usec\nrounds: 3605"
          },
          {
            "name": "benchmarks/test_node_compute.py::test_add_node",
            "value": 492782.2060421965,
            "unit": "iter/sec",
            "range": "stddev: 2.1112089487403264e-7",
            "extra": "mean: 2.029294052704424 usec\nrounds: 51267"
          },
          {
            "name": "benchmarks/test_node_compute.py::test_fft_node",
            "value": 68871.17469901146,
            "unit": "iter/sec",
            "range": "stddev: 0.0000026861383260251085",
            "extra": "mean: 14.519862691036014 usec\nrounds: 72224"
          },
          {
            "name": "benchmarks/test_node_compute.py::test_values_buffer_node",
            "value": 100.09059821967085,
            "unit": "iter/sec",
            "range": "stddev: 0.00027664453926244946",
            "extra": "mean: 9.990948378640716 msec\nrounds: 103"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_10_callbacks",
            "value": 1086026.6181788386,
            "unit": "iter/sec",
            "range": "stddev: 1.1821348782129747e-7",
            "extra": "mean: 920.7877442975795 nsec\nrounds: 113033"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_100_callbacks",
            "value": 270444.91942471784,
            "unit": "iter/sec",
            "range": "stddev: 5.034019992318949e-7",
            "extra": "mean: 3.6976105971122304 usec\nrounds: 143001"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_large_payload",
            "value": 1090470.4149338722,
            "unit": "iter/sec",
            "range": "stddev: 1.1639220318901828e-7",
            "extra": "mean: 917.0354246251213 nsec\nrounds: 113805"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_receive_value_with_index",
            "value": 6348776.841800167,
            "unit": "iter/sec",
            "range": "stddev: 1.4685927201484978e-8",
            "extra": "mean: 157.51065518884715 nsec\nrounds: 66103"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_chain_10",
            "value": 134859.82426021542,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011170451178615468",
            "extra": "mean: 7.415106800602637 usec\nrounds: 141563"
          },
          {
            "name": "benchmarks/test_port_subscribe.py::test_subscribe_1000",
            "value": 250.30047790172415,
            "unit": "iter/sec",
            "range": "stddev: 0.00008224761148368033",
            "extra": "mean: 3.995198125001709 msec\nrounds: 256"
          },
          {
            "name": "benchmarks/test_port_subscribe.py::test_unsubscribe_middle",
            "value": 817.0949266800927,
            "unit": "iter/sec",
            "range": "stddev: 0.00005120256047203074",
            "extra": "mean: 1.2238480100018023 msec\nrounds: 100"
          },
          {
            "name": "benchmarks/test_port_subscribe.py::test_subscribe_unsubscribe_cycle",
            "value": 8161.974028440889,
            "unit": "iter/sec",
            "range": "stddev: 0.000005600504094448389",
            "extra": "mean: 122.51938030131436 usec\nrounds: 8559"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_f32_small",
            "value": 361438.4684711895,
            "unit": "iter/sec",
            "range": "stddev: 5.193575017974438e-7",
            "extra": "mean: 2.766722657468627 usec\nrounds: 189394"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_f32_large",
            "value": 113559.41562321201,
            "unit": "iter/sec",
            "range": "stddev: 0.000001767287032492971",
            "extra": "mean: 8.805962891866061 usec\nrounds: 120701"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_multi_value",
            "value": 98035.12301217626,
            "unit": "iter/sec",
            "range": "stddev: 0.0000016153161194957651",
            "extra": "mean: 10.200425819589139 usec\nrounds: 102271"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_string",
            "value": 133411.4917564342,
            "unit": "iter/sec",
            "range": "stddev: 0.0000014772796256170943",
            "extra": "mean: 7.495606164315089 usec\nrounds: 139025"
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
        "date": 1795012864507,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_endian_conversion.py::test_frombuffer_big_to_native",
            "value": 30530.894812210918,
            "unit": "iter/sec",
            "range": "stddev: 0.0000020007008101756445",
            "extra": "mean: 32.753707552654085 usec\nrounds: 34266"
          },
          {
            "name": "benchmarks/test_endian_conversion.py::test_astype_native_to_big",
            "value": 31000.456664883142,
            "unit": "iter/sec",
            "range": "stddev: 0.0000020814999370847245",
            "extra": "mean: 32.25758932554001 usec\nrounds: 34044"
          },
          {
            "name": "benchmarks/test_endian_conversion.py::test_total_cost_convert_once",
            "value": 4437.866885102828,
            "unit": "iter/sec",
            "range": "stddev: 0.000005952284980144611",
            "extra": "mean: 225.3334824793487 usec\nrounds: 4566"
          },
          {
            "name": "benchmarks/test_node_compute.py::test_add_node",
            "value": 653991.4681590393,
            "unit": "iter/sec",
            "range": "stddev: 1.7776344108328183e-7",
            "extra": "mean: 1.5290719354718354 usec\nrounds: 69440"
          },
          {
            "name": "benchmarks/test_node_compute.py::test_fft_node",
            "value": 97756.72503673371,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010711697216731612",
            "extra": "mean: 10.229475257321 usec\nrounds: 102313"
          },
          {
            "name": "benchmarks/test_node_compute.py::test_values_buffer_node",
            "value": 187.39940527473837,
            "unit": "iter/sec",
            "range": "stddev: 0.00007612751521205756",
            "extra": "mean: 5.336196230366592 msec\nrounds: 191"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_10_callbacks",
            "value": 1442133.1095170327,
            "unit": "iter/sec",
            "range": "stddev: 7.343767575119581e-8",
            "extra": "mean: 693.4172673803549 nsec\nrounds: 150376"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_100_callbacks",
            "value": 323387.20706528466,
            "unit": "iter/sec",
            "range": "stddev: 3.899293117620044e-7",
            "extra": "mean: 3.0922682720659456 usec\nrounds: 166169"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_large_payload",
            "value": 1408416.3717749184,
            "unit": "iter/sec",
            "range": "stddev: 8.409410541122879e-8",
            "extra": "mean: 710.0173074101383 nsec\nrounds: 149254"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_receive_value_with_index",
            "value": 8084748.149321945,
            "unit": "iter/sec",
            "range": "stddev: 1.1149618307228708e-8",
            "extra": "mean: 123.68969095013931 nsec\nrounds: 83417"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_chain_10",
            "value": 179464.1304907966,
            "unit": "iter/sec",
            "range": "stddev: 6.776362511999922e-7",
            "extra": "mean: 5.572144122979955 usec\nrounds: 192419"
          },
          {
            "name": "benchmarks/test_port_subscribe.py::test_subscribe_1000",
            "value": 298.13543439491133,
            "unit": "iter/sec",
            "range": "stddev: 0.00035946662019161217",
            "extra": "mean: 3.354180297385906 msec\nrounds: 306"
          },
          {
            "name": "benchmarks/test_port_subscribe.py::test_unsubscribe_middle",
            "value": 905.1149120770983,
            "unit": "iter/sec",
            "range": "stddev: 0.00008743322463990756",
            "extra": "mean: 1.104832089999661 msec\nrounds: 100"
          },
          {
            "name": "benchmarks/test_port_subscribe.py::test_subscribe_unsubscribe_cycle",
            "value": 10518.729367004835,
            "unit": "iter/sec",
            "range": "stddev: 0.000004181641188992556",
            "extra": "mean: 95.06851684356491 usec\nrounds: 10657"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_f32_small",
            "value": 619229.959284773,
            "unit": "iter/sec",
            "range": "stddev: 1.3737948425369263e-7",
            "extra": "mean: 1.6149089445785423 usec\nrounds: 65604"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_f32_large",
            "value": 171922.5681750873,
            "unit": "iter/sec",
            "range": "stddev: 7.084202609827874e-7",
            "extra": "mean: 5.816572022013958 usec\nrounds: 179598"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_multi_value",
            "value": 196402.97978061595,
            "unit": "iter/sec",
            "range": "stddev: 5.690130896873467e-7",
            "extra": "mean: 5.0915724451686515 usec\nrounds: 104341"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_string",
            "value": 214723.9707621169,
            "unit": "iter/sec",
            "range": "stddev: 4.94491564335867e-7",
            "extra": "mean: 4.657141894548213 usec\nrounds: 112196"
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
        "date": 1795062579461,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_endian_conversion.py::test_frombuffer_big_to_native",
            "value": 37344.50937255047,
            "unit": "iter/sec",
            "range": "stddev: 0.0000014734301235647118",
            "extra": "mean: 26.777698162371234 usec\nrounds: 37984"
          },
          {
            "name": "benchmarks/test_endian_conversion.py::test_astype_native_to_big",
            "value": 37780.063046639465,
            "unit": "iter/sec",
            "range": "stddev: 0.0000013587066380279571",
            "extra": "mean: 26.4689870624488 usec\nrounds: 38338"
          },
          {
            "name": "benchmarks/test_endian_conversion.py::test_total_cost_convert_once",
            "value": 4700.00882640795,
            "unit": "iter/sec",
            "range": "stddev: 0.000010398690345854044",
            "extra": "mean: 212.76555788178473 usec\nrounds: 4872"
          },
          {
            "name": "benchmarks/test_node_compute.py::test_add_node",
            "value": 788583.4711512295,
            "unit": "iter/sec",
            "range": "stddev: 1.4590808707994594e-7",
            "extra": "mean: 1.2680965764348682 usec\nrounds: 87920"
          },
          {
            "name": "benchmarks/test_node_compute.py::test_fft_node",
            "value": 108516.4397950929,
            "unit": "iter/sec",
            "range": "stddev: 0.0000011385389054468897",
            "extra": "mean: 9.21519358622766 usec\nrounds: 121863"
          },
          {
            "name": "benchmarks/test_node_compute.py::test_values_buffer_node",
            "value": 218.86865253535288,
            "unit": "iter/sec",
            "range": "stddev: 0.00004145073576475583",
            "extra": "mean: 4.568950319820123 msec\nrounds: 222"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_10_callbacks",
            "value": 1572302.1398524274,
            "unit": "iter/sec",
            "range": "stddev: 8.25959572925319e-8",
            "extra": "mean: 636.0100737978149 nsec\nrounds: 168834"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_100_callbacks",
            "value": 423064.8340721492,
            "unit": "iter/sec",
            "range": "stddev: 1.668660220065094e-7",
            "extra": "mean: 2.363703904138407 usec\nrounds: 42519"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_large_payload",
            "value": 1585458.7925927879,
            "unit": "iter/sec",
            "range": "stddev: 8.196832938986474e-8",
            "extra": "mean: 630.732255339571 nsec\nrounds: 170533"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_receive_value_with_index",
            "value": 10196881.33824133,
            "unit": "iter/sec",
            "range": "stddev: 9.463481617339588e-9",
            "extra": "mean: 98.06920045737363 nsec\nrounds: 108437"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_chain_10",
            "value": 195406.06353950297,
            "unit": "iter/sec",
            "range": "stddev: 5.547886197173166e-7",
            "extra": "mean: 5.117548462347698 usec\nrounds: 109518"
          },
          {
            "name": "benchmarks/test_port_subscribe.py::test_subscribe_1000",
            "value": 363.43016604573313,
            "unit": "iter/sec",
            "range": "stddev: 0.00003262479320625914",
            "extra": "mean: 2.751560254010842 msec\nrounds: 374"
          },
          {
            "name": "benchmarks/test_port_subscribe.py::test_unsubscribe_middle",
            "value": 1195.627551782735,
            "unit": "iter/sec",
            "range": "stddev: 0.000033848732090948124",
            "extra": "mean: 836.3808600002187 usec\nrounds: 100"
          },
          {
            "name": "benchmarks/test_port_subscribe.py::test_subscribe_unsubscribe_cycle",
            "value": 12714.506356472524,
            "unit": "iter/sec",
            "range": "stddev: 0.000003406604994038994",
            "extra": "mean: 78.65032050504531 usec\nrounds: 13148"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_f32_small",
            "value": 858262.4138294839,
            "unit": "iter/sec",
            "range": "stddev: 1.2990371151320658e-7",
            "extra": "mean: 1.1651448133888336 usec\nrounds: 91100"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_f32_large",
            "value": 202920.77412630024,
            "unit": "iter/sec",
            "range": "stddev: 5.626856641404382e-7",
            "extra": "mean: 4.928031663123798 usec\nrounds: 108249"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_multi_value",
            "value": 256522.30754398083,
            "unit": "iter/sec",
            "range": "stddev: 0.000004562490761783689",
            "extra": "mean: 3.898296446707855 usec\nrounds: 142572"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_string",
            "value": 268170.0861914956,
            "unit": "iter/sec",
            "range": "stddev: 4.95796950885804e-7",
            "extra": "mean: 3.728976688644972 usec\nrounds: 144865"
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
        "date": 1795111077947,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmarks/test_endian_conversion.py::test_frombuffer_big_to_native",
            "value": 26065.54736835556,
            "unit": "iter/sec",
            "range": "stddev: 0.000003974665854317376",
            "extra": "mean: 38.36481873440467 usec\nrounds: 28461"
          },
          {
            "name": "benchmarks/test_endian_conversion.py::test_astype_native_to_big",
            "value": 26680.56276673039,
            "unit": "iter/sec",
            "range": "stddev: 0.000003414860816291693",
            "extra": "mean: 37.48046878707373 usec\nrounds: 28674"
          },
          {
            "name": "benchmarks/test_endian_conversion.py::test_total_cost_convert_once",
            "value": 3287.142415387925,
            "unit": "iter/sec",
            "range": "stddev: 0.00003291506202106714",
            "extra": "mean: 304.2155993359926 usec\nrounds: 3614"
          },
          {
            "name": "benchmarks/test_node_compute.py::test_add_node",
            "value": 503369.4771787104,
            "unit": "iter/sec",
            "range": "stddev: 2.029943049475168e-7",
            "extra": "mean: 1.9866123103146216 usec\nrounds: 52785"
          },
          {
            "name": "benchmarks/test_node_compute.py::test_fft_node",
            "value": 68123.07052518764,
            "unit": "iter/sec",
            "range": "stddev: 0.000002595352225776262",
            "extra": "mean: 14.679314838432932 usec\nrounds: 73660"
          },
          {
            "name": "benchmarks/test_node_compute.py::test_values_buffer_node",
            "value": 101.4122645375702,
            "unit": "iter/sec",
            "range": "stddev: 0.00009163985618923477",
            "extra": "mean: 9.860740262135947 msec\nrounds: 103"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_10_callbacks",
            "value": 1065266.2796235643,
            "unit": "iter/sec",
            "range": "stddev: 1.4343274268589676e-7",
            "extra": "mean: 938.7324269324902 nsec\nrounds: 111025"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_100_callbacks",
            "value": 267076.18664447,
            "unit": "iter/sec",
            "range": "stddev: 5.611754493112286e-7",
            "extra": "mean: 3.744249955654763 usec\nrounds: 140945"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_large_payload",
            "value": 1070536.801402272,
            "unit": "iter/sec",
            "range": "stddev: 1.1068956619434135e-7",
            "extra": "mean: 934.1108112215592 nsec\nrounds: 111782"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_receive_value_with_index",
            "value": 5680782.337683692,
            "unit": "iter/sec",
            "range": "stddev: 1.3538939836508475e-8",
            "extra": "mean: 176.03209215855924 nsec\nrounds: 61047"
          },
          {
            "name": "benchmarks/test_port_dispatch.py::test_dispatch_chain_10",
            "value": 131461.28770366352,
            "unit": "iter/sec",
            "range": "stddev: 9.593559193025563e-7",
            "extra": "mean: 7.606802104769984 usec\nrounds: 138447"
          },
          {
            "name": "benchmarks/test_port_subscribe.py::test_subscribe_1000",
            "value": 262.86623251355866,
            "unit": "iter/sec",
            "range": "stddev: 0.000027674098546214344",
            "extra": "mean: 3.8042162754716697 msec\nrounds: 265"
          },
          {
            "name": "benchmarks/test_port_subscribe.py::test_unsubscribe_middle",
            "value": 860.3965696853879,
            "unit": "iter/sec",
            "range": "stddev: 0.00004651209600409715",
            "extra": "mean: 1.162254749999363 msec\nrounds: 100"
          },
          {
            "name": "benchmarks/test_port_subscribe.py::test_subscribe_unsubscribe_cycle",
            "value": 8220.34800470707,
            "unit": "iter/sec",
            "range": "stddev: 0.000004163134214013161",
            "extra": "mean: 121.6493510283735 usec\nrounds: 8703"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_f32_small",
            "value": 457430.8806728776,
            "unit": "iter/sec",
            "range": "stddev: 1.791032702745102e-7",
            "extra": "mean: 2.1861226302192907 usec\nrounds: 47304"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_f32_large",
            "value": 136231.53715711794,
            "unit": "iter/sec",
            "range": "stddev: 0.000001146755992384413",
            "extra": "mean: 7.340444223621175 usec\nrounds: 145922"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_multi_value",
            "value": 141287.70183308783,
            "unit": "iter/sec",
            "range": "stddev: 0.000001233654529605202",
            "extra": "mean: 7.077756853751954 usec\nrounds: 151012"
          },
          {
            "name": "benchmarks/test_serialization.py::test_to_bytes_string",
            "value": 161179.54536887805,
            "unit": "iter/sec",
            "range": "stddev: 9.516031156401292e-7",
            "extra": "mean: 6.204261202694078 usec\nrounds: 172414"
          }
        ]
      }
    ]
  }
}