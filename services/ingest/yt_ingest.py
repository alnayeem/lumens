#!/usr/bin/env python3
"""
Backwards-compatible CLI entry that delegates to the package CLI.

You can run either of:
  - python services/ingest/yt_ingest.py
  - python -m services.ingest.cli
"""

from services.ingest.cli import main

if __name__ == "__main__":
    raise SystemExit(main())

