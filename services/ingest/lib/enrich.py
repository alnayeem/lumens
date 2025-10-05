from __future__ import annotations

import re
from typing import Dict, Iterator, List, Optional, Tuple

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
                "part": "contentDetails,statistics,snippet,status",
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
    """Enrich records in-place with duration_seconds, stats, language, and kids flags."""
    ids = [r.get("video_id") for r in records if r.get("video_id")]
    details = fetch_videos_info(ids, api_key)
    for r in records:
        vid = r.get("video_id")
        info = details.get(vid, {})
        content = info.get("contentDetails", {})
        stats = info.get("statistics", {})
        sn = info.get("snippet", {})
        status = info.get("status", {})
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
        # Normalize language: store root (e.g., 'en') in 'language' and full tag in 'language_full'
        if lang:
            try:
                norm = str(lang).strip().lower().replace("_", "-")
                root = norm.split("-", 1)[0]
            except Exception:
                norm = str(lang)
                root = norm
            if not r.get("language"):
                r["language"] = root
            if not r.get("language_full"):
                r["language_full"] = norm

        # Lightweight text-based language hint from title + description
        title = (sn.get("title") or "").strip()
        desc = (sn.get("description") or "").strip()
        text_lang, text_conf = _detect_text_language(f"{title}\n{desc}")
        if text_lang:
            r.setdefault("text_language", text_lang)
        if text_conf is not None:
            r.setdefault("text_lang_conf", text_conf)

        # Derived boolean for easy filtering in Firestore queries
        # Mark as English if either explicit language root is 'en' or text hint is 'en' with reasonable confidence
        if "is_english" not in r:
            r["is_english"] = (r.get("language") == "en") or (text_lang == "en" and (text_conf or 0.0) >= 0.7)
        # Kids flags (if present in status)
        if isinstance(status, dict):
            if "madeForKids" in status:
                r["made_for_kids"] = bool(status.get("madeForKids"))
            if "selfDeclaredMadeForKids" in status:
                r["self_declared_made_for_kids"] = bool(status.get("selfDeclaredMadeForKids"))


def _detect_text_language(text: str) -> Tuple[Optional[str], Optional[float]]:
    """Detect language of provided text via langdetect; returns (lang, confidence).

    - Uses title + description as a proxy when audio language is mislabeled.
    - Returns (None, None) if detection is not possible.
    """
    try:
        # Lazy import to avoid mandatory dep at import time
        from langdetect import detect_langs  # type: ignore
    except Exception:
        return None, None
    try:
        cleaned = (text or "").strip()
        if not cleaned or len(cleaned) < 20:
            return None, None
        # detect_langs returns list like ['en:0.99','fr:0.01']
        langs = detect_langs(cleaned)
        if not langs:
            return None, None
        best = max(langs, key=lambda l: l.prob)
        # langdetect returns e.g., 'en'
        return getattr(best, 'lang', None), float(getattr(best, 'prob', 0.0))
    except Exception:
        return None, None
