# Core Operating Rules (finwise)

## 1) Maximize Precision (shortest path to truth)
- **Read before writing:** Check READMEs, map services, entrypoints, env vars, DBs/brokers; confirm assumptions in code.
- **Tests first:** Add or adjust unit + integration tests. **Always implement e2e test cases** to collapse the development cycle and provide immediate feedback on issues.
- **Prove with evidence:** Reproduce; capture logs or stack traces; cite exact lines. No speculative fixes.
- **Schema discipline:** All database tables and columns **must** have proper descriptions (comments) for AI agents to work correctly. Update schema descriptions when adding or modifying tables/columns.

## 2) Safety Rails (non-negotiable)
- **Staging only:** Never touch production unless the task explicitly says so.
- **Never destructive by default:** Migrations must be reversible; take backups **only** when schema or data changes.
- **Small blast radius:** Keep diffs minimal in scope; **use flags or canary only for risky or cross-service changes**.

## 3) Collapse the Cycle (Think → Code → Deploy → Test → Decide)
- **Plan briefly** (3–5 bullets) **only if non-trivial**, then ship the smallest viable change that proves it.
- **E2E test mandatory:** Write and run an e2e test case to validate the full flow. This provides immediate feedback and catches integration issues early.
- **Run tests → run service → read logs/metrics → fix → re-run** only what's affected.
- **Commit when green:** If tests, health, and basic performance pass, commit immediately; otherwise propose a one-command fix and iterate. On success, note "tests OK / health OK".

## Git Discipline (small-team policy)
- **Feature branches:** Work in `feature/<task>`; don't push WIP that isn't green.
- **Green push only:** Iterate locally (or in an unshared `journal/<task>`); push a small, coherent commit **after** tests and health are green.
- **Squash merge:** Merge `feature/<task>` via squash; message `feat|fix(scope): summary` + brief proof (tests OK, health OK). Reverts are one step (`git revert`).

## Code Modularity (2025 best practices)
- **Max 300 lines per file:** Keep each file under 300 lines. If exceeded, modularize following industry standards.
- **Extract logically:** Split by responsibility—separate utilities, types, constants, hooks, services, and components.
- **No over-engineering:** Use simple, clear module boundaries. Avoid premature abstractions or complex patterns.
- **Standard structure:** Follow language/framework conventions (e.g., React: components + hooks + utils; Python: modules + services + models).

## Journaling
- **One journal per project:** Keep a single `JOURNAL.md` (or append to an existing project log). Do **not** create multiple `.md` files.
- **Keep it concise and functional:** Summarize only key reasoning, design decisions, and command references that may help later.
- **No noise:** Skip verbose narrations or redundant commentary. The goal is traceability, not storytelling.
- **No unnecessary docs:** Do not create analysis, status, or guide .md files unless explicitly requested. Use JOURNAL.md only.
