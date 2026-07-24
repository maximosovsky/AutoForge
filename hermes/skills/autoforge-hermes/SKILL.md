---
name: autoforge-hermes
description: "Use when turning a project idea into a Hermes AutoForge-style product workflow: ask product questions, write .hermes/autoforge spec artifacts, validate features.yaml, import tasks into Hermes Kanban, and only then run builder/reviewer work with evidence gates."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [autoforge, hermes, kanban, autonomous-coding, spec-first, product-workflow]
    related_skills: [hermes-agent, hermes-agent-skill-authoring, test-driven-development, requesting-code-review, lightweight-repo-audit]
---

# AutoForge Hermes Product Workflow

## Overview

This skill turns the AutoForge pattern into a Hermes-native product workflow:

```text
idea → product spec → features.yaml → validation → Hermes Kanban → builders → reviewers → release evidence
```

Use it to prevent code-first drift. The deliverable of the first phase is not application code; it is a verified product specification and a Kanban-ready feature graph that another Hermes worker can execute safely.

This skill is distributed from the repository:

```text
C:/100_star/AutoForge
```

## When to Use

Use this skill when the user asks to:

- create a site, app, prototype, product, or internal tool with an agentic workflow;
- “сделай через AutoForge”, “spec first”, “сначала спецификация”, or “features.yaml → Kanban”;
- create reusable Hermes worker prompts for builders/reviewers;
- translate a product idea into implementation tasks before coding;
- import feature tasks into Hermes Kanban.

Do not use it for tiny one-file edits, emergency fixes, or cases where the user explicitly says to skip the spec/Kanban workflow.

## Product Contract

The default contract is strict:

1. **Ask product questions first** unless the user already supplied enough detail.
2. **Write the AutoForge artifact set** under `.hermes/autoforge/`.
3. **Validate artifacts** before importing or implementing.
4. **Import `features.yaml` into Hermes Kanban** as the durable feature database.
5. **Stop before implementation** and ask for approval unless the user explicitly authorized build work.
6. **Builders work one ready feature at a time** and run all relevant checks.
7. **Reviewers verify independently** and create/block regression tasks when evidence fails.
8. **No implementation before approval.** Do not write application source code during the spec/import phase.

## Phase Workflow

### Phase 0 — Identify the target project

If the user gives a path, use it. If not, create a project folder only after the user confirms the name. For examples inside this repo, use:

```text
examples/<project-slug>/
```

The workflow artifacts live inside the target project, not in a separate notes file.

### Phase 1 — Product interview

Ask a compact set of product questions, preferably all at once:

- project name and one-sentence goal;
- target users;
- primary user action / CTA;
- pages, screens, or routes;
- data model and persistence needs;
- authentication / roles / privacy constraints;
- visual direction or reference sites;
- integrations and external services;
- what counts as done.

If the user already provided enough context, proceed with explicit assumptions instead of asking redundant questions.

### Phase 2 — Write artifacts

Create the full artifact set under `.hermes/autoforge/` using file tools. Do not use shell heredocs for durable content.

### Phase 3 — Validate

Run the repo validator when working inside this AutoForge repo:

```bash
python scripts/check_autoforge_layout.py <project-dir>
```

Fix failures and rerun until it reports `PASS`.

### Phase 4 — Preview and import to Kanban

Preview first:

```bash
python scripts/import_features_to_kanban.py <project-dir> \
  --board autoforge-<project-slug> \
  --name 'AutoForge <Project Name>' \
  --idempotency-prefix autoforge-<project-slug> \
  --dry-run
```

Then import:

```bash
python scripts/import_features_to_kanban.py <project-dir> \
  --board autoforge-<project-slug> \
  --name 'AutoForge <Project Name>' \
  --idempotency-prefix autoforge-<project-slug> \
  --json
```

Check board state:

```bash
hermes kanban list
hermes kanban stats
```

### Phase 5 — Wait for build approval

After Kanban import, report the board, ready task count, blocked/todo count, and next recommended task. Stop unless the user explicitly says to build.

### Phase 6 — Build and review

When approved, start with the first ready infrastructure task. For code behavior, follow TDD. For UI features, use browser verification. For CRUD/data features, verify persistence after refresh and process restart. Mark Kanban tasks complete only with evidence.

## Artifact Layout

Each target project must contain:

```text
.hermes/autoforge/app_spec.md
.hermes/autoforge/features.yaml
.hermes/autoforge/review_policy.md
.hermes/autoforge/worker_prompt.md
.hermes/autoforge/status.json
```

### `app_spec.md`

Minimum sections:

- Project name
- Product goal
- Target users
- Core user journeys
- Pages/screens/routes
- Data model and persistence
- Authentication, privacy, and permissions
- Integrations
- Design direction
- Non-goals
- Success criteria

### `features.yaml`

Use stable IDs and explicit dependencies:

```yaml
features:
  - id: INFRA-001
    title: Verify project skeleton
    type: infrastructure
    depends_on: []
    acceptance:
      - The project has a documented spec and feature list.
      - The implementation directory is clear.
    verification:
      - Run scripts/check_autoforge_layout.py <project-dir>.
      - Confirm PASS.

  - id: F001
    title: Implement the first user-visible feature
    type: feature
    depends_on:
      - INFRA-001
    acceptance:
      - The user can complete the named action.
    verification:
      - Run lint/build/tests for the chosen stack.
      - Verify the flow in browser or API.
```

Rules:

- IDs must be unique.
- Dependencies must reference existing IDs.
- Every task must have acceptance criteria and verification steps.
- Create/list/delete flows should depend in natural order.
- Protected pages depend on auth/access-control tasks.
- Persistence checks are mandatory for CRUD/data features.

### `review_policy.md`

Include gates appropriate to the stack:

- lint / format;
- typecheck where applicable;
- build;
- unit/integration tests;
- browser or API smoke checks;
- persistence after refresh/restart for data features;
- no unexplained mock/in-memory production stores;
- security/access-control review for protected flows;
- git diff review;
- evidence added to Kanban before completion.

### `worker_prompt.md`

Require workers to read the spec, feature list, and review policy; work on exactly one assigned feature; run checks; commit only verified changes if commits are authorized; and block instead of guessing.

### `status.json`

Use this shape:

```json
{
  "status": "complete",
  "version": 1,
  "project": "project-slug",
  "files_written": [
    ".hermes/autoforge/app_spec.md",
    ".hermes/autoforge/features.yaml",
    ".hermes/autoforge/review_policy.md",
    ".hermes/autoforge/worker_prompt.md"
  ],
  "feature_count": 8
}
```

## Kanban Import

Inside `C:/100_star/AutoForge`, use the included importer:

```bash
python scripts/import_features_to_kanban.py <project-dir> \
  --board autoforge-<project-slug> \
  --name 'AutoForge <Project Name>' \
  --idempotency-prefix autoforge-<project-slug> \
  --json
```

The importer:

- loads `.hermes/autoforge/features.yaml`;
- validates unique IDs and dependency references;
- creates one Hermes Kanban card per feature;
- uses idempotency keys for safer re-runs;
- links dependencies in Kanban.

## Builder Worker Prompt

Use this shape when assigning a task to another Hermes worker:

```text
You are an AutoForge-Hermes builder worker.

Project: <absolute path>
Assigned Kanban task: <task id/title>

Read:
- .hermes/autoforge/app_spec.md
- .hermes/autoforge/features.yaml
- .hermes/autoforge/review_policy.md
- .hermes/autoforge/worker_prompt.md

Work only on the assigned feature. Implement the smallest complete change that satisfies its acceptance criteria. Run all applicable gates. Commit only verified changes if commits are authorized. Mark the Kanban task complete only with evidence. If blocked, mark the task blocked with the reason.
```

## Reviewer Worker Prompt

```text
You are an AutoForge-Hermes reviewer.

Review completed Kanban task <task id/title> in <absolute path>. Read the spec, the feature definition, review_policy.md, git diff, and available evidence. Run cheap verification where possible. If correct, comment PASS with evidence. If not, block/reopen with exact failure and reproduction steps.
```

## Common Pitfalls

1. **Coding during the spec phase.** The first deliverable is a verified spec and Kanban graph, not source code.
2. **Vague tasks.** A feature without acceptance and verification cannot be assigned safely.
3. **Missing dependencies.** Encode sequence explicitly; otherwise workers start too early.
4. **Mock success.** For real products, mock/in-memory stores are allowed only when the spec explicitly says prototype-only.
5. **No browser check for UI.** A build passing is not enough for user-visible work.
6. **No restart check for persistence.** CRUD features must survive refresh/restart.
7. **Unbounded agent loops.** Use Kanban tasks and bounded workers, not uncontrolled autonomous sessions.
8. **Forgetting to stop after import.** Unless build approval is explicit, report the Kanban state and wait.

## Verification Checklist

Before reporting the spec/import phase complete:

- [ ] `.hermes/autoforge/app_spec.md` exists and states product goal, users, pages, data, security, design, and success criteria.
- [ ] `.hermes/autoforge/features.yaml` has unique feature IDs.
- [ ] Every dependency points to an existing feature ID.
- [ ] Every feature has acceptance criteria and verification steps.
- [ ] `.hermes/autoforge/review_policy.md` defines completion gates.
- [ ] `.hermes/autoforge/worker_prompt.md` defines builder behavior.
- [ ] `.hermes/autoforge/status.json` has `"status": "complete"`.
- [ ] `python scripts/check_autoforge_layout.py <project-dir>` returns `PASS`.
- [ ] Kanban dry-run shows expected tasks and links.
- [ ] Kanban import succeeds or reports only understood idempotent warnings.
- [ ] No implementation was started before user approval.
