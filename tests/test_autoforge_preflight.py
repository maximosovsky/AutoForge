import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT = ROOT / "scripts" / "autoforge_preflight.py"

FEATURES = """features:
  - id: INFRA-001
    title: Verify skeleton
    type: infrastructure
    depends_on: []
    acceptance:
      - A
    verification:
      - V
  - id: UI-001
    title: Build UI
    type: feature
    depends_on:
      - INFRA-001
    acceptance:
      - A
    verification:
      - V
"""


def write_project(root: Path, approval: dict) -> None:
    spec = root / ".hermes" / "autoforge"
    spec.mkdir(parents=True)
    (spec / "features.yaml").write_text(FEATURES, encoding="utf-8")
    (spec / "approval.json").write_text(json.dumps(approval), encoding="utf-8")


class AutoForgePreflightTests(unittest.TestCase):
    def run_preflight(self, project: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(PREFLIGHT), str(project), *args],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_missing_approval_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / ".hermes/autoforge").mkdir(parents=True)
            (project / ".hermes/autoforge/features.yaml").write_text(FEATURES, encoding="utf-8")
            completed = self.run_preflight(project, "--task", "UI-001", "--require-build-approval")
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("missing", completed.stdout)

    def test_requires_task_id_and_approval_flags_for_build(self):
        approval = {
            "spec_approved": False,
            "design_reference_approved": False,
            "kanban_imported": False,
            "implementation_allowed": False,
        }
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            write_project(project, approval)
            completed = self.run_preflight(project, "--require-build-approval")
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("assigned Kanban/feature task id is required", completed.stdout)
        self.assertIn("spec_approved must be true", completed.stdout)

    def test_dirty_source_before_approval_fails(self):
        approval = {
            "spec_approved": True,
            "design_reference_approved": True,
            "kanban_imported": True,
            "implementation_allowed": False,
        }
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            write_project(project, approval)
            subprocess.run(["git", "init"], cwd=project, capture_output=True, text=True)
            (project / "app.py").write_text("print('illegal')\n", encoding="utf-8")
            completed = self.run_preflight(project, "--task", "UI-001")
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("implementation files changed before approval", completed.stdout)

    def test_passes_when_all_approvals_and_task_exist(self):
        approval = {
            "spec_approved": True,
            "design_reference_approved": True,
            "kanban_imported": True,
            "implementation_allowed": True,
        }
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            write_project(project, approval)
            completed = self.run_preflight(project, "--task", "UI-001", "--require-build-approval")
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("PASS", completed.stdout)


if __name__ == "__main__":
    unittest.main()
