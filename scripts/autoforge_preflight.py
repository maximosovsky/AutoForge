#!/usr/bin/env python
"""Fail-closed AutoForge build preflight.

This script is the implementation gate that turns `.hermes/autoforge` from a
folder of documents into a build permission check. Builders should run it before
editing implementation files.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None

AUTOFORGE_DIR = Path(".hermes") / "autoforge"
APPROVAL_FILE = AUTOFORGE_DIR / "approval.json"
FEATURES_FILE = AUTOFORGE_DIR / "features.yaml"
AUTOFORGE_PREFIX = ".hermes/autoforge/"

REQUIRED_APPROVAL_FLAGS = [
    "spec_approved",
    "design_reference_approved",
    "kanban_imported",
    "implementation_allowed",
]


def fail(lines: list[str]) -> int:
    print("FAIL")
    for line in lines:
        print(" -", line)
    return 1


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"missing {path.as_posix()}")
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path.as_posix()}: {exc}")
    if not isinstance(data, dict):
        raise ValueError(f"{path.as_posix()} must contain a JSON object")
    return data


def load_features(project: Path) -> list[dict[str, Any]]:
    path = project / FEATURES_FILE
    text = path.read_text(encoding="utf-8")
    if yaml is None:
        raise ValueError("PyYAML is required for autoforge_preflight.py")
    data = yaml.safe_load(text)
    features = data.get("features") if isinstance(data, dict) else None
    if not isinstance(features, list) or not features:
        raise ValueError("features.yaml must contain a non-empty features list")
    return [feature for feature in features if isinstance(feature, dict)]


def approval_errors(approval: dict[str, Any], *, require_build: bool) -> list[str]:
    errors: list[str] = []
    for flag in REQUIRED_APPROVAL_FLAGS:
        if flag not in approval:
            errors.append(f"approval.json missing {flag}")
        elif not isinstance(approval[flag], bool):
            errors.append(f"approval.json {flag} must be boolean")
    if require_build:
        for flag in REQUIRED_APPROVAL_FLAGS:
            if approval.get(flag) is not True:
                errors.append(f"approval.json {flag} must be true before implementation")
    return errors


def task_errors(features: list[dict[str, Any]], task_id: str | None) -> list[str]:
    if not task_id:
        return ["assigned Kanban/feature task id is required (--task)"]
    ids = {str(feature.get("id") or "") for feature in features}
    if task_id not in ids:
        return [f"task {task_id} is not present in features.yaml"]
    return []


def git_changed_files(project: Path) -> list[str]:
    root_result = subprocess.run(
        ["git", "-C", str(project), "rev-parse", "--show-toplevel"],
        text=True,
        capture_output=True,
        check=False,
    )
    git_root = Path(root_result.stdout.strip()) if root_result.returncode == 0 and root_result.stdout.strip() else project
    completed = subprocess.run(
        ["git", "-C", str(git_root), "status", "--porcelain"],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return []
    try:
        project_rel = project.resolve().relative_to(git_root.resolve()).as_posix()
        if project_rel == ".":
            project_rel = ""
    except ValueError:
        project_rel = ""
    changed: list[str] = []
    for line in completed.stdout.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        path = path.replace("\\", "/")
        if project_rel:
            prefix = project_rel.rstrip("/") + "/"
            if path == project_rel:
                changed.append("")
            elif path.startswith(prefix):
                changed.append(path[len(prefix):])
        else:
            changed.append(path)
    return [path for path in changed if path]


def dirty_source_errors(project: Path, approval: dict[str, Any]) -> list[str]:
    if approval.get("implementation_allowed") is True:
        return []
    illegal = [path for path in git_changed_files(project) if not path.startswith(AUTOFORGE_PREFIX)]
    if not illegal:
        return []
    return [
        "implementation files changed before approval: " + ", ".join(illegal[:20])
    ]


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AutoForge build preflight gate")
    parser.add_argument("project_dir", help="Project directory")
    parser.add_argument("--task", help="Assigned feature/Kanban task id, e.g. UI-001")
    parser.add_argument(
        "--require-build-approval",
        action="store_true",
        help="Require all approval flags to be true (builders should use this)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    project = Path(args.project_dir)
    errors: list[str] = []

    try:
        approval = load_json(project / APPROVAL_FILE)
    except ValueError as exc:
        return fail([str(exc)])

    try:
        features = load_features(project)
    except Exception as exc:
        return fail([str(exc)])

    errors.extend(approval_errors(approval, require_build=args.require_build_approval))
    errors.extend(task_errors(features, args.task))
    errors.extend(dirty_source_errors(project, approval))

    if errors:
        return fail(errors)

    print(f"PASS AutoForge preflight for {project} task {args.task}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
