from __future__ import annotations

import csv
import datetime as dt
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


@dataclass
class SourceRow:
    source: str
    source_ref: str
    name: str
    notes: str = ""


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
                date = dt.datetime.fromisoformat(str(date).replace("Z", "+00:00")).date().isoformat()
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
            # include duration/stats if available
            dur = rec.get("duration_seconds")
            stats = rec.get("stats")
            if dur is not None or stats:
                ft.write("Info: ")
                if dur is not None:
                    ft.write(f"duration={dur}s ")
                if stats:
                    views = stats.get("views")
                    likes = stats.get("likes")
                    comments = stats.get("comments")
                    ft.write(f"views={views} likes={likes} comments={comments}")
                ft.write("\n")
            ft.write("---\n")
            count += 1
    return count, ndjson_path, text_path


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as f:
            import json

            return json.load(f)
    except FileNotFoundError:
        return None


def save_json(obj: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    import json

    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
