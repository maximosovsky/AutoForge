import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import scaffold_project


class ScaffoldProjectTests(unittest.TestCase):
    def test_scaffold_creates_valid_autoforge_artifact_set(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "demo-app"
            written = scaffold_project.scaffold(project, "Demo App", "Test the scaffold.")

            self.assertEqual(len(written), 6)
            status = json.loads((project / ".hermes/autoforge/status.json").read_text(encoding="utf-8"))
            self.assertEqual(status["project"], "demo-app")
            self.assertEqual(status["feature_count"], 2)
            self.assertTrue((project / ".hermes/autoforge/system_view.md").exists())

            completed = subprocess.run(
                [sys.executable, str(SCRIPTS / "check_autoforge_layout.py"), str(project)],
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("PASS", completed.stdout)

    def test_scaffold_refuses_to_overwrite_without_force(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "demo-app"
            scaffold_project.scaffold(project, "Demo App", "Test the scaffold.")

            with self.assertRaises(FileExistsError):
                scaffold_project.scaffold(project, "Demo App", "Test the scaffold.")


if __name__ == "__main__":
    unittest.main()
