import json
import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import import_features_to_kanban as importer


FEATURES = """
features:
  - id: INFRA-001
    title: Verify project skeleton
    type: infrastructure
    depends_on: []
    acceptance:
      - The project has a documented spec and feature list.
    verification:
      - Confirm PASS.
  - id: F001
    title: Create a note
    type: feature
    depends_on:
      - INFRA-001
    acceptance:
      - User can enter a note title and body.
    verification:
      - Verify through UI or API.
"""


class ImportFeaturesToKanbanTests(unittest.TestCase):
    def test_load_features_preserves_ids_titles_and_dependencies(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec_dir = root / ".hermes" / "autoforge"
            spec_dir.mkdir(parents=True)
            (spec_dir / "features.yaml").write_text(FEATURES, encoding="utf-8")

            features = importer.load_features(root)

        self.assertEqual([f.id for f in features], ["INFRA-001", "F001"])
        self.assertEqual(features[1].title, "Create a note")
        self.assertEqual(features[1].depends_on, ["INFRA-001"])

    def test_unknown_dependency_fails_validation(self):
        features = [
            importer.Feature(id="F001", title="A", type="feature", depends_on=["MISSING"], acceptance=[], verification=[])
        ]
        with self.assertRaises(ValueError) as ctx:
            importer.validate_features(features)
        self.assertIn("unknown dependency", str(ctx.exception))

    def test_build_task_body_contains_acceptance_and_verification(self):
        feature = importer.Feature(
            id="F001",
            title="Create a note",
            type="feature",
            depends_on=["INFRA-001"],
            acceptance=["User can save the note."],
            verification=["Verify through UI."],
        )

        body = importer.build_task_body(feature)

        self.assertIn("AutoForge feature id: F001", body)
        self.assertIn("Acceptance:", body)
        self.assertIn("- User can save the note.", body)
        self.assertIn("Verification:", body)
        self.assertIn("- Verify through UI.", body)

    def test_dry_run_returns_dependency_plan_without_running_hermes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec_dir = root / ".hermes" / "autoforge"
            spec_dir.mkdir(parents=True)
            (spec_dir / "features.yaml").write_text(FEATURES, encoding="utf-8")

            plan = importer.build_import_plan(root, board="demo", board_name="Demo", idempotency_prefix="demo")

        self.assertEqual(plan["board"], "demo")
        self.assertEqual(len(plan["tasks"]), 2)
        self.assertEqual(plan["links"], [{"parent": "INFRA-001", "child": "F001"}])
        self.assertEqual(plan["tasks"][1]["idempotency_key"], "demo-F001")


if __name__ == "__main__":
    unittest.main()
