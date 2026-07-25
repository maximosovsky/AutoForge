# Tiny Notes sample spec

## Project name

Tiny Notes

## Product goal

Tiny Notes is a deliberately small web application used to test the AutoForge → Hermes workflow. A user can create short notes, see them in a list, and verify that notes persist after refresh/restart.

## Target users

- Hermes operators testing the AutoForge artifact contract.
- Builder/reviewer workers that need a tiny ordered feature graph.

## Core user journeys

- Create a note with a title and body.
- See saved notes in a list.
- Delete a note and verify that it stays deleted.

## Pages/screens/routes

- Notes screen with create, list, and delete actions.
- Optional local API endpoints for note CRUD in a full implementation.

## Data model and persistence

- Note: id, title, body, created timestamp.
- Real persistence is required for a full implementation; no in-memory-only store for a production pass.

## Authentication, privacy, and permissions

- Authentication is out of scope for this smoke sample.
- Notes are local test data only.

## Integrations

- No external integrations are required.

## Design direction

- Minimal, readable local app UI; visual polish is not the purpose of this sample.

## Non-goals

- Multi-user collaboration.
- Cloud deployment.
- Rich text editing.

## Technology defaults

- Frontend: minimal HTML/JavaScript or React if a builder chooses to implement it.
- Backend: small local API or static localStorage prototype for the smoke version.
- Database: real persistence required for full implementation; no in-memory-only store for a production pass.

## Success criteria

- Project skeleton exists.
- Feature tasks are represented in Hermes Kanban.
- Builder/reviewer prompts can identify implementation order and quality gates.
- No feature is marked done without evidence.
