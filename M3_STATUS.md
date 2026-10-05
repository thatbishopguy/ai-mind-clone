# M3 — Structured Decision Context

Status: implemented and verified.

## Behavior

From a saved decision, open Structured context to create or reopen a draft.
The context contains the original situation, domain, stakes, time pressure,
problem, actors, constraints, reported facts, and unknowns. Candidate options
have stable UUIDs and descriptions. Context and options are validated on the
server and stored separately from the original decision.

This milestone uses conservative deterministic extraction, not AI semantic
analysis. Explicit `Problem:`, `Actor:`, `Fact:`, `Constraint:`, `Unknown:`,
and `Option:` lines are recognized (one item per line). Unlabeled prose is
retained verbatim as the problem if no explicit problem exists. It does not
guess actors, verify claims, or invent options. Warnings explain omissions and
uncertainty. The user can review and edit extracted fields and add/remove
candidate options, then save reviewed context.

Existing reviewed context is returned unchanged when reopened. The original
saved decision is not overwritten. Source situation/domain/stakes/time pressure
cannot be changed via the analysis endpoint. Blank problems, empty list items,
blank option descriptions, and duplicate option IDs are rejected.

## Persistence and endpoints

Schema initialization adds `decision_analyses` with a foreign key to decisions;
existing M2 records remain intact. The JSON payload is validated against typed
Pydantic context, option, and analysis schemas on both write and read.

- POST `/api/v1/decisions/{id}/analysis`: create draft if absent; otherwise reopen.
- GET `/api/v1/decisions/{id}/analysis`: fetch existing analysis or return 404.
- PUT `/api/v1/decisions/{id}/analysis`: save reviewed context and options.

## Verification

- 16 backend tests passed, including M2 regressions, explicit-field extraction,
  ambiguity preservation, stable option IDs, invalid updates, missing records,
  review persistence across app instances, and upgrading an existing M2 database.
- Ruff passed.
- Frontend type check and production build passed.
- Browser workflow passed against live Next.js/FastAPI/SQLite: create, list,
  reopen, reload, structured context, user edits, adding an option, simulated
  save failure/input preservation, retry, and reloading reviewed values.
- Mobile (390 × 844) and desktop (1440 × 1000) screenshots inspected; mobile
  overflow check passed; no browser runtime errors occurred.
- Screenshots in `docs/verification/m3-mobile.png` and `m3-desktop.png`.

Tests use synthetic input and temporary databases. No API key or AI service is
used. The test runner still emits the existing Starlette/httpx deprecation warning.

## Next

M4 — Rules and scoring. M3 does not rank options or predict the owner's choice.
No GitHub push or deployment was performed.
