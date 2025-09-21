#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Dict, List, Optional

from .lib.env import load_env_files
from .lib.io import parse_csv, write_outputs
from .lib.youtube import (
    detect_youtube_ref,
    resolve_channel_id,
    iter_channel_videos,
    iter_playlist_videos,
)
from .lib.enrich import enrich_records
from .lib.store.firestore_writer import write_firestore_content


def run_ingest(
    channels_csv: Path,
    out_prefix: Path,
    limit: int,
    api_key: str,
    enrich: bool,
    firestore_project: str | None = None,
    firestore_collection: str = "content",
) -> int:
    src_rows = parse_csv(channels_csv)
    if not src_rows:
        print(f"No sources found in {channels_csv}")
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
                for rec in iter_playlist_videos(value, api_key, limit):
                    if rec["video_id"] in seen_video_ids:
                        continue
                    seen_video_ids.add(rec["video_id"])
                    all_records.append(rec)
            except Exception as e:
                print(f"WARN: playlist {value} failed: {e}")
            continue

        channel_id = resolve_channel_id(kind, value, api_key)
        if not channel_id:
            print(f"WARN: could not resolve channel for {row.source_ref}")
            continue
        try:
            for rec in iter_channel_videos(channel_id, api_key, limit):
                if rec["video_id"] in seen_video_ids:
                    continue
                seen_video_ids.add(rec["video_id"])
                all_records.append(rec)
        except Exception as e:
            print(f"WARN: channel {channel_id} failed: {e}")

    if enrich:
        try:
            enrich_records(all_records, api_key)
        except Exception as e:
            print(f"WARN: enrichment failed: {e}")

    total, ndjson_path, text_path = write_outputs(all_records, out_prefix)
    print(f"Wrote {total} records → {ndjson_path} and {text_path}")
    if firestore_project:
        try:
            written = write_firestore_content(all_records, firestore_project, firestore_collection)
            print(f"Stored {written} docs in Firestore project {firestore_project} collection '{firestore_collection}'")
        except Exception as e:
            print(f"WARN: Firestore write skipped/failed: {e}")
    return 0


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
    ap.add_argument("--firestore-project", default=os.getenv("LUMENS_GCP_PROJECT"), help="If set, write output to Firestore Native in this GCP project (requires ADC)")
    ap.add_argument("--firestore-collection", default="content", help="Firestore collection name (default: content)")
    args = ap.parse_args(argv)

    if not args.api_key:
        print("ERROR: Provide --api-key or set LUMENS_YT_API_KEY")
        return 2

    return run_ingest(
        Path(args.channels),
        Path(args.out),
        int(args.limit),
        str(args.api_key),
        bool(args.enrich),
        str(args.firestore_project) if args.firestore_project else None,
        str(args.firestore_collection),
    )


if __name__ == "__main__":
    raise SystemExit(main())
