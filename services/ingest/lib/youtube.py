from __future__ import annotations

import json
import time
from typing import Dict, Iterator, Optional, Tuple
from urllib.parse import urlencode, urlparse, parse_qs
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError


API_BASE = "https://www.googleapis.com/youtube/v3"
YOUTUBE_HOSTS = {"www.youtube.com", "youtube.com", "m.youtube.com", "youtu.be"}


def http_get_json(path: str, params: Dict[str, str], api_key: str) -> Dict:
    params = {**params, "key": api_key}
    url = f"{API_BASE}{path}?{urlencode(params)}"
    req = Request(url, headers={"User-Agent": "lumens-ingest/0.1"})
    try:
        with urlopen(req, timeout=30) as resp:
            data = resp.read()
            if resp.status != 200:
                # Attempt to surface error JSON details even on non-200
                try:
                    detail = json.loads(data.decode("utf-8")).get("error", {}).get("message", "")
                except Exception:
                    detail = (data[:200].decode("utf-8", "ignore") if isinstance(data, (bytes, bytearray)) else str(data))
                raise RuntimeError(f"HTTP {resp.status} for {url} - {detail}")
            return json.loads(data.decode("utf-8"))
    except HTTPError as e:
        # Read error body for YouTube error details
        body = ""
        try:
            body_bytes = e.read()
            body = body_bytes.decode("utf-8", "ignore")
        except Exception:
            pass
        detail = ""
        try:
            ej = json.loads(body)
            err = ej.get("error", {})
            message = err.get("message")
            reason = (err.get("errors", [{}])[0] or {}).get("reason")
            detail = f"{message} (reason: {reason})"
        except Exception:
            detail = body[:200]
        raise RuntimeError(f"HTTP {e.code} for {url} - {detail}") from None
    except URLError as e:
        raise RuntimeError(f"Network error calling {url}: {e}") from None


def backoff_sleep(attempt: int) -> None:
    time.sleep(min(5.0, 0.5 * (2 ** attempt)))


def yt_api(path: str, params: Dict[str, str], api_key: str, max_attempts: int = 4) -> Dict:
    for attempt in range(max_attempts):
        try:
            return http_get_json(path, params, api_key)
        except Exception:
            if attempt == max_attempts - 1:
                raise
            backoff_sleep(attempt)
    raise RuntimeError("Unreachable")


def detect_youtube_ref(ref: str) -> Tuple[str, str]:
    s = ref.strip()
    if s.startswith("@") and "/" not in s:
        return ("handle", s)
    try:
        u = urlparse(s)
        if u.netloc in YOUTUBE_HOSTS:
            if u.netloc == "youtu.be":
                vid = u.path.lstrip("/")
                if vid:
                    return ("video_id", vid)
            qs = parse_qs(u.query)
            if "list" in qs:
                return ("playlist_id", qs["list"][0])
            if "v" in qs:
                return ("video_id", qs["v"][0])
            parts = [p for p in u.path.split("/") if p]
            if len(parts) >= 2 and parts[0] == "channel" and parts[1].startswith("UC"):
                return ("channel_id", parts[1])
            if len(parts) >= 2 and parts[0] == "user":
                return ("user", parts[1])
            if len(parts) >= 1 and parts[0].startswith("@"):
                return ("handle", parts[0])
            if len(parts) >= 2 and parts[0] == "c":
                return ("query", parts[1])
            if len(parts) >= 2 and parts[0] == "playlist":
                pid = parts[1]
                return ("playlist_id", pid)
    except Exception:
        pass
    return ("query", s)


def resolve_channel_id(kind: str, value: str, api_key: str) -> Optional[str]:
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
    return None


def iter_channel_videos(channel_id: str, api_key: str, limit: int) -> Iterator[Dict]:
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
