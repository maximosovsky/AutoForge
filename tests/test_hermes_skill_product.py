import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "hermes" / "skills" / "autoforge-hermes"
SKILL_MD = SKILL_DIR / "SKILL.md"
INSTALL_SCRIPT = ROOT / "hermes" / "scripts" / "install-local.sh"
VALIDATE_SCRIPT = ROOT / "hermes" / "scripts" / "validate-skill.py"


def _frontmatter(text: str) -> dict[str, str]:
    assert text.startswith("---\n")
    end = text.index("\n---\n", 4)
    raw = text[4:end]
    data: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip().strip('"')
    return data


class HermesSkillProductTests(unittest.TestCase):
    def test_skill_package_has_valid_frontmatter_and_product_sections(self):
        text = SKILL_MD.read_text(encoding="utf-8")
        meta = _frontmatter(text)

        self.assertEqual(meta["name"], "autoforge-hermes")
        self.assertTrue(meta["description"].startswith("Use when"))
        self.assertLessEqual(len(meta["description"]), 1024)
        for section in [
            "## Product Contract",
            "## Phase Workflow",
            "## Artifact Layout",
            "## Kanban Import",
            "## Verification Checklist",
        ]:
            self.assertIn(section, text)

    def test_skill_documents_required_autoforge_artifacts_and_no_code_before_approval(self):
        text = SKILL_MD.read_text(encoding="utf-8")
        for artifact in [
            ".hermes/autoforge/app_spec.md",
            ".hermes/autoforge/features.yaml",
            ".hermes/autoforge/review_policy.md",
            ".hermes/autoforge/worker_prompt.md",
            ".hermes/autoforge/status.json",
        ]:
            self.assertIn(artifact, text)
        self.assertIn('"files_written"', text)
        self.assertRegex(text, re.compile(r"no implementation before (user )?approval", re.I))
        self.assertIn("scripts/import_features_to_kanban.py", text)

    def test_install_and_validation_scripts_are_packaged(self):
        install = INSTALL_SCRIPT.read_text(encoding="utf-8")
        validator = VALIDATE_SCRIPT.read_text(encoding="utf-8")

        self.assertIn("autoforge-hermes", install)
        self.assertIn("HERMES_HOME", install)
        self.assertIn("SKILL.md", install)
        self.assertIn("validate_frontmatter", validator)
        self.assertIn("autoforge-hermes", validator)


if __name__ == "__main__":
    unittest.main()
