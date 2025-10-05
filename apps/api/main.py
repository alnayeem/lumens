#!/usr/bin/env python3
from __future__ import annotations

import os
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader, select_autoescape


def _fs_client(project_id: str):
    try:
        from google.cloud import firestore  # type: ignore
    except Exception as e:
        raise RuntimeError(
            "google-cloud-firestore is required. Install via `make install-ingest` or `pip install google-cloud-firestore`"
        ) from e
    return firestore.Client(project=project_id)


def _query_content(
    project_id: str,
    limit: int,
    channel_id: Optional[str] = None,
    made_for_kids: Optional[bool] = None,
    language: Optional[str] = None,
    topic: Optional[str] = None,
) -> List[Dict[str, Any]]:
    client = _fs_client(project_id)
    from google.cloud.firestore_v1 import FieldFilter  # type: ignore
    from google.cloud import firestore as _fs  # type: ignore

    q = client.collection("content")
    if channel_id:
        q = q.where(filter=FieldFilter("channel_id", "==", channel_id))
    if made_for_kids is not None:
        q = q.where(filter=FieldFilter("made_for_kids", "==", made_for_kids))
    if language:
        # If requesting English, prefer derived boolean filter to catch mislabels
        if language.lower() == "en":
            q = q.where(filter=FieldFilter("is_english", "==", True))
        else:
            q = q.where(filter=FieldFilter("language", "==", language))
    if topic:
        q = q.where(filter=FieldFilter("topics", "array_contains", topic))
    # Order newest first; if Firestore requires an index and it's missing,
    # fall back to unordered results instead of failing the page.
    try:
        q = q.order_by("published_at", direction=_fs.Query.DESCENDING).limit(limit)
        return [d.to_dict() for d in q.stream()]
    except Exception:
        q = q.limit(limit)
        return [d.to_dict() for d in q.stream()]


def _env() -> Environment:
    templates_dir = os.path.join(os.path.dirname(__file__), "templates")
    return Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=select_autoescape(["html", "xml"]),
    )


app = FastAPI(title="Lumens API (MVP)")


# Mount static assets
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.get("/v1/content")
def get_content(
    limit: int = Query(24, ge=1, le=100),
    channelId: Optional[str] = None,
    madeForKids: Optional[bool] = Query(None),
    language: Optional[str] = Query(None),
    topic: Optional[str] = Query(None),
    cursor: Optional[str] = Query(None, description="Opaque cursor from previous page (published_at)"),
) -> JSONResponse:
    project_id = os.getenv("LUMENS_GCP_PROJECT")
    if not project_id:
        return JSONResponse({"error": "Set LUMENS_GCP_PROJECT"}, status_code=400)
    # Use paged query; fall back to simple if unavailable
    try:
        result = _query_content_paged(project_id, limit, channelId, madeForKids, language, topic, cursor)  # type: ignore[name-defined]
        return JSONResponse(result)
    except Exception:
        items = _query_content(project_id, limit, channelId, madeForKids, language, topic)
        return JSONResponse({"items": _decorate_items(items)})


@app.get("/")
def home(
    request: Request,
    limit: int = Query(24, ge=1, le=100),
    lang: Optional[str] = Query("en"),
) -> HTMLResponse:
    project_id = os.getenv("LUMENS_GCP_PROJECT")
    if not project_id:
        return HTMLResponse(
            "<h3>Set LUMENS_GCP_PROJECT to your GCP project id</h3>", status_code=500
        )
    items = _query_content(project_id, limit, language=lang)
    # Prepare display-friendly fields
    for it in items:
        it["thumb"] = (
            it.get("thumbnails", {}).get("medium", {}).get("url")
            or it.get("thumbnails", {}).get("default", {}).get("url")
        )
        vid = it.get("video_id") or it.get("source_item_id")
        it["url"] = it.get("video_url") or (f"https://www.youtube.com/watch?v={vid}" if vid else "#")
        if vid:
            # Use official YouTube embed with safe, monetization-friendly params
            it["embed"] = (
                f"https://www.youtube.com/embed/{vid}?playsinline=1&rel=0&modestbranding=1&enablejsapi=1"
            )
        else:
            it["embed"] = None

    featured = items[0] if items else None
    env = _env()
    tpl = env.get_template("index.html")
    html = tpl.render(items=items, featured=featured, title="Latest Videos")
    return HTMLResponse(html)


# Curated categories (topic slugs) for clients
CATEGORIES: List[Dict[str, str]] = [
    {"slug": "prophets", "label": "Prophets"},
    {"slug": "duas", "label": "Duas & Supplications"},
    {"slug": "ramadan", "label": "Ramadan"},
    {"slug": "seerah", "label": "Seerah"},
    {"slug": "nasheeds", "label": "Nasheeds"},
]


def _decorate_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Add convenience fields: thumb, url, embed for clients (mobile/web)."""
    out: List[Dict[str, Any]] = []
    for it in items:
        d = dict(it)
        d["thumb"] = (
            d.get("thumbnails", {}).get("medium", {}).get("url")
            or d.get("thumbnails", {}).get("default", {}).get("url")
        )
        vid = d.get("video_id") or d.get("source_item_id")
        d["url"] = d.get("video_url") or (f"https://www.youtube.com/watch?v={vid}" if vid else None)
        d["embed"] = (
            f"https://www.youtube.com/embed/{vid}?playsinline=1&rel=0&modestbranding=1&enablejsapi=1"
            if vid
            else None
        )
        out.append(d)
    return out


def _query_content_paged(
    project_id: str,
    limit: int,
    channel_id: Optional[str] = None,
    made_for_kids: Optional[bool] = None,
    language: Optional[str] = None,
    topic: Optional[str] = None,
    cursor: Optional[str] = None,
) -> Dict[str, Any]:
    client = _fs_client(project_id)
    from google.cloud.firestore_v1 import FieldFilter  # type: ignore
    from google.cloud import firestore as _fs  # type: ignore

    q = client.collection("content")
    if channel_id:
        q = q.where(filter=FieldFilter("channel_id", "==", channel_id))
    if made_for_kids is not None:
        q = q.where(filter=FieldFilter("made_for_kids", "==", made_for_kids))
    if language:
        if language.lower() == "en":
            q = q.where(filter=FieldFilter("is_english", "==", True))
        else:
            q = q.where(filter=FieldFilter("language", "==", language))
    if topic:
        q = q.where(filter=FieldFilter("topics", "array_contains", topic))

    try:
        q = q.order_by("published_at", direction=_fs.Query.DESCENDING)
        page_size = min(100, max(1, int(limit)))
        if cursor:
            q = q.start_after({"published_at": cursor})  # type: ignore[arg-type]
        docs = list(q.limit(page_size + 1).stream())
        items = _decorate_items([d.to_dict() for d in docs[:page_size]])
        next_cursor = None
        if len(docs) > page_size:
            last = docs[page_size - 1].to_dict()
            next_cursor = last.get("published_at")
        # Fallback: if a topic was requested but no items matched (e.g., topics not populated yet),
        # return latest items without topic filter so clients still show content.
        if topic and not items:
            q2 = client.collection("content")
            if channel_id:
                q2 = q2.where(filter=FieldFilter("channel_id", "==", channel_id))
            if made_for_kids is not None:
                q2 = q2.where(filter=FieldFilter("made_for_kids", "==", made_for_kids))
            if language:
                if language.lower() == "en":
                    q2 = q2.where(filter=FieldFilter("is_english", "==", True))
                else:
                    q2 = q2.where(filter=FieldFilter("language", "==", language))
            q2 = q2.order_by("published_at", direction=_fs.Query.DESCENDING)
            if cursor:
                q2 = q2.start_after({"published_at": cursor})  # type: ignore[arg-type]
            docs2 = list(q2.limit(page_size + 1).stream())
            items = _decorate_items([d.to_dict() for d in docs2[:page_size]])
            next_cursor = None
            if len(docs2) > page_size:
                last2 = docs2[page_size - 1].to_dict()
                next_cursor = last2.get("published_at")
        return {"items": items, "nextCursor": next_cursor}
    except Exception:
        docs = list(q.limit(limit).stream())
        return {"items": _decorate_items([d.to_dict() for d in docs]), "nextCursor": None}


@app.get("/v1/categories")
def get_categories() -> JSONResponse:
    return JSONResponse({"items": CATEGORIES})
