import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
CHECK = SCRIPTS / "check_autoforge_layout.py"


def write_project(root: Path, *, features: str, app_spec: str | None = None, status: dict | None = None) -> None:
    spec_dir = root / ".hermes" / "autoforge"
    spec_dir.mkdir(parents=True)
    (spec_dir / "app_spec.md").write_text(app_spec or """# Demo

## Project name
Demo

## Product goal
Test.

## Target users
Users.

## Core user journeys
Use it.

## Pages/screens/routes
Home.

## Data model and persistence
Data persists.

## Authentication, privacy, and permissions
None.

## Integrations
None.

## Design direction
Simple.

## Non-goals
None.

## Success criteria
PASS.
""", encoding="utf-8")
    (spec_dir / "system_view.md").write_text("""# Demo system view

## System boundary
Inside/outside.

## Main elements
Elements.

## Component diagram
```mermaid
flowchart TD
  A[A] --> B[B]
  classDef base fill:#ffffff,stroke:#e5e7eb,color:#000
  class A,B base
```

## Data flow
Flow.

## Integration points
Integrations.

## Architectural constraints
Constraints.
""", encoding="utf-8")
    (spec_dir / "features.yaml").write_text(features, encoding="utf-8")
    (spec_dir / "review_policy.md").write_text("# Review policy\n\n- tests pass\n", encoding="utf-8")
    (spec_dir / "worker_prompt.md").write_text("# Worker prompt\n", encoding="utf-8")
    (spec_dir / "design_reference.md").write_text("""# Design reference

Approved visual source: test fixture.

Do not redesign.
Do not simplify visible UI.
""", encoding="utf-8")
    (spec_dir / "visual_parity_checklist.md").write_text("""# Visual parity checklist

- Reference screenshot must be captured.
- Candidate screenshot must be captured.
- Visible differences must be listed.
- User approval is required for deviations.
""", encoding="utf-8")
    (spec_dir / "approval.json").write_text(json.dumps({
        "spec_approved": False,
        "design_reference_approved": False,
        "kanban_imported": False,
        "implementation_allowed": False,
        "approved_by_user": None,
        "approved_at": None,
    }), encoding="utf-8")
    payload = status or {
        "status": "complete",
        "version": 1,
        "project": "demo",
        "files_written": [
            ".hermes/autoforge/app_spec.md",
            ".hermes/autoforge/system_view.md",
            ".hermes/autoforge/design_reference.md",
            ".hermes/autoforge/visual_parity_checklist.md",
            ".hermes/autoforge/features.yaml",
            ".hermes/autoforge/review_policy.md",
            ".hermes/autoforge/worker_prompt.md",
            ".hermes/autoforge/approval.json",
            ".hermes/autoforge/status.json",
        ],
        "feature_count": 1,
    }
    (spec_dir / "status.json").write_text(json.dumps(payload), encoding="utf-8")


class CheckAutoForgeLayoutTests(unittest.TestCase):
    def run_check(self, project: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(CHECK), str(project)], text=True, capture_output=True, check=False)

    def test_rejects_missing_acceptance_and_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            write_project(
                project,
                features="""features:
  - id: F001
    title: Incomplete feature
    type: feature
    depends_on: []
""",
            )
            completed = self.run_check(project)

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("F001 has no acceptance criteria", completed.stdout)
        self.assertIn("F001 has no verification steps", completed.stdout)

    def test_rejects_dependency_cycles(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            write_project(
                project,
                features="""features:
  - id: F001
    title: First
    type: feature
    depends_on:
      - F002
    acceptance:
      - A
    verification:
      - V
  - id: F002
    title: Second
    type: feature
    depends_on:
      - F001
    acceptance:
      - A
    verification:
      - V
""",
                status={
                    "status": "complete",
                    "version": 1,
                    "project": "demo",
                    "files_written": [
                        ".hermes/autoforge/app_spec.md",
                        ".hermes/autoforge/system_view.md",
                        ".hermes/autoforge/design_reference.md",
                        ".hermes/autoforge/visual_parity_checklist.md",
                        ".hermes/autoforge/features.yaml",
                        ".hermes/autoforge/review_policy.md",
                        ".hermes/autoforge/worker_prompt.md",
                        ".hermes/autoforge/approval.json",
                        ".hermes/autoforge/status.json",
                    ],
                    "feature_count": 2,
                },
            )
            completed = self.run_check(project)

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("dependency cycle", completed.stdout)

    def test_rejects_status_feature_count_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            write_project(
                project,
                features="""features:
  - id: F001
    title: Complete feature
    type: feature
    depends_on: []
    acceptance:
      - A
    verification:
      - V
""",
                status={
                    "status": "complete",
                    "files_written": [
                        ".hermes/autoforge/app_spec.md",
                        ".hermes/autoforge/system_view.md",
                        ".hermes/autoforge/design_reference.md",
                        ".hermes/autoforge/visual_parity_checklist.md",
                        ".hermes/autoforge/features.yaml",
                        ".hermes/autoforge/review_policy.md",
                        ".hermes/autoforge/worker_prompt.md",
                        ".hermes/autoforge/approval.json",
                        ".hermes/autoforge/status.json",
                    ],
                    "feature_count": 99,
                },
            )
            completed = self.run_check(project)

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("feature_count 99 does not match 1", completed.stdout)

    def test_app_spec_requires_real_markdown_headings(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            prose_mentions = """# Demo

This prose mentions Project name, Product goal, Target users, Core user journeys,
Pages/screens/routes, Data model and persistence, Authentication, privacy, and permissions,
Integrations, Design direction, Non-goals, and Success criteria, but not as headings.
"""
            write_project(
                project,
                app_spec=prose_mentions,
                features="""features:
  - id: F001
    title: Complete feature
    type: feature
    depends_on: []
    acceptance:
      - A
    verification:
      - V
""",
            )
            completed = self.run_check(project)

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("app_spec.md missing section heading: Project name", completed.stdout)

    def test_rejects_missing_system_view(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            write_project(
                project,
                features="""features:
  - id: F001
    title: Complete feature
    type: feature
    depends_on: []
    acceptance:
      - A
    verification:
      - V
""",
            )
            (project / ".hermes/autoforge/system_view.md").unlink()
            completed = self.run_check(project)

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn(".hermes/autoforge/system_view.md", completed.stdout)

    def test_rejects_system_view_without_mermaid_style_tokens(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            write_project(
                project,
                features="""features:
  - id: F001
    title: Complete feature
    type: feature
    depends_on: []
    acceptance:
      - A
    verification:
      - V
""",
            )
            (project / ".hermes/autoforge/system_view.md").write_text("""# Demo system view

## System boundary
Inside/outside.

## Main elements
Elements.

## Component diagram
```mermaid
flowchart TD
  A[A] ==> B[B]
```

## Data flow
Flow.

## Integration points
Integrations.

## Architectural constraints
Constraints.
""", encoding="utf-8")
            completed = self.run_check(project)

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("system_view.md must use --> arrows, not ==> arrows", completed.stdout)
        self.assertIn("system_view.md Mermaid diagrams must include classDef style tokens", completed.stdout)


if __name__ == "__main__":
    unittest.main()
