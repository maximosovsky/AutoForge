#!/usr/bin/env python
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_NAME = "autoforge-hermes"
SKILL_MD = REPO_ROOT / "hermes" / "skills" / SKILL_NAME / "SKILL.md"
REQUIRED_STRINGS = [
    ".hermes/autoforge/app_spec.md",
    ".hermes/autoforge/features.yaml",
    ".hermes/autoforge/review_policy.md",
    ".hermes/autoforge/worker_prompt.md",
    ".hermes/autoforge/status.json",
    "scripts/import_features_to_kanban.py",
    "## Product Contract",
    "## Phase Workflow",
    "## Kanban Import",
    "## Verification Checklist",
]


def validate_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        raise ValueError("SKILL.md must start with YAML frontmatter")
    try:
        end = text.index("\n---\n", 4)
    except ValueError as exc:
        raise ValueError("SKILL.md frontmatter must close with ---") from exc
    raw = text[4:end]
    meta: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip().strip('"')
    if meta.get("name") != SKILL_NAME:
        raise ValueError(f"frontmatter name must be {SKILL_NAME!r}")
    description = meta.get("description", "")
    if not description:
        raise ValueError("frontmatter description is required")
    if len(description) > 1024:
        raise ValueError("frontmatter description must be <= 1024 chars")
    if not text[end + len("\n---\n") :].strip():
        raise ValueError("SKILL.md body is empty")
    return meta


def validate_content(text: str) -> None:
    missing = [item for item in REQUIRED_STRINGS if item not in text]
    if missing:
        raise ValueError("missing required content: " + ", ".join(missing))
    if not re.search(r"no implementation before (user )?approval", text, re.I):
        raise ValueError("skill must state no implementation before approval")


def main() -> int:
    text = SKILL_MD.read_text(encoding="utf-8")
    validate_frontmatter(text)
    validate_content(text)
    print(f"PASS {SKILL_MD} is a valid {SKILL_NAME} Hermes skill")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        raise SystemExit(1)
