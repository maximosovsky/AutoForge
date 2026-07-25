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
    (spec_dir / "features.yaml").write_text(features, encoding="utf-8")
    (spec_dir / "review_policy.md").write_text("# Review policy\n\n- tests pass\n", encoding="utf-8")
    (spec_dir / "worker_prompt.md").write_text("# Worker prompt\n", encoding="utf-8")
    payload = status or {
        "status": "complete",
        "version": 1,
        "project": "demo",
        "files_written": [
            ".hermes/autoforge/app_spec.md",
            ".hermes/autoforge/features.yaml",
            ".hermes/autoforge/review_policy.md",
            ".hermes/autoforge/worker_prompt.md",
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
                        ".hermes/autoforge/features.yaml",
                        ".hermes/autoforge/review_policy.md",
                        ".hermes/autoforge/worker_prompt.md",
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
                        ".hermes/autoforge/features.yaml",
                        ".hermes/autoforge/review_policy.md",
                        ".hermes/autoforge/worker_prompt.md",
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


if __name__ == "__main__":
    unittest.main()
