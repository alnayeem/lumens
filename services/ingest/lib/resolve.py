from __future__ import annotations

from typing import Dict, List, Tuple

from .io import SourceRow
from .youtube import detect_youtube_ref, resolve_channel_id


def build_channels_map(rows: List[SourceRow], api_key: str, relevance_language: str | None = None) -> Dict[str, str]:
    """Resolve non-canonical references to canonical channel IDs (yt UCIDs).

    Returns mapping from reference key to channel_id. Keys include the
    detected reference 'value' (e.g., '@handle', custom slug) and the raw
    'source_ref' for convenience.
    """
    m: Dict[str, str] = {}
    for r in rows:
        if r.source.lower() != "youtube":
            continue
        kind, value = detect_youtube_ref(r.source_ref)
        if kind == "channel_id":
            # Already canonical; record both forms
            m[value] = value
            m[r.source_ref] = value
            continue
        if kind == "playlist_id" or kind == "video_id":
            # Not a channel; skip for channel map
            continue
        cid = resolve_channel_id(kind, value, api_key, relevance_language)
        if cid:
            m[value] = cid
            m[r.source_ref] = cid
    return m
