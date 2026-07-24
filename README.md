<div align="center">

# ⚒️ AutoForge Hermes

![Hermes](https://img.shields.io/badge/Hermes-Agent-111827?style=for-the-badge&logo=sparkfun&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Kanban](https://img.shields.io/badge/Hermes-Kanban-7C3AED?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-lightgrey?style=for-the-badge)

**A reusable Hermes skill that turns product ideas into spec-first, Kanban-driven agent workflows.**

</div>

> AutoForge Hermes translates the AutoForge-style loop — idea → spec → feature graph → builders → review gates — into native Hermes Agent primitives: skills, `.hermes/autoforge` artifacts, Hermes Kanban, delegated workers, and evidence-based verification.

<div align="center">

<!-- Preview image placeholder: add a real screenshot/GIF when a public demo exists. -->

<a href="#-quick-start">Quick Start</a> · <a href="#-features">Features</a> · <a href="#-skill-package">Skill Package</a> · <a href="#-tech-stack">Tech Stack</a> · <a href="#-roadmap">Roadmap</a>

</div>

---

## 💡 Concept

AutoForgeAI popularized a useful autonomous-coding pattern: interview the user, write a spec, turn it into a feature database, let coding sessions implement one feature at a time, and require testing/review before progress is marked complete.

Hermes already has the primitives needed for the same workflow: project context, skills, file/terminal/browser tools, Kanban, delegation, cron, session search, and review skills. This repository packages that translation as a reusable Hermes skill named `autoforge-hermes`.

The skill is intentionally spec-first: it asks product questions, writes `.hermes/autoforge/*` artifacts, validates `features.yaml`, imports tasks into Hermes Kanban, and stops before implementation unless the user explicitly approves build work.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| Hermes skill package | Ships `hermes/skills/autoforge-hermes/SKILL.md` with a reusable spec → Kanban → build/review workflow. |
| Public install path | Supports direct `hermes skills install` from the raw GitHub `SKILL.md` URL once the repository is public. |
| Full local install path | Includes `hermes/scripts/install-local.sh` to copy the complete skill folder into `$HERMES_HOME/skills/software-development/`. |
| Spec artifact contract | Defines `.hermes/autoforge/app_spec.md`, `features.yaml`, `review_policy.md`, `worker_prompt.md`, and `status.json`. |
| Kanban importer | Converts `features.yaml` into Hermes Kanban cards with idempotency keys and dependency links. |
| Smoke sample | Includes `examples/tiny-notes` with four ordered features for validation and Kanban import tests. |
| Quality gates | Requires lint/build/tests/browser/API/persistence checks where applicable before a task can be marked done. |
| LLM discovery files | Provides `llms.txt` and `llms-full.txt` for machine-readable project context. |

---

## 🚀 Quick Start

Install only the skill from a public GitHub URL:

```bash
hermes skills install https://raw.githubusercontent.com/maximosovsky/AutoForge/main/hermes/skills/autoforge-hermes/SKILL.md
```

Or install the full package with helper scripts:

```bash
git clone https://github.com/maximosovsky/AutoForge.git
cd AutoForge
python hermes/scripts/validate-skill.py
bash hermes/scripts/install-local.sh
```

Then restart Hermes or run:

```text
/reload-skills
```

<details>
<summary>🧪 Smoke test the sample project</summary>

```bash
python scripts/check_autoforge_layout.py examples/tiny-notes
python scripts/import_features_to_kanban.py examples/tiny-notes \
  --board autoforge-tiny-notes \
  --name 'AutoForge Tiny Notes' \
  --idempotency-prefix autoforge-tiny \
  --dry-run
python -m unittest discover -s tests -q
```

Expected results:

```text
PASS examples\tiny-notes has 4 AutoForge-style features and valid dependencies
Ran 7 tests ... OK
```

</details>

<details>
<summary>⚙️ Install into a custom Hermes home/profile</summary>

```bash
HERMES_HOME=/path/to/hermes/home bash hermes/scripts/install-local.sh
```

Default target:

```text
$HERMES_HOME/skills/software-development/autoforge-hermes
```

</details>

---

## 🧩 Skill Package

| File | Purpose |
|------|---------|
| `hermes/skills/autoforge-hermes/SKILL.md` | Runtime Hermes skill loaded by `/skill autoforge-hermes` or automatic skill matching. |
| `hermes/scripts/validate-skill.py` | Validates frontmatter, required sections, artifact names, and install contract. |
| `hermes/scripts/install-local.sh` | Installs the skill folder into the active Hermes home. |
| `scripts/check_autoforge_layout.py` | Validates a target project's `.hermes/autoforge` artifact layout. |
| `scripts/import_features_to_kanban.py` | Imports `features.yaml` into Hermes Kanban with dependencies. |
| `examples/tiny-notes/.hermes/autoforge/` | Minimal smoke project demonstrating the artifact contract. |

The core workflow:

```text
idea
└── app_spec.md
    └── features.yaml
        ├── validate layout/dependencies
        ├── import to Hermes Kanban
        └── builders/reviewers work one verified task at a time
```

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|------------|
| Agent runtime | [Hermes Agent](https://hermes-agent.nousresearch.com/docs) |
| Workflow package | Hermes `SKILL.md` |
| Task database | Hermes Kanban |
| Validation/import scripts | Python 3.11+ standard library + optional PyYAML |
| Sample format | Markdown, YAML, JSON |
| Distribution | GitHub raw `SKILL.md` or clone + install script |

<details>
<summary>📁 Project Structure</summary>

```text
AutoForge/
├── README.md
├── TRY_IT.md
├── ARCHITECTURE.md
├── llms.txt
├── llms-full.txt
├── LICENSE
├── hermes/
│   ├── README.md
│   ├── scripts/
│   │   ├── install-local.sh
│   │   └── validate-skill.py
│   └── skills/
│       └── autoforge-hermes/
│           ├── README.md
│           └── SKILL.md
├── examples/
│   └── tiny-notes/
│       └── .hermes/autoforge/
│           ├── app_spec.md
│           ├── features.yaml
│           ├── review_policy.md
│           ├── status.json
│           └── worker_prompt.md
├── scripts/
│   ├── check_autoforge_layout.py
│   └── import_features_to_kanban.py
└── tests/
    ├── test_hermes_skill_product.py
    └── test_import_features_to_kanban.py
```

</details>

---

## 🗺️ Roadmap

- [x] Map AutoForge concepts to Hermes primitives.
- [x] Add a smoke `.hermes/autoforge` sample project.
- [x] Validate artifact layout and feature dependencies.
- [x] Import `features.yaml` into Hermes Kanban.
- [x] Package the workflow as a reusable Hermes skill.
- [x] Add public README, install path, license, and LLM discovery files.
- [ ] Add a generated project template command or scaffold script.
- [ ] Add CI for validation and unit tests.
- [ ] Add optional dispatcher examples for bounded builder/reviewer workers.

---

## 🤝 Contributing

Fork → `feature/name` → PR.

Keep the workflow spec-first, avoid copying implementation code from upstream AutoForge, and verify changes with:

```bash
python hermes/scripts/validate-skill.py
python scripts/check_autoforge_layout.py examples/tiny-notes
python -m unittest discover -s tests -q
```

---

## 📄 License

[Maxim Osovsky](https://www.wikidata.org/wiki/Q107189449). Licensed under [MIT](LICENSE).
