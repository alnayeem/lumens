import os
from pathlib import Path

from services.ingest.lib.env import load_env_files
from services.ingest.lib.io import parse_csv, write_outputs


def test_env_loader(tmp_path: Path, monkeypatch):
    # Ensure we don't override existing env
    monkeypatch.setenv("EXISTING", "keep")
    # Ensure loader sets new keys if not already present
    monkeypatch.delenv("LUMENS_YT_API_KEY", raising=False)
    envfile = tmp_path / ".env"
    envfile.write_text("""
# comment
LUMENS_YT_API_KEY="abc123"
EXISTING='nope'
""".strip())

    loaded = load_env_files([envfile])
    assert envfile in loaded
    assert os.getenv("LUMENS_YT_API_KEY") == "abc123"
    assert os.getenv("EXISTING") == "keep"


def test_parse_and_write_outputs(tmp_path: Path):
    csv_path = tmp_path / "channels.csv"
    csv_path.write_text("""
source,source_ref,name,notes
youtube,https://youtu.be/vidid,Example,short
""".lstrip())

    rows = parse_csv(csv_path)
    assert len(rows) == 1
    assert rows[0].source == "youtube"

    out_prefix = tmp_path / "out" / "videos"
    records = [{
        "video_id": "vidid",
        "video_url": "https://www.youtube.com/watch?v=vidid",
        "title": "Test Video",
        "description": "Line1\nLine2",
        "published_at": "2020-01-01T00:00:00Z",
        "channel_title": "Channel",
        "thumbnails": {},
        "duration_seconds": 123,
        "stats": {"views": 10, "likes": 1, "comments": 0},
    }]
    count, ndjson_path, text_path = write_outputs(records, out_prefix)
    assert count == 1
    assert ndjson_path.exists()
    assert text_path.exists()
    assert "Test Video" in text_path.read_text()
