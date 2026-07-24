# AutoForge Hermes Skill

This folder packages the repository as a reusable Hermes skill.

## Skill

```text
hermes/skills/autoforge-hermes/SKILL.md
```

The skill makes Hermes run a spec-first AutoForge-style product workflow:

```text
idea → .hermes/autoforge artifacts → validation → Hermes Kanban → builders/reviewers
```

## Validate

From the repository root:

```bash
python hermes/scripts/validate-skill.py
python -m unittest discover -s tests -q
```

## Install locally

From Git Bash / POSIX shell:

```bash
bash hermes/scripts/install-local.sh
```

By default this installs to:

```text
$HOME/.hermes/skills/software-development/autoforge-hermes
```

Set `HERMES_HOME` to install into a different Hermes profile/home.

After installing, start a new Hermes session or run `/reload-skills` before expecting the new skill to be auto-discovered.
