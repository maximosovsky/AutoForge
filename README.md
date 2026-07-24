# AutoForge → Hermes adaptation map

This repository records a compact mapping from the public [`AutoForgeAI/autoforge`](https://github.com/AutoForgeAI/autoforge) architecture to an equivalent Hermes Agent workflow.

`AutoForgeAI/autoforge` is a long-running autonomous coding harness built around Claude Agent SDK / Claude Code CLI. Its core pattern is:

```text
idea → spec → initializer → feature database → coding sessions → testing/review → repeat
```

Hermes already has many matching primitives: skills, project context, profiles, spawned agents, Kanban, browser/file/terminal tools, code-review skills, cron, and durable session search. The practical adaptation is therefore not a direct port of every AutoForge file, but a workflow translation.

## Correspondence table

| AutoForgeAI/autoforge concept | Original role | Hermes equivalent | Adaptation note |
|---|---|---|---|
| Claude Code CLI | Runs the coding agent process. | `hermes chat`, Hermes Desktop, spawned Hermes worker profiles. | Use Hermes as the acting agent runtime instead of Claude Code. |
| Claude Agent SDK | Long-running agent loop and tool calls. | Hermes agent runtime (`run_conversation`, toolsets, profiles). | Hermes supplies model/provider routing, tools, memory, and session state. |
| `/create-spec` command | Interviews user and creates the application spec. | Hermes skill `autoforge-hermes` or a project planning prompt. | Implement as a Hermes skill that asks product-level questions and writes spec artifacts. |
| `.autoforge/prompts/app_spec.txt` | Canonical project specification. | `.hermes/autoforge/app_spec.md` or `planning/spec.md`. | Keep a source-first spec with product goals, tech stack, data model, API/UI, and success criteria. |
| `.autoforge/prompts/initializer_prompt.md` | First-session prompt that turns spec into features. | Hermes initializer prompt / one-shot `hermes chat -q`. | Reads spec and creates Kanban tasks with dependencies. |
| `.spec_status.json` | Signals that spec generation is complete for the UI. | `.hermes/autoforge/status.json` or Kanban metadata. | Used only if a UI or automation needs completion detection. |
| `features.db` | SQLite feature/test database. | Hermes Kanban board SQLite. | Store implementation, review, regression, and blocked tasks as Kanban items. |
| `feature_create_bulk` | Creates all feature test cases. | `hermes kanban create` / `kanban_create`. | Generate tasks in batches from spec; preserve dependencies and priorities. |
| `feature_get_next` | Selects next pending feature. | Kanban dispatcher / `kanban_list` / assigned worker task. | Let dispatcher assign ready tasks to worker profiles. |
| `feature_mark_in_progress` | Claims feature for a coding session. | `kanban_show` + worker claim / heartbeat. | Worker owns one task or a small batch. |
| `feature_mark_passing` | Marks feature complete after verification. | `kanban_complete`. | Only complete after lint/build/tests/browser checks pass. |
| `feature_mark_failing` | Reopens a regression. | `kanban_block` or new bug/regression task linked to original. | Preserve failure evidence and reproduction steps. |
| `feature_skip` | Moves blocked feature out of the way. | `kanban_block` with blocker reason. | Do not silently skip; record external dependency or missing auth. |
| Initializer Agent | First run creates feature DB, structure, git. | `autoforge-initializer` Hermes profile / one-shot worker. | Creates project skeleton, `.hermes/autoforge/*`, Kanban board, first commit. |
| Coding Agent | Implements one feature per session. | `autoforge-builder` Hermes profile. | Uses file/terminal/browser tools; one feature or small independent batch per run. |
| Testing Agent | Regression-tests previously passing features. | `autoforge-tester` Hermes profile. | Runs browser/UI checks, API checks, restart persistence tests, and marks failures. |
| Code review subagent | Reviews code quality, security, maintainability. | Hermes skills `requesting-code-review`, `github-code-review`, `systematic-debugging`. | Review before merge/release and after risky feature batches. |
| Browser verification requirement | Proves user-visible feature works. | Hermes browser/computer-use tools. | Required for UI features; keep screenshots/logs when useful. |
| Mock-data grep | Detects fake/in-memory implementations. | Terminal/search gate in reviewer prompt. | Grep for `mockData`, `fakeData`, `sampleData`, `globalThis`, `devStore`, `TODO.*database`. |
| Server restart persistence test | Catches in-memory stores. | Hermes terminal process + browser/API recheck. | Create unique data, restart server, verify data persists, clean up. |
| `init.sh` | Generated setup script. | `scripts/setup.*` or project-specific runbook. | Keep runnable setup commands and expected ports in repo. |
| Git commits after features | Durable progress checkpoint. | Git commit per completed feature/batch. | Commit only after verification; include task id in message. |
| Web UI progress/Kanban | Monitors feature progress. | Hermes Desktop + Kanban dashboard/status. | Hermes already has project/session UI and can expose Kanban status. |
| Auto-continue between sessions | Keeps building across context windows. | Hermes Kanban dispatcher, cron jobs, spawned workers. | Use bounded workers, not an uncontrolled infinite loop. |
| YOLO mode | Faster mode with weaker verification. | Hermes `--yolo` / approvals off, but keep minimal gates. | Use only for prototypes; never for production claims. |
| Auto-improve mode | Adds one polish feature after completion. | Hermes follow-up Kanban task or cron-improvement job. | Create one explicit improvement task, verify, commit. |
| N8N webhook progress | External notifications. | Hermes gateway / webhook / cron delivery. | Send status to Telegram/Discord/etc. if configured. |

## Proposed Hermes workflow

### 1. Spec phase

A Hermes skill interviews the user and writes:

```text
.hermes/autoforge/app_spec.md
.hermes/autoforge/features.yaml
.hermes/autoforge/review_policy.md
.hermes/autoforge/worker_prompt.md
.hermes/autoforge/status.json
```

The spec phase should ask product questions first, derive technical defaults when the user is non-technical, and avoid starting implementation until the spec is approved.

### 2. Initialization phase

The initializer reads the spec and creates a Kanban board:

```text
Infrastructure tasks
Core feature tasks
UI/browser verification tasks
Security/access-control tasks
Regression tasks
Review/release tasks
```

Every functional task should carry acceptance criteria and verification steps. Infrastructure tasks should verify database connectivity, schema existence, persistence, and absence of mock data before feature work proceeds.

### 3. Build phase

Builder workers take one ready task at a time:

```text
kanban_show → implement → lint/typecheck/build/test → browser/API verification → commit → kanban_complete
```

If blocked, they must write the blocker and stop instead of pretending success.

### 4. Review phase

Reviewer/tester workers independently check completed work:

```text
read diff → run quality gates → browser regression → persistence restart → security checks → approve or reopen
```

The reviewer should create linked regression tasks when it finds failures.

### 5. Release / improve phase

After all required tasks pass, Hermes can run a final release review and optionally create one small `auto-improve` task at a time.

## Minimal quality gates

A Hermes AutoForge-style feature is not complete until all applicable gates pass:

- lint / format / typecheck;
- build succeeds;
- unit/integration tests pass;
- UI feature verified in browser;
- no obvious mock/in-memory data patterns in production code;
- data persists after server restart for CRUD/data features;
- security/access rules are checked for protected routes/API endpoints;
- git diff is reviewed;
- Kanban task is completed with evidence.

## Notes from public search

Public GitHub searches found the original `AutoForgeAI/autoforge` and many forks/renames such as `autocoder`, `autoforge-long-coding`, and `autoforge-coding-agent`, but no clearly maintained public `Hermes` adaptation. Reddit search was blocked by Reddit network security during investigation, so this repository records a local adaptation plan rather than an existing upstream Hermes port.

## Non-goals

- This is not a fork of `AutoForgeAI/autoforge`.
- This repository does not copy Claude Agent SDK implementation code.
- The goal is a Hermes-native workflow mapping that can later become a skill/plugin.
