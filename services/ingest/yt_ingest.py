#!/usr/bin/env python3
"""
YouTube ingest (metadata only) for curated channels/playlists.

Reads a CSV of sources (data/channels/*.csv) and fetches the latest N videos
per channel or playlist using the YouTube Data API v3. Writes:
 - NDJSON: one JSON object per line (machine-friendly)
 - Plain text: human-friendly summary (for a quick glance)

Usage:
  python services/ingest/yt_ingest.py \
    --channels data/channels/islamic_kids.csv \
    --out out/yt_videos \
    --limit 100 \
    --api-key $LUMENS_YT_API_KEY

Env:
  LUMENS_YT_API_KEY can be used instead of --api-key.

Notes:
 - This uses only public metadata (no video bytes) and respects quotas.
 - Handles @username, /user/Username, /channel/UC..., playlist URLs where possible.
 - For @handles and custom URLs we fall back to search to resolve the channel.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Tuple
from urllib.parse import urlencode, urlparse, parse_qs
from urllib.request import urlopen, Request


API_BASE = "https://www.googleapis.com/youtube/v3"


def http_get_json(path: str, params: Dict[str, str], api_key: str) -> Dict:
    params = {**params, "key": api_key}
    url = f"{API_BASE}{path}?{urlencode(params)}"
    req = Request(url, headers={"User-Agent": "lumens-ingest/0.1"})
    with urlopen(req, timeout=30) as resp:
        if resp.status != 200:
            raise RuntimeError(f"HTTP {resp.status} for {url}")
        data = resp.read()
        return json.loads(data.decode("utf-8"))


def backoff_sleep(attempt: int) -> None:
    time.sleep(min(5.0, 0.5 * (2 ** attempt)))


def yt_api(path: str, params: Dict[str, str], api_key: str, max_attempts: int = 4) -> Dict:
    for attempt in range(max_attempts):
        try:
            return http_get_json(path, params, api_key)
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            backoff_sleep(attempt)
    raise RuntimeError("Unreachable")


@dataclass
class SourceRow:
    source: str
    source_ref: str
    name: str
    notes: str = ""


YOUTUBE_HOSTS = {"www.youtube.com", "youtube.com", "m.youtube.com", "youtu.be"}


def parse_csv(path: Path) -> List[SourceRow]:
    rows: List[SourceRow] = []
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(SourceRow(
                source=(r.get("source") or "").strip().lower(),
                source_ref=(r.get("source_ref") or "").strip(),
                name=(r.get("name") or "").strip(),
                notes=(r.get("notes") or "").strip(),
            ))
    return rows


def load_env_files(candidates: List[Path]) -> List[Path]:
    """Load simple KEY=VALUE lines from .env-style files without overriding existing env.

    - Ignores blank lines and lines starting with '#'.
    - Trims surrounding single or double quotes in values.
    - Returns list of loaded file paths.
    """
    loaded: List[Path] = []
    for p in candidates:
        try:
            if not p or not p.is_file():
                continue
            with p.open("r", encoding="utf-8") as f:
                for raw in f:
                    line = raw.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    key = k.strip()
                    val = v.strip()
                    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                        val = val[1:-1]
                    if key and key not in os.environ:
                        os.environ[key] = val
            loaded.append(p)
        except Exception:
            # Best-effort loader; ignore parse errors
            continue
    return loaded


def detect_youtube_ref(ref: str) -> Tuple[str, str]:
    """Classify a YouTube reference.

    Returns (kind, value) where kind in {"channel_id","playlist_id","handle","user","video_id","query"}.
    """
    s = ref.strip()
    # Handle pure handle input
    if s.startswith("@") and "/" not in s:
        return ("handle", s)
    # URL forms
    try:
        u = urlparse(s)
        if u.netloc in YOUTUBE_HOSTS:
            # Short youtu.be links are typically videos
            if u.netloc == "youtu.be":
                vid = u.path.lstrip("/")
                if vid:
                    return ("video_id", vid)
            # Query params
            qs = parse_qs(u.query)
            if "list" in qs:
                return ("playlist_id", qs["list"][0])
            if "v" in qs:
                return ("video_id", qs["v"][0])
            # Path-based resolution
            parts = [p for p in u.path.split("/") if p]
            if len(parts) >= 2 and parts[0] == "channel" and parts[1].startswith("UC"):
                return ("channel_id", parts[1])
            if len(parts) >= 2 and parts[0] == "user":
                return ("user", parts[1])
            if len(parts) >= 1 and parts[0].startswith("@"):
                return ("handle", parts[0])
            if len(parts) >= 2 and parts[0] == "c":
                # custom URL; fall back to search
                return ("query", parts[1])
            if len(parts) >= 2 and parts[0] == "playlist":
                # sometimes /playlist?list=... or /playlist/PL...
                pid = parts[1]
                return ("playlist_id", pid)
    except Exception:
        pass
    # Fallback: treat as search query
    return ("query", s)


def resolve_channel_id(kind: str, value: str, api_key: str) -> Optional[str]:
    """Resolve YouTube channel ID from various reference kinds."""
    if kind == "channel_id":
        return value
    if kind == "user":
        resp = yt_api("/channels", {"part": "id", "forUsername": value}, api_key)
        items = resp.get("items", [])
        return items[0]["id"] if items else None
    if kind == "handle":
        q = value.lstrip("@")
        resp = yt_api("/search", {"part": "snippet", "type": "channel", "q": q, "maxResults": 5}, api_key)
        for item in resp.get("items", []):
            cid = item.get("snippet", {}).get("channelId")
            if cid:
                return cid
        return None
    if kind == "query":
        resp = yt_api("/search", {"part": "snippet", "type": "channel", "q": value, "maxResults": 1}, api_key)
        items = resp.get("items", [])
        return items[0]["snippet"]["channelId"] if items else None
    # playlist_id and video_id are not channels
    return None


def iter_channel_videos(channel_id: str, api_key: str, limit: int) -> Iterator[Dict]:
    """Yield latest videos for a channel using search (order=date)."""
    fetched = 0
    page_token: Optional[str] = None
    while fetched < limit:
        page_size = min(50, limit - fetched)
        params = {
            "part": "snippet",
            "channelId": channel_id,
            "order": "date",
            "maxResults": str(page_size),
            "type": "video",
        }
        if page_token:
            params["pageToken"] = page_token
        resp = yt_api("/search", params, api_key)
        for item in resp.get("items", []):
            if item.get("id", {}).get("kind") != "youtube#video":
                continue
            vid = item.get("id", {}).get("videoId")
            sn = item.get("snippet", {})
            yield {
                "source": "youtube",
                "video_id": vid,
                "video_url": f"https://www.youtube.com/watch?v={vid}",
                "title": sn.get("title"),
                "description": sn.get("description"),
                "published_at": sn.get("publishedAt"),
                "channel_id": sn.get("channelId"),
                "channel_title": sn.get("channelTitle"),
                "thumbnails": sn.get("thumbnails", {}),
            }
            fetched += 1
            if fetched >= limit:
                break
        page_token = resp.get("nextPageToken")
        if not page_token or fetched >= limit:
            break


def iter_playlist_videos(playlist_id: str, api_key: str, limit: int) -> Iterator[Dict]:
    """Yield latest videos for a playlist (playlistItems)."""
    fetched = 0
    page_token: Optional[str] = None
    while fetched < limit:
        page_size = min(50, limit - fetched)
        params = {
            "part": "snippet",
            "playlistId": playlist_id,
            "maxResults": str(page_size),
        }
        if page_token:
            params["pageToken"] = page_token
        resp = yt_api("/playlistItems", params, api_key)
        for item in resp.get("items", []):
            sn = item.get("snippet", {})
            rid = sn.get("resourceId", {})
            if rid.get("kind") != "youtube#video":
                continue
            vid = rid.get("videoId")
            yield {
                "source": "youtube",
                "video_id": vid,
                "video_url": f"https://www.youtube.com/watch?v={vid}",
                "title": sn.get("title"),
                "description": sn.get("description"),
                "published_at": sn.get("publishedAt"),
                "channel_id": sn.get("channelId"),
                "channel_title": sn.get("channelTitle"),
                "thumbnails": sn.get("thumbnails", {}),
            }
            fetched += 1
            if fetched >= limit:
                break
        page_token = resp.get("nextPageToken")
        if not page_token or fetched >= limit:
            break


def write_outputs(records: Iterable[Dict], out_prefix: Path) -> Tuple[int, Path, Path]:
    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    ndjson_path = out_prefix.with_suffix(".ndjson")
    text_path = out_prefix.with_suffix(".txt")
    count = 0
    with ndjson_path.open("w", encoding="utf-8") as fj, text_path.open("w", encoding="utf-8") as ft:
        for rec in records:
            fj.write(json.dumps(rec, ensure_ascii=False) + "\n")
            # human friendly summary
            date = rec.get("published_at", "?")
            try:
                date = dt.datetime.fromisoformat(date.replace("Z", "+00:00")).date().isoformat()
            except Exception:
                pass
            title = (rec.get("title") or "").strip().replace("\n", " ")
            ch = rec.get("channel_title", "?")
            url = rec.get("video_url", "")
            desc = (rec.get("description") or "").strip().splitlines()
            desc_first = desc[0] if desc else ""
            ft.write(f"[{date}] {ch} — {title}\n")
            ft.write(f"URL: {url}\n")
            if desc_first:
                ft.write(f"Desc: {desc_first[:240]}\n")
            ft.write("---\n")
            count += 1
    return count, ndjson_path, text_path


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


def _fetch_videos_info(video_ids: List[str], api_key: str) -> Dict[str, Dict]:
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
    details = _fetch_videos_info(ids, api_key)
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
        # Prefer defaultAudioLanguage, fallback to defaultLanguage
        lang = sn.get("defaultAudioLanguage") or sn.get("defaultLanguage")
        if lang and not r.get("language"):
            r["language"] = lang


def main(argv: Optional[List[str]] = None) -> int:
    # Best-effort auto-load of .env from CWD and repo root
    script_path = Path(__file__).resolve()
    repo_root = script_path.parents[2] if len(script_path.parents) >= 3 else Path.cwd()
    load_env_files([Path.cwd() / ".env", repo_root / ".env"])

    ap = argparse.ArgumentParser(description="Ingest latest YouTube videos for curated channels/playlists.")
    ap.add_argument("--channels", default="data/channels/islamic_kids.csv", help="Path to curated channels CSV")
    ap.add_argument("--out", default="out/yt_videos", help="Output prefix (writes .ndjson and .txt)")
    ap.add_argument("--limit", type=int, default=100, help="Max videos per source")
    ap.add_argument("--enrich", dest="enrich", action="store_true", default=True, help="Fetch durations and stats via videos.list (default on)")
    ap.add_argument("--no-enrich", dest="enrich", action="store_false", help="Disable enrichment step to save quota")
    ap.add_argument("--api-key", default=os.getenv("LUMENS_YT_API_KEY"), help="YouTube Data API key (or env LUMENS_YT_API_KEY; .env is auto-loaded if present)")
    args = ap.parse_args(argv)

    if not args.api_key:
        print("ERROR: Provide --api-key or set LUMENS_YT_API_KEY", file=sys.stderr)
        return 2

    src_rows = parse_csv(Path(args.channels))
    if not src_rows:
        print(f"No sources found in {args.channels}", file=sys.stderr)
        return 0

    all_records: List[Dict] = []
    seen_video_ids: set[str] = set()

    for row in src_rows:
        if row.source.lower() != "youtube":
            continue
        kind, value = detect_youtube_ref(row.source_ref)
        print(f"→ {row.name}: {kind} {value}")
        if kind == "playlist_id":
            try:
                for rec in iter_playlist_videos(value, args.api_key, args.limit):
                    if rec["video_id"] in seen_video_ids:
                        continue
                    seen_video_ids.add(rec["video_id"])
                    all_records.append(rec)
            except Exception as e:
                print(f"WARN: playlist {value} failed: {e}")
            continue

        channel_id = resolve_channel_id(kind, value, args.api_key)
        if not channel_id:
            print(f"WARN: could not resolve channel for {row.source_ref}")
            continue
        try:
            for rec in iter_channel_videos(channel_id, args.api_key, args.limit):
                if rec["video_id"] in seen_video_ids:
                    continue
                seen_video_ids.add(rec["video_id"])
                all_records.append(rec)
        except Exception as e:
            print(f"WARN: channel {channel_id} failed: {e}")

    if args.enrich:
        try:
            enrich_records(all_records, args.api_key)
        except Exception as e:
            print(f"WARN: enrichment failed: {e}")

    total, ndjson_path, text_path = write_outputs(all_records, Path(args.out))
    print(f"Wrote {total} records → {ndjson_path} and {text_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
