from __future__ import annotations

import os
from pathlib import Path
from typing import List


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
            continue
    return loaded

