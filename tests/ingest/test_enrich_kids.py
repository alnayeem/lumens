from services.ingest.lib import enrich


def test_enrich_sets_kids_flags(monkeypatch):
    # Prepare a single record
    records = [{"video_id": "VID1"}]

    # Mock details returned by fetch_videos_info
    def _mock_fetch(ids, api_key):
        return {
            "VID1": {
                "contentDetails": {"duration": "PT2M10S"},
                "statistics": {"viewCount": "100"},
                "snippet": {"defaultLanguage": "en"},
                "status": {"madeForKids": True, "selfDeclaredMadeForKids": False},
            }
        }

    monkeypatch.setattr(enrich, "fetch_videos_info", _mock_fetch)

    enrich.enrich_records(records, api_key="dummy")

    rec = records[0]
    assert rec["duration_seconds"] == 130
    assert rec["language"] == "en"
    assert rec["made_for_kids"] is True
    assert rec["self_declared_made_for_kids"] is False

