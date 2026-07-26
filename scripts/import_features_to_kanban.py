#!/usr/bin/env python
"""Import AutoForge-style features.yaml into a Hermes Kanban board.

This is intentionally small and explicit: it validates the feature graph, creates
one Kanban card per feature using idempotency keys, and links dependencies.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None


@dataclass(frozen=True)
class Feature:
    id: str
    title: str
    type: str
    depends_on: list[str]
    acceptance: list[str]
    verification: list[str]


def _load_yaml_text(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if yaml is None:
        raise RuntimeError("PyYAML is required for import_features_to_kanban.py")
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return data


def load_features(project_dir: Path) -> list[Feature]:
    features_path = project_dir / ".hermes" / "autoforge" / "features.yaml"
    data = _load_yaml_text(features_path)
    raw_features = data.get("features")
    if not isinstance(raw_features, list) or not raw_features:
        raise ValueError(f"{features_path} must contain a non-empty 'features' list")

    features: list[Feature] = []
    for index, raw in enumerate(raw_features):
        if not isinstance(raw, dict):
            raise ValueError(f"Feature #{index + 1} must be a mapping")
        fid = str(raw.get("id") or "").strip()
        title = str(raw.get("title") or "").strip()
        if not fid or not title:
            raise ValueError(f"Feature #{index + 1} must have id and title")
        depends_on = [str(x).strip() for x in (raw.get("depends_on") or []) if str(x).strip()]
        acceptance = [str(x).strip() for x in (raw.get("acceptance") or []) if str(x).strip()]
        verification = [str(x).strip() for x in (raw.get("verification") or []) if str(x).strip()]
        features.append(
            Feature(
                id=fid,
                title=title,
                type=str(raw.get("type") or "feature").strip(),
                depends_on=depends_on,
                acceptance=acceptance,
                verification=verification,
            )
        )
    validate_features(features)
    return features


def validate_features(features: list[Feature]) -> None:
    ids = [feature.id for feature in features]
    if len(ids) != len(set(ids)):
        duplicates = sorted({fid for fid in ids if ids.count(fid) > 1})
        raise ValueError(f"duplicate feature ids: {', '.join(duplicates)}")
    id_set = set(ids)
    for feature in features:
        for dependency in feature.depends_on:
            if dependency not in id_set:
                raise ValueError(f"{feature.id} has unknown dependency {dependency}")


def to_git_bash_path(path: Path) -> str:
    resolved = path.resolve()
    text = resolved.as_posix()
    if len(text) >= 3 and text[1:3] == ":/":
        return f"/{text[0].lower()}{text[2:]}"
    return text


def build_task_body(feature: Feature) -> str:
    lines = [f"AutoForge feature id: {feature.id}", f"AutoForge feature type: {feature.type}", ""]
    lines.append("Acceptance:")
    if feature.acceptance:
        lines.extend(f"- {item}" for item in feature.acceptance)
    else:
        lines.append("- Not specified")
    lines.append("")
    lines.append("Verification:")
    if feature.verification:
        lines.extend(f"- {item}" for item in feature.verification)
    else:
        lines.append("- Not specified")
    return "\n".join(lines)


def build_import_plan(
    project_dir: Path,
    board: str,
    board_name: str,
    idempotency_prefix: str,
    workspace: str | None = None,
) -> dict[str, Any]:
    features = load_features(project_dir)
    workspace_value = workspace or f"dir:{to_git_bash_path(project_dir)}"
    tasks = [
        {
            "feature_id": feature.id,
            "title": f"{feature.id}: {feature.title}",
            "type": feature.type,
            "workspace": workspace_value,
            "idempotency_key": f"{idempotency_prefix}-{feature.id}",
            "body": build_task_body(feature),
        }
        for feature in features
    ]
    links = [
        {"parent": dependency, "child": feature.id}
        for feature in features
        for dependency in feature.depends_on
    ]
    return {"board": board, "board_name": board_name, "workspace": workspace_value, "tasks": tasks, "links": links}


def run_command(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, text=True, capture_output=True, check=check)


def ensure_board(board: str, board_name: str, project_dir: Path) -> None:
    default_workdir = to_git_bash_path(project_dir)
    create = run_command(
        [
            "hermes",
            "kanban",
            "boards",
            "create",
            board,
            "--name",
            board_name,
            "--default-workdir",
            default_workdir,
        ],
        check=False,
    )
    if create.returncode != 0 and "already" not in (create.stderr + create.stdout).lower():
        sys.stderr.write(create.stdout + create.stderr)
        raise SystemExit(create.returncode)
    run_command(["hermes", "kanban", "boards", "switch", board])


def create_task(task: dict[str, Any]) -> str:
    cmd = [
        "hermes",
        "kanban",
        "create",
        task["title"],
        "--workspace",
        task["workspace"],
        "--body",
        task["body"],
        "--idempotency-key",
        task["idempotency_key"],
        "--json",
    ]
    completed = run_command(cmd)
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Could not parse kanban create JSON for {task['title']}: {completed.stdout}") from exc
    return str(payload["id"])


def import_to_kanban(project_dir: Path, board: str, board_name: str, idempotency_prefix: str) -> dict[str, Any]:
    plan = build_import_plan(project_dir, board=board, board_name=board_name, idempotency_prefix=idempotency_prefix)
    ensure_board(board, board_name, project_dir)
    task_ids: dict[str, str] = {}
    for task in plan["tasks"]:
        task_ids[task["feature_id"]] = create_task(task)
    linked: list[dict[str, str]] = []
    link_errors: list[dict[str, str]] = []
    for link in plan["links"]:
        parent_id = task_ids[link["parent"]]
        child_id = task_ids[link["child"]]
        completed = run_command(["hermes", "kanban", "link", parent_id, child_id], check=False)
        record = {"parent": link["parent"], "child": link["child"], "parent_task": parent_id, "child_task": child_id}
        if completed.returncode == 0:
            linked.append(record)
        else:
            # Idempotent re-runs may fail on already-existing links; keep going but report it.
            record["error"] = (completed.stderr or completed.stdout).strip()
            link_errors.append(record)
    return {"board": board, "tasks": task_ids, "linked": linked, "link_errors": link_errors}


def mark_kanban_imported(project_dir: Path) -> None:
    approval_path = project_dir / ".hermes" / "autoforge" / "approval.json"
    if not approval_path.exists():
        return
    approval = json.loads(approval_path.read_text(encoding="utf-8"))
    if isinstance(approval, dict):
        approval["kanban_imported"] = True
        approval_path.write_text(json.dumps(approval, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import .hermes/autoforge/features.yaml into Hermes Kanban")
    parser.add_argument("project_dir", help="Project directory containing .hermes/autoforge/features.yaml")
    parser.add_argument("--board", default="autoforge-tiny-notes", help="Kanban board slug")
    parser.add_argument("--name", default="AutoForge Tiny Notes", help="Kanban board display name")
    parser.add_argument("--idempotency-prefix", default=None, help="Prefix for per-feature idempotency keys")
    parser.add_argument("--dry-run", action="store_true", help="Print import plan JSON without calling Hermes")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON result")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    project_dir = Path(args.project_dir)
    prefix = args.idempotency_prefix or args.board
    if args.dry_run:
        plan = build_import_plan(project_dir, board=args.board, board_name=args.name, idempotency_prefix=prefix)
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 0
    result = import_to_kanban(project_dir, board=args.board, board_name=args.name, idempotency_prefix=prefix)
    mark_kanban_imported(project_dir)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Imported {len(result['tasks'])} AutoForge features into board {result['board']}")
        for feature_id, task_id in result["tasks"].items():
            print(f"  {feature_id} -> {task_id}")
        print(f"Links created: {len(result['linked'])}; link warnings: {len(result['link_errors'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
