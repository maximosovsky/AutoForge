#!/usr/bin/env python
"""Create a minimal AutoForge-Hermes artifact set for a target project."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "autoforge-project"


def write_new(path: Path, content: str, *, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"refusing to overwrite existing file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def app_spec(name: str, goal: str) -> str:
    return f"""# {name} app spec

## Project name

{name}

## Product goal

{goal}

## Target users

- TODO: describe primary users.

## Core user journeys

- TODO: describe the main user journey.

## Pages/screens/routes

- TODO: list pages, screens, or routes.

## Data model and persistence

- TODO: describe entities and persistence requirements.

## Authentication, privacy, and permissions

- TODO: state whether auth, roles, or private data are in scope.

## Integrations

- TODO: list external services, or state none.

## Design direction

- TODO: describe visual direction and references.

## Non-goals

- TODO: list what should not be built in this pass.

## Success criteria

- The AutoForge artifact set exists and validates.
- Features are importable into Hermes Kanban.
- No implementation starts before approval.
"""


def features_yaml() -> str:
    return """features:
  - id: INFRA-001
    title: Verify project skeleton
    type: infrastructure
    depends_on: []
    acceptance:
      - The project has a documented spec and feature list.
      - The implementation directory is clear.
    verification:
      - Run scripts/check_autoforge_layout.py <project-dir>.
      - Confirm PASS.

  - id: F001
    title: Implement the first approved user-visible feature
    type: feature
    depends_on:
      - INFRA-001
    acceptance:
      - The approved user action can be completed.
    verification:
      - Run lint/build/tests for the chosen stack.
      - Verify the flow in browser or API.
"""


def system_view(name: str) -> str:
    return f"""# {name} system view

## System boundary

TODO: state what is inside this project and what is outside it.

## Main elements

| Element | Role | Owns data? | Notes |
|---|---|---:|---|
| User | TODO | no | Primary actor. |
| User interface | TODO | no | Screens/routes from app_spec.md. |
| Application logic | TODO | no | Backend/API/local logic. |
| Persistent store | TODO | yes | Database/files/local storage as appropriate. |

## Component diagram

```mermaid
flowchart TD
  User[User]
  UI[User interface]
  App[Application logic]
  Store[(Persistent store)]

  User --> UI
  UI --> App
  App --> Store

  classDef actor fill:#eff6ff,stroke:#3b82f6,color:#000
  classDef ui fill:#f5f3ff,stroke:#8b5cf6,color:#000
  classDef logic fill:#ecfeff,stroke:#06b6d4,color:#000
  classDef data fill:#f8fafc,stroke:#94a3b8,color:#000
  class User actor
  class UI ui
  class App logic
  class Store data
```

## Data flow

```mermaid
sequenceDiagram
  participant U as User
  participant UI as User interface
  participant App as Application logic
  participant Store as Persistent store

  U->>UI: performs approved action
  UI->>App: sends request or local event
  App->>Store: reads/writes data
  Store-->>App: result
  App-->>UI: updated state
  UI-->>U: visible feedback
```

## Integration points

- Auth: TODO or none.
- Payments: TODO or none.
- Email: TODO or none.
- Storage: TODO.
- LLM/API: TODO or none.
- Analytics: TODO or none.

## Architectural constraints

- Persistence: TODO.
- Privacy: TODO.
- Security: TODO.
- Deployment: TODO.
- Performance: TODO.
- Offline/real-time: TODO or out of scope.

## Diagram standards

- Use `flowchart TD` or `flowchart LR` for component diagrams.
- Use `-->` for main flows and `-. label .->` for dependencies; never use `==>`.
- Use light pastel `classDef` fills with colored strokes and black text.
- Use Mermaid subgraphs only for real bounded subsystems; keep nesting shallow.
- If emoji are used in Mermaid labels, prefer HTML entities instead of raw Unicode emoji.
"""


def review_policy() -> str:
    return """# Review policy

A task is complete only when all applicable gates pass:

- lint / format check;
- typecheck where applicable;
- build succeeds;
- tests pass;
- UI/API flow is verified with unique test data;
- CRUD data persists after refresh and restart;
- production code has no unexplained mock/in-memory store patterns;
- git diff is reviewed;
- evidence is written to the Kanban task before completion.

Blocked tasks must be marked blocked with a concrete reason instead of being skipped silently.
"""


def worker_prompt() -> str:
    return """# AutoForge-Hermes worker prompt

Read before work:

- .hermes/autoforge/app_spec.md
- .hermes/autoforge/system_view.md
- .hermes/autoforge/features.yaml
- .hermes/autoforge/review_policy.md
- .hermes/autoforge/status.json

Work on exactly one assigned feature. Implement the smallest complete change that satisfies its acceptance criteria. Run all applicable gates. Mark the Kanban task complete only with evidence. If blocked, mark the task blocked with the reason instead of guessing.
"""


def scaffold(project_dir: Path, name: str, goal: str, *, force: bool = False) -> list[str]:
    base = project_dir / ".hermes" / "autoforge"
    files = {
        "app_spec.md": app_spec(name, goal),
        "system_view.md": system_view(name),
        "features.yaml": features_yaml(),
        "review_policy.md": review_policy(),
        "worker_prompt.md": worker_prompt(),
    }
    written: list[str] = []
    for filename, content in files.items():
        path = base / filename
        write_new(path, content, force=force)
        written.append(str(path.relative_to(project_dir).as_posix()))

    status = {
        "status": "complete",
        "version": 1,
        "project": slugify(name),
        "files_written": written + [".hermes/autoforge/status.json"],
        "feature_count": 2,
    }
    status_path = base / "status.json"
    write_new(status_path, json.dumps(status, ensure_ascii=False, indent=2) + "\n", force=force)
    written.append(str(status_path.relative_to(project_dir).as_posix()))
    return written


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create .hermes/autoforge artifacts for a project")
    parser.add_argument("project_dir", help="Target project directory")
    parser.add_argument("--name", required=True, help="Project name")
    parser.add_argument("--goal", default="TODO: describe the product goal.", help="One-sentence product goal")
    parser.add_argument("--force", action="store_true", help="Overwrite existing AutoForge artifact files")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    written = scaffold(Path(args.project_dir), args.name, args.goal, force=args.force)
    print(f"Created {len(written)} AutoForge artifact files in {args.project_dir}")
    for path in written:
        print(f" - {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
