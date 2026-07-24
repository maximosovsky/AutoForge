# Tiny Notes sample spec

## Overview

Tiny Notes is a deliberately small web application used to test the AutoForge → Hermes workflow. A user can create short notes, see them in a list, and verify that notes persist after refresh/restart.

## Technology defaults

- Frontend: minimal HTML/JavaScript or React if a builder chooses to implement it.
- Backend: small local API or static localStorage prototype for the smoke version.
- Database: real persistence required for full implementation; no in-memory-only store for a production pass.

## Success criteria

- Project skeleton exists.
- Feature tasks are represented in Hermes Kanban.
- Builder/reviewer prompts can identify implementation order and quality gates.
- No feature is marked done without evidence.
