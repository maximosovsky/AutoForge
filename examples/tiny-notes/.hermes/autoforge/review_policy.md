# Review policy

A task is complete only when all applicable gates pass:

- lint / format check;
- typecheck where applicable;
- build succeeds;
- tests pass;
- UI/API flow is verified with unique test data;
- CRUD data persists after refresh and restart;
- production code has no unexplained mock/in-memory store patterns;
- git diff is reviewed;
- evidence is written to the Kanban task before completion.

Blocked tasks must be marked blocked with a concrete reason instead of being skipped silently.
