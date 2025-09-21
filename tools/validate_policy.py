#!/usr/bin/env python3
import json
import sys
import pathlib

try:
    import yaml  # type: ignore
    from jsonschema import validate, Draft202012Validator  # type: ignore
except Exception as e:
    print(f"::error ::Missing dependencies: {e}. Install with: pip install pyyaml jsonschema", file=sys.stderr)
    sys.exit(1)

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "tools" / "policy_schema.json"
POLICIES_DIR = ROOT / "policies"

def load_schema():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def iter_policy_files():
    if not POLICIES_DIR.exists():
        return []
    return [p for p in POLICIES_DIR.rglob("policy.yaml") if p.is_file()]

def main():
    schema = load_schema()
    validator = Draft202012Validator(schema)
    errors_found = False
    files = iter_policy_files()
    if not files:
        print("No policy files found under policies/**/policy.yaml")
        return 0
    for path in files:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
            if errors:
                errors_found = True
                for err in errors:
                    loc = "/".join([str(x) for x in err.path]) or "<root>"
                    print(f"::error file={path}::Validation error at {loc}: {err.message}")
            else:
                print(f"Validated: {path}")
        except Exception as e:
            errors_found = True
            print(f"::error file={path}::Failed to validate: {e}")
    return 1 if errors_found else 0

if __name__ == "__main__":
    sys.exit(main())

