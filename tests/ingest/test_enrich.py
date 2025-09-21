from services.ingest.lib.enrich import iso8601_duration_to_seconds


def test_duration_parsing_basic():
    assert iso8601_duration_to_seconds("PT1H2M3S") == 3723
    assert iso8601_duration_to_seconds("PT15M") == 900
    assert iso8601_duration_to_seconds("PT0S") == 0


def test_duration_with_days():
    # 1 day + 1 hour = 86400 + 3600 = 90000
    assert iso8601_duration_to_seconds("P1DT1H") == 90000


def test_duration_invalid():
    assert iso8601_duration_to_seconds("") is None
    assert iso8601_duration_to_seconds("INVALID") is None

