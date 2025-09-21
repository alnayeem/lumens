#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Optional


def _client(project_id: str):
    try:
        from google.cloud import firestore  # type: ignore
    except Exception as e:
        raise RuntimeError(
            "google-cloud-firestore is required. Install via `make install-ingest`"
        ) from e
    return firestore.Client(project=project_id)


def query_content(
    project_id: str,
    channel_id: Optional[str],
    topic: Optional[str],
    limit: int,
    since: Optional[str],
    out: Optional[Path],
) -> int:
    client = _client(project_id)
    q = client.collection("content")
    # Filters (simple demo)
    if channel_id:
        q = q.where("channel_id", "==", channel_id)
    if topic:
        q = q.where("topics", "array_contains", topic)
    if since:
        q = q.where("published_at", ">=", since)
    q = q.order_by("published_at", direction=client.field_path("published_at").DESCENDING)
    q = q.limit(limit)

    docs = list(q.stream())
    items = [d.to_dict() for d in docs]
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8") as f:
            for item in items:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        print(f"Wrote {len(items)} to {out}")
    else:
        for item in items:
            title = (item.get("title") or "").split("\n")[0]
            print(f"{item.get('published_at')} | {item.get('channel_title')} | {title}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Query Firestore content collection")
    ap.add_argument("--project", default=os.getenv("LUMENS_GCP_PROJECT"), help="GCP project id (or env LUMENS_GCP_PROJECT)")
    ap.add_argument("--channel", default=None, help="Filter by channel_id (e.g., yt:UCxxxx...) or leave blank")
    ap.add_argument("--topic", default=None, help="Filter by topic slug if present in records")
    ap.add_argument("--limit", type=int, default=25, help="Max results")
    ap.add_argument("--since", default=None, help="ISO timestamp lower bound for published_at (e.g., 2024-01-01T00:00:00Z)")
    ap.add_argument("--out", default=None, help="Optional output NDJSON path (writes to stdout if omitted)")
    args = ap.parse_args(argv)

    if not args.project:
        print("ERROR: Provide --project or set LUMENS_GCP_PROJECT")
        return 2
    out = Path(args.out) if args.out else None
    return query_content(args.project, args.channel, args.topic, int(args.limit), args.since, out)


if __name__ == "__main__":
    raise SystemExit(main())

