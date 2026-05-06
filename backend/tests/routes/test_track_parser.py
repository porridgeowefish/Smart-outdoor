from __future__ import annotations

import json
from pathlib import Path


def test_parse_gpx_track_metrics() -> None:
    from app.features.routes.parser import parse_track

    content = b"""<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="test">
  <trk><trkseg>
    <trkpt lat="30.000000" lon="104.000000"><ele>100</ele></trkpt>
    <trkpt lat="30.000000" lon="104.001000"><ele>115</ele></trkpt>
    <trkpt lat="30.000000" lon="104.002000"><ele>110</ele></trkpt>
  </trkseg></trk>
</gpx>
"""

    result = parse_track(content, "gpx")

    assert result.distance_km > 0
    assert result.elevation_gain_m == 15
    assert result.elevation_loss_m == 5
    assert result.elevation_min_m == 100
    assert result.elevation_max_m == 115
    assert result.start_point == {"lon": 104.0, "lat": 30.0, "ele": 100.0}
    assert result.end_point == {"lon": 104.002, "lat": 30.0, "ele": 110.0}
    assert result.track_geojson["type"] == "LineString"
    assert result.track_geojson["coordinates"][0] == [104.0, 30.0, 100.0]
    assert result.track_geojson["coordinates"][-1] == [104.002, 30.0, 110.0]
    assert len(result.track_geojson["coordinates"]) >= result.distance_km * 100


def test_parse_gpx_excludes_stationary_rest_from_moving_time() -> None:
    from app.features.routes.parser import parse_track

    content = b"""<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="test">
  <trk><trkseg>
    <trkpt lat="30.000000" lon="104.000000"><ele>100</ele><time>2026-01-01T00:00:00Z</time></trkpt>
    <trkpt lat="30.000000" lon="104.010000"><ele>150</ele><time>2026-01-01T00:10:00Z</time></trkpt>
    <trkpt lat="30.000010" lon="104.010050"><ele>151</ele><time>2026-01-01T00:20:00Z</time></trkpt>
    <trkpt lat="30.000020" lon="104.010100"><ele>152</ele><time>2026-01-01T00:30:00Z</time></trkpt>
    <trkpt lat="30.000000" lon="104.020000"><ele>220</ele><time>2026-01-01T00:40:00Z</time></trkpt>
  </trkseg></trk>
</gpx>
"""

    result = parse_track(content, "gpx")

    assert result.analysis_json["elapsed_time_seconds"] == 2400
    assert 1200 <= result.analysis_json["rest_time_seconds"] <= 1260
    assert 1140 <= result.moving_time_seconds <= 1200


def test_parse_coros_gpx_with_extensions_keeps_time_data() -> None:
    from app.features.routes.parser import parse_track

    content = b"""<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="COROS" xmlns:gpxdata="http://www.cluetrust.com/XML/GPXDATA/1/0">
  <metadata>
    <link href="https://www.coros.com"><text>COROS</text></link>
    <time>2025-01-12T01:07:33Z</time>
  </metadata>
  <trk>
    <name>Ganzi hike</name>
    <type>running</type>
    <trkseg>
      <trkpt lat="30.0260438" lon="101.9603225">
        <ele>2577</ele>
        <time>2025-01-12T01:07:47Z</time>
        <extensions>
          <gpxdata:hr>93</gpxdata:hr>
          <gpxdata:distance>0.00</gpxdata:distance>
          <gpxdata:speed>0.764</gpxdata:speed>
        </extensions>
      </trkpt>
      <trkpt lat="30.0260365" lon="101.9603184">
        <ele>2577</ele>
        <time>2025-01-12T01:07:48Z</time>
        <extensions>
          <gpxdata:hr>93</gpxdata:hr>
          <gpxdata:distance>0.00</gpxdata:distance>
          <gpxdata:speed>0.769</gpxdata:speed>
        </extensions>
      </trkpt>
      <trkpt lat="30.0259726" lon="101.9602565">
        <ele>2577</ele>
        <time>2025-01-12T01:07:54Z</time>
        <extensions>
          <gpxdata:hr>97</gpxdata:hr>
          <gpxdata:distance>15.00</gpxdata:distance>
          <gpxdata:speed>0.953</gpxdata:speed>
        </extensions>
      </trkpt>
    </trkseg>
  </trk>
</gpx>
"""

    result = parse_track(content, "gpx")

    assert result.analysis_json["has_time_data"] is True
    assert result.analysis_json["elapsed_time_seconds"] == 7
    assert result.moving_time_seconds == 7
    assert result.track_geojson["type"] == "LineString"


def test_parse_geojson_linestring_metrics() -> None:
    from app.features.routes.parser import parse_track

    content = json.dumps(
        {
            "type": "LineString",
            "coordinates": [
                [104.0, 30.0, 100],
                [104.001, 30.0, 120],
                [104.002, 30.0, 90],
            ],
        }
    ).encode("utf-8")

    result = parse_track(content, "geojson")

    assert result.distance_km > 0
    assert result.elevation_gain_m == 20
    assert result.elevation_loss_m == 30
    assert result.elevation_min_m == 90
    assert result.elevation_max_m == 120
    assert result.track_geojson["type"] == "LineString"


def test_parse_geojson_multilinestring_metrics() -> None:
    from app.features.routes.parser import parse_track

    content = json.dumps(
        {
            "type": "MultiLineString",
            "coordinates": [
                [[104.0, 30.0, 100], [104.001, 30.0, 110]],
                [[104.001, 30.0, 110], [104.002, 30.0, 120]],
            ],
        }
    ).encode("utf-8")

    result = parse_track(content, "geojson")

    assert result.elevation_gain_m == 20
    assert result.track_geojson["type"] == "LineString"
    assert result.track_geojson["coordinates"][0] == [104.0, 30.0, 100.0]
    assert result.track_geojson["coordinates"][-1] == [104.002, 30.0, 120.0]
    assert len(result.track_geojson["coordinates"]) >= result.distance_km * 100


def test_parse_rejects_track_with_too_few_points() -> None:
    from app.features.routes.parser import TrackParseError, parse_track

    content = json.dumps(
        {"type": "LineString", "coordinates": [[104.0, 30.0, 100]]}
    ).encode("utf-8")

    try:
        parse_track(content, "geojson")
    except TrackParseError as exc:
        assert str(exc) == "TRACK_PARSE_FAILED"
    else:
        raise AssertionError("Expected TrackParseError")


def test_parse_real_flower_kml_sample() -> None:
    from app.features.routes.parser import parse_track

    sample_path = Path(__file__).parents[2] / "flower.kml"
    result = parse_track(sample_path.read_bytes(), "kml")

    assert result.distance_km > 9
    assert result.elevation_gain_m > 800
    assert result.elevation_loss_m > 800
    assert result.elevation_min_m > 0
    assert result.elevation_max_m == 697
    assert result.analysis_json["point_count"] == 7756
    assert result.start_point == {"lon": 114.1864989, "lat": 22.5955095}
    assert result.end_point == {"lon": 114.1702769, "lat": 22.5695503, "ele": 54.0}
    assert result.track_geojson["type"] == "LineString"


def test_parse_kml_reads_gx_track_coordinates() -> None:
    from app.features.routes.parser import parse_track

    content = b"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2">
  <Document>
    <Placemark>
      <gx:Track>
        <when>2026-01-01T00:00:00Z</when><gx:coord>104.0000 30.0000 100</gx:coord>
        <when>2026-01-01T00:01:00Z</when><gx:coord>104.0010 30.0000 110</gx:coord>
        <when>2026-01-01T00:02:00Z</when><gx:coord>104.0020 30.0000 120</gx:coord>
      </gx:Track>
    </Placemark>
  </Document>
</kml>
"""

    result = parse_track(content, "kml")

    assert result.start_point == {"lon": 104.0, "lat": 30.0, "ele": 100.0}
    assert result.end_point == {"lon": 104.002, "lat": 30.0, "ele": 120.0}
    assert result.moving_time_seconds == 120
    assert result.analysis_json["has_time_data"] is True
    assert len(result.track_geojson["coordinates"]) >= 3


def test_parse_kml_reads_gx_track_when_after_coordinates() -> None:
    from app.features.routes.parser import parse_track

    content = b"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2">
  <Document>
    <Placemark>
      <gx:Track>
        <gx:coord>104.0000 30.0000 100</gx:coord>
        <gx:coord>104.0010 30.0000 110</gx:coord>
        <gx:coord>104.0020 30.0000 120</gx:coord>
        <when>2026-01-01T00:00:00Z</when>
        <when>2026-01-01T00:01:00Z</when>
        <when>2026-01-01T00:02:00Z</when>
      </gx:Track>
    </Placemark>
  </Document>
</kml>
"""

    result = parse_track(content, "kml")

    assert result.moving_time_seconds == 120
    assert result.analysis_json["has_time_data"] is True


def test_parse_kml_chooses_source_with_more_track_points() -> None:
    from app.features.routes.parser import parse_track

    content = b"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2">
  <Document>
    <Placemark>
      <LineString>
        <coordinates>104.0,30.0,0 104.1,30.0,0</coordinates>
      </LineString>
      <gx:Track>
        <gx:coord>104.0000 30.0000 100</gx:coord>
        <gx:coord>104.0010 30.0000 110</gx:coord>
        <gx:coord>104.0020 30.0000 120</gx:coord>
      </gx:Track>
    </Placemark>
  </Document>
</kml>
"""

    result = parse_track(content, "kml")

    assert result.distance_km < 1
    assert result.start_point == {"lon": 104.0, "lat": 30.0, "ele": 100.0}
    assert result.end_point == {"lon": 104.002, "lat": 30.0, "ele": 120.0}
    assert len(result.track_geojson["coordinates"]) >= result.distance_km * 100


def test_parse_real_gx_kml_sample_ignores_marker_points() -> None:
    from app.features.routes.parser import parse_track

    sample_path = next(Path(__file__).parents[2].glob("2026-01-02*.kml"))
    result = parse_track(sample_path.read_bytes(), "kml")

    assert result.distance_km > 17
    assert result.analysis_json["point_count"] >= 3238
    assert result.analysis_json["has_time_data"] is True
    assert result.moving_time_seconds is not None
    assert result.track_geojson["type"] == "LineString"


def test_parser_densifies_sparse_track_to_ten_meter_spacing() -> None:
    from app.features.routes.parser import parse_track

    content = json.dumps(
        {
            "type": "LineString",
            "coordinates": [
                [104.0, 30.0, 100],
                [104.02, 30.0, 120],
            ],
        }
    ).encode("utf-8")

    result = parse_track(content, "geojson")

    assert result.distance_km > 1
    assert len(result.track_geojson["coordinates"]) >= result.distance_km * 100
