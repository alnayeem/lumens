#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from typing import Optional


def wipe_collection(project: str, collection: str, page_size: int = 500) -> int:
    try:
        from google.cloud import firestore  # type: ignore
    except Exception as e:
        print("ERROR: google-cloud-firestore is required. Install via `make install-ingest`.")
        raise

    client = firestore.Client(project=project)
    total_deleted = 0
    last_doc = None
    while True:
        q = client.collection(collection).order_by("__name__").limit(page_size)
        if last_doc is not None:
            q = q.start_after(last_doc)
        docs = list(q.stream())
        if not docs:
            break
        batch = client.batch()
        ops = 0
        for d in docs:
            batch.delete(d.reference)
            ops += 1
        batch.commit()
        total_deleted += ops
        last_doc = docs[-1]
        print(f"Deleted {ops} docs (cumulative={total_deleted})…")
    return total_deleted


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Dangerous: wipe all documents in a Firestore collection (Native mode)")
    ap.add_argument("--project", required=True, help="GCP project id")
    ap.add_argument("--collection", default="content", help="Collection name to wipe (default: content)")
    ap.add_argument("--page-size", type=int, default=500, help="Docs per batch (<=500)")
    ap.add_argument("--yes", action="store_true", help="Proceed without interactive confirmation")
    args = ap.parse_args(argv)

    if not args.yes:
        ans = input(
            f"WARNING: This will delete ALL documents in collection '{args.collection}' in project '{args.project}'.\nType 'DELETE' to confirm: "
        ).strip()
        if ans != "DELETE":
            print("Aborted.")
            return 2

    deleted = wipe_collection(str(args.project), str(args.collection), int(args.page_size))
    print(f"Done. Deleted {deleted} documents from {args.collection} in {args.project}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

