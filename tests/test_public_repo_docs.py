import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PublicRepoDocsTests(unittest.TestCase):
    def test_readme_has_public_install_and_guideline_sections(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn('<div align="center">', readme)
        self.assertIn("style=for-the-badge", readme)
        self.assertIn("## 🚀 Quick Start", readme)
        self.assertIn("bash hermes/scripts/install-local.sh", readme)
        self.assertIn("curl -fsSL https://raw.githubusercontent.com/maximosovsky/AutoForge/main/hermes/skills/autoforge-hermes/SKILL.md", readme)
        self.assertIn("## 🏗️ Tech Stack", readme)
        self.assertIn("## 📄 License", readme)
        self.assertNotIn("©", readme)

    def test_public_discovery_and_license_files_exist(self):
        for path in ["LICENSE", "llms.txt", "llms-full.txt", "ARCHITECTURE.md"]:
            self.assertTrue((ROOT / path).exists(), path)
        llms = (ROOT / "llms.txt").read_text(encoding="utf-8")
        full = (ROOT / "llms-full.txt").read_text(encoding="utf-8")
        self.assertIn("# AutoForge Hermes", llms)
        self.assertIn("https://github.com/maximosovsky/AutoForge", llms)
        self.assertIn("hermes/skills/autoforge-hermes/SKILL.md", full)


if __name__ == "__main__":
    unittest.main()
