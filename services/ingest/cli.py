#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Dict, List, Optional

from .lib.env import load_env_files
from .lib.io import parse_csv, write_outputs, load_json, save_json
from .lib.youtube import (
    detect_youtube_ref,
    resolve_channel_id,
    iter_channel_videos,
    iter_playlist_videos,
)
from .lib.enrich import enrich_records
from .lib.store.firestore_writer import write_firestore_content
from .lib.resolve import build_channels_map


def run_ingest(
    channels_csv: Path,
    out_prefix: Path,
    limit: int,
    api_key: str,
    enrich: bool,
    firestore_project: str | None = None,
    firestore_collection: str = "content",
    channels_map_path: Path | None = None,
    state_path: Path | None = None,
) -> int:
    src_rows = parse_csv(channels_csv)
    if not src_rows:
        print(f"No sources found in {channels_csv}")
        return 0
    all_records: List[Dict] = []
    seen_video_ids: set[str] = set()
    # Load optional mapping (source_ref/handle -> channel_id)
    channels_map: Dict[str, str] = {}
    if channels_map_path:
        m = load_json(channels_map_path)
        if isinstance(m, dict):
            channels_map = {str(k): str(v) for k, v in m.items()}
    # Load incremental state: {channel_id: last_video_id}
    state: Dict[str, str] = {}
    if state_path:
        s = load_json(state_path)
        if isinstance(s, dict):
            state = {str(k): str(v) for k, v in s.items()}
    # Track new heads to update state after ingest
    new_heads: Dict[str, str] = {}

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

        # Prefer cached mapping
        channel_id = channels_map.get(value) or channels_map.get(row.source_ref)
        if not channel_id:
            channel_id = resolve_channel_id(kind, value, api_key)
        if not channel_id:
            print(f"WARN: could not resolve channel for {row.source_ref}")
            continue
        try:
            fetched_for_channel = 0
            stop_at = state.get(channel_id)
            for rec in iter_channel_videos(channel_id, api_key, limit):
                if rec["video_id"] in seen_video_ids:
                    continue
                # Incremental stop condition: if we hit the last seen video, stop fetching this channel
                if stop_at and rec["video_id"] == stop_at:
                    break
                seen_video_ids.add(rec["video_id"])
                all_records.append(rec)
                fetched_for_channel += 1
                # Record head (first seen) to update state later
                if channel_id not in new_heads:
                    new_heads[channel_id] = rec["video_id"]
            if fetched_for_channel == 0 and stop_at:
                # No new videos; keep existing head
                pass
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
    # Save updated state if requested
    if state_path and new_heads:
        # Merge old state with new heads
        merged = {**state, **new_heads}
        try:
            save_json(merged, state_path)
            print(f"Updated state → {state_path}")
        except Exception as e:
            print(f"WARN: failed to write state file: {e}")
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
    ap.add_argument("--resolve-out", default=None, help="Resolve channels only and write mapping JSON to this path, then exit")
    ap.add_argument("--channels-map", default=None, help="Path to a JSON mapping (source_ref or handle → channel_id) to avoid search calls")
    ap.add_argument("--state", default=None, help="Path to a JSON state file {channel_id: last_video_id} for incremental ingest")
    args = ap.parse_args(argv)

    if not args.api_key:
        print("ERROR: Provide --api-key or set LUMENS_YT_API_KEY")
        return 2

    # Resolve-only mode
    if args.resolve_out:
        rows = parse_csv(Path(args.channels))
        mapping = build_channels_map(rows, str(args.api_key))
        save_json(mapping, Path(args.resolve_out))
        print(f"Resolved {len(mapping)} entries → {args.resolve_out}")
        return 0

    return run_ingest(
        Path(args.channels),
        Path(args.out),
        int(args.limit),
        str(args.api_key),
        bool(args.enrich),
        str(args.firestore_project) if args.firestore_project else None,
        str(args.firestore_collection),
        Path(args.channels_map) if args.channels_map else None,
        Path(args.state) if args.state else None,
    )


if __name__ == "__main__":
    raise SystemExit(main())
