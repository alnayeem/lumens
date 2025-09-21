from __future__ import annotations

import re
from typing import Dict, Iterator, List, Optional

from .youtube import yt_api


def _chunked(seq: List[str], size: int) -> Iterator[List[str]]:
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


_DUR_RE = re.compile(
    r"^P(?:(?P<days>\d+)D)?(?:T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?)?$"
)


def iso8601_duration_to_seconds(value: str) -> Optional[int]:
    """Parse a subset of ISO-8601 durations like PT1H2M3S or P2DT3M.

    Returns seconds or None if unparsable.
    """
    if not value:
        return None
    m = _DUR_RE.match(value)
    if not m:
        return None
    days = int(m.group("days") or 0)
    hours = int(m.group("hours") or 0)
    minutes = int(m.group("minutes") or 0)
    seconds = int(m.group("seconds") or 0)
    return days * 86400 + hours * 3600 + minutes * 60 + seconds


def fetch_videos_info(video_ids: List[str], api_key: str) -> Dict[str, Dict]:
    """Fetch videos.list for batches of ids; returns map id -> details."""
    out: Dict[str, Dict] = {}
    if not video_ids:
        return out
    for batch in _chunked(video_ids, 50):
        resp = yt_api(
            "/videos",
            {
                "part": "contentDetails,statistics,snippet",
                "id": ",".join(batch),
                "maxResults": "50",
            },
            api_key,
        )
        for item in resp.get("items", []):
            vid = item.get("id")
            if not vid:
                continue
            out[vid] = item
    return out


def enrich_records(records: List[Dict], api_key: str) -> None:
    """Enrich records in-place with duration_seconds, stats, and language."""
    ids = [r.get("video_id") for r in records if r.get("video_id")]
    details = fetch_videos_info(ids, api_key)
    for r in records:
        vid = r.get("video_id")
        info = details.get(vid, {})
        content = info.get("contentDetails", {})
        stats = info.get("statistics", {})
        sn = info.get("snippet", {})
        if content:
            dur = iso8601_duration_to_seconds(content.get("duration"))
            if dur is not None:
                r["duration_seconds"] = dur
        if stats:
            def _to_int(x: Optional[str]) -> Optional[int]:
                try:
                    return int(x) if x is not None else None
                except Exception:
                    return None
            r["stats"] = {
                k: v for k, v in {
                    "views": _to_int(stats.get("viewCount")),
                    "likes": _to_int(stats.get("likeCount")),
                    "comments": _to_int(stats.get("commentCount")),
                }.items() if v is not None
            }
        lang = sn.get("defaultAudioLanguage") or sn.get("defaultLanguage")
        if lang and not r.get("language"):
            r["language"] = lang

