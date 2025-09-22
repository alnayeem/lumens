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
) -> List[Dict[str, Any]]:
    client = _fs_client(project_id)
    from google.cloud.firestore_v1 import FieldFilter  # type: ignore
    from google.cloud import firestore as _fs  # type: ignore

    q = client.collection("content")
    if channel_id:
        q = q.where(filter=FieldFilter("channel_id", "==", channel_id))
    if made_for_kids is not None:
        q = q.where(filter=FieldFilter("made_for_kids", "==", made_for_kids))
    q = q.order_by("published_at", direction=_fs.Query.DESCENDING).limit(limit)
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
) -> JSONResponse:
    project_id = os.getenv("LUMENS_GCP_PROJECT")
    if not project_id:
        return JSONResponse({"error": "Set LUMENS_GCP_PROJECT"}, status_code=400)
    items = _query_content(project_id, limit, channelId, madeForKids)
    return JSONResponse({"items": items})


@app.get("/")
def home(request: Request, limit: int = Query(24, ge=1, le=100)) -> HTMLResponse:
    project_id = os.getenv("LUMENS_GCP_PROJECT")
    if not project_id:
        return HTMLResponse(
            "<h3>Set LUMENS_GCP_PROJECT to your GCP project id</h3>", status_code=500
        )
    items = _query_content(project_id, limit)
    # Prepare display-friendly fields
    for it in items:
        it["thumb"] = (
            it.get("thumbnails", {}).get("medium", {}).get("url")
            or it.get("thumbnails", {}).get("default", {}).get("url")
        )
        vid = it.get("video_id") or it.get("source_item_id")
        it["url"] = it.get("video_url") or (f"https://www.youtube.com/watch?v={vid}" if vid else "#")
    env = _env()
    tpl = env.get_template("index.html")
    html = tpl.render(items=items, title="Latest Videos")
    return HTMLResponse(html)

