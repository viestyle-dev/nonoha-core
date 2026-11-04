window.BENCHMARK_DATA = {
  "lastUpdate": 1793751022356,
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
      }
    ]
  }
}