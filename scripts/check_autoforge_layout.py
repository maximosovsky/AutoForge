import json
import sys
from pathlib import Path

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None

REQUIRED = [
    ".hermes/autoforge/app_spec.md",
    ".hermes/autoforge/features.yaml",
    ".hermes/autoforge/review_policy.md",
    ".hermes/autoforge/worker_prompt.md",
    ".hermes/autoforge/status.json",
]


def load_yaml(path: Path):
    text = path.read_text(encoding="utf-8")
    if yaml is not None:
        return yaml.safe_load(text)
    # Tiny fallback sufficient for this sample: detect feature ids/titles/deps by text.
    features = []
    current = None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- id:"):
            current = {"id": stripped.split(":", 1)[1].strip(), "depends_on": []}
            features.append(current)
        elif current and stripped.startswith("title:"):
            current["title"] = stripped.split(":", 1)[1].strip()
        elif current and stripped.startswith("- ") and "depends_on" in current:
            value = stripped[2:].strip()
            if value.startswith(("INFRA-", "F")):
                current["depends_on"].append(value)
    return {"features": features}


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    missing = [p for p in REQUIRED if not (root / p).exists()]
    if missing:
        print("FAIL missing files:")
        for p in missing:
            print(" -", p)
        return 1

    features_path = root / ".hermes/autoforge/features.yaml"
    data = load_yaml(features_path) or {}
    features = data.get("features") or []
    if not features:
        print("FAIL no features found")
        return 1
    ids = [f.get("id") for f in features]
    if len(ids) != len(set(ids)):
        print("FAIL duplicate feature ids")
        return 1
    id_set = set(ids)
    bad_deps = []
    for f in features:
        for dep in f.get("depends_on") or []:
            if dep not in id_set:
                bad_deps.append((f.get("id"), dep))
    if bad_deps:
        print("FAIL unknown dependencies:")
        for fid, dep in bad_deps:
            print(f" - {fid} depends on {dep}")
        return 1

    status = json.loads((root / ".hermes/autoforge/status.json").read_text(encoding="utf-8"))
    if status.get("status") != "complete":
        print("FAIL status.json is not complete")
        return 1

    print(f"PASS {root} has {len(features)} AutoForge-style features and valid dependencies")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
