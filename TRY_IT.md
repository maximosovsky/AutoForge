# Try the AutoForge → Hermes workflow

This repo is currently a workflow map, not a full plugin. The fastest way to prove the idea works is to run a small smoke test: create a tiny spec, validate the artifact layout, then optionally create a Hermes Kanban board from the sample tasks.

## 0. Confirm Hermes can use the intended model

From this repo:

```bash
cd /c/100_star/AutoForge
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

## 2. Optional: create a Hermes Kanban board

This proves the AutoForge feature list can be represented in Hermes Kanban.

```bash
cd /c/100_star/AutoForge
hermes kanban boards create autoforge-tiny-notes --name 'AutoForge Tiny Notes' --default-workdir /c/100_star/AutoForge/examples/tiny-notes || true
hermes kanban boards switch autoforge-tiny-notes
```

Create the infrastructure and feature cards:

```bash
INFRA=$(hermes kanban create 'INFRA-001: verify project skeleton' \
  --workspace dir:/c/100_star/AutoForge/examples/tiny-notes \
  --body 'Verify package/app structure exists; no generated code is required for this smoke test.' \
  --idempotency-key autoforge-tiny-INFRA-001 --json | python -c "import sys,json; print(json.load(sys.stdin)['id'])")

F1=$(hermes kanban create 'F001: create a note' \
  --workspace dir:/c/100_star/AutoForge/examples/tiny-notes \
  --body 'Acceptance: user can create a note with title and body. Verification: unit/browser check in a real app.' \
  --idempotency-key autoforge-tiny-F001 --json | python -c "import sys,json; print(json.load(sys.stdin)['id'])")

F2=$(hermes kanban create 'F002: list notes' \
  --workspace dir:/c/100_star/AutoForge/examples/tiny-notes \
  --body 'Acceptance: user can see saved notes after refresh. Verification includes persistence check.' \
  --idempotency-key autoforge-tiny-F002 --json | python -c "import sys,json; print(json.load(sys.stdin)['id'])")

hermes kanban link "$INFRA" "$F1" || true
hermes kanban link "$INFRA" "$F2" || true
hermes kanban list
```

Expected: one board with three cards; feature cards depend on the infrastructure card.

## 3. Optional: run a one-shot initializer/checker

For a no-risk test, ask Hermes to read the spec and report the next action without editing code:

```bash
hermes chat -q 'Read examples/tiny-notes/.hermes/autoforge/app_spec.md and examples/tiny-notes/.hermes/autoforge/features.yaml. Do not edit files. Reply with the ordered implementation plan and the quality gates.' --provider custom:azure-max -m gpt-5.5 --quiet
```

Expected: Hermes should summarize `INFRA-001 → F001/F002/F003` and mention lint/build/test/browser/persistence gates.

## 4. What a full run would add later

A real Hermes AutoForge implementation would add:

- a reusable `autoforge-hermes` skill;
- a parser that imports `features.yaml` into Kanban automatically;
- dedicated worker profiles: `autoforge-initializer`, `autoforge-builder`, `autoforge-reviewer`, `autoforge-tester`;
- a dispatcher or cron/kanban loop that runs bounded workers;
- final release/review gates.

For now, this repository validates the spec format, mapping, and Kanban translation path.
