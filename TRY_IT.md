# Try the AutoForge → Hermes workflow

This repo is now a workflow map plus a packaged Hermes skill. The fastest way to prove the idea works is to validate/install the skill, run a small smoke test, validate the artifact layout, then optionally create a Hermes Kanban board from the sample tasks.

## A. Validate and install the Hermes skill

Validate the packaged skill:

```bash
cd AutoForge
python hermes/scripts/validate-skill.py
```

Install into the active Hermes home:

```bash
bash hermes/scripts/install-local.sh
```

Then start a new Hermes session or run `/reload-skills` before expecting `autoforge-hermes` to be auto-discovered.

## 0. Confirm Hermes can use the intended model

From this repo:

```bash
cd AutoForge
hermes chat -q 'Ответь одним словом: OK' --provider custom:azure-max -m gpt-5.5 --quiet
```

Expected: `OK`.

## 1. Inspect the sample spec artifacts

The sample project lives under:

```text
examples/tiny-notes/.hermes/autoforge/
```

Files:

```text
app_spec.md       Product/spec source of truth
features.yaml     Small feature list with dependencies and verification steps
review_policy.md  Gates before a task can be marked done
worker_prompt.md  Prompt skeleton for a builder worker
status.json       Completion marker for this smoke sample
```

Validate the layout:

```bash
python scripts/check_autoforge_layout.py examples/tiny-notes
```

Expected: `PASS`.

## 2. Import features into a Hermes Kanban board

This proves the AutoForge feature list can be represented in Hermes Kanban. Use the importer so the process is repeatable and not a hand-written sequence of `kanban create` calls.

Preview what will be imported:

```bash
cd AutoForge
python scripts/import_features_to_kanban.py examples/tiny-notes \
  --board autoforge-tiny-notes \
  --name 'AutoForge Tiny Notes' \
  --idempotency-prefix autoforge-tiny \
  --dry-run
```

Import into Kanban:

```bash
python scripts/import_features_to_kanban.py examples/tiny-notes \
  --board autoforge-tiny-notes \
  --name 'AutoForge Tiny Notes' \
  --idempotency-prefix autoforge-tiny \
  --json

hermes kanban list
hermes kanban stats
```

Expected: one board with four cards; `INFRA-001` is ready, and `F001/F002/F003` remain todo until their dependencies are completed.

## 3. Optional: run a one-shot initializer/checker

For a no-risk test, ask Hermes to read the spec and report the next action without editing code:

```bash
hermes chat -q 'Read examples/tiny-notes/.hermes/autoforge/app_spec.md and examples/tiny-notes/.hermes/autoforge/features.yaml. Do not edit files. Reply with the ordered implementation plan and the quality gates.' --provider custom:azure-max -m gpt-5.5 --quiet
```

Expected: Hermes should summarize `INFRA-001 → F001/F002/F003` and mention lint/build/test/browser/persistence gates.

## 4. What a full run would add later

A real Hermes AutoForge implementation would add:

- a reusable `autoforge-hermes` skill;
- a parser/importer that imports `features.yaml` into Kanban automatically (`scripts/import_features_to_kanban.py` provides the first smoke implementation);
- dedicated worker profiles: `autoforge-initializer`, `autoforge-builder`, `autoforge-reviewer`, `autoforge-tester`;
- a dispatcher or cron/kanban loop that runs bounded workers;
- final release/review gates.

For now, this repository validates the spec format, mapping, and Kanban translation path.
