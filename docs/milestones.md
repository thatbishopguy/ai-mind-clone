# Milestones

## M0 — Foundation

- [x] Define repository structure
- [x] Establish frontend/backend boundary
- [x] Establish configuration strategy
- [x] Add backend health endpoint
- [x] Add frontend starter shell
- [x] Document architectural principles
- [x] Document technology choice
- [ ] Push scaffold to private GitHub repository

Exit criterion: the project has a stable source-control home and a runnable baseline for both frontend and backend.

## M1 — Working UI shell

- [ ] Responsive application layout
- [ ] Persistent primary navigation
- [ ] Dashboard route
- [ ] New Decision route
- [ ] Decisions route
- [ ] Mind Model route
- [ ] Memories route
- [ ] Simulator route
- [ ] Calibration route
- [ ] Settings route
- [ ] New Decision input form
- [ ] Mobile usability review

Exit criterion: the user can open the app and interact with the permanent application shell even though advanced reasoning is not implemented yet.

## M2 — Decision persistence

Create, save, list, and retrieve decision records. Implemented and verified through backend tests, production build, and a live HTTP flow including process restart. Browser acceptance passed on retry using packaged Chromium; see `../M2_STATUS.md`.

## M3 — Structured analysis

Implemented: conservative labeled-field extraction, typed context and candidate options, review/edit workflow, and persistent reviewed analysis. Backend, production build, and browser checks passed. See `../M3_STATUS.md`.

## M4 — Rules and scoring

Implemented and verified: user-configured weighted criteria, hard exclusions, soft penalties, explicit traces, preference conflicts, incomplete/tie handling, and saved evaluations with stale-context checks. See `../M4_STATUS.md`.

## M5 — AI reasoning integration

Implemented provider isolation, strict structured outputs, reviewed suggestions, provenance, deterministic fallback, and failure handling. Offline and simulated browser checks passed; live API validation awaits secure API access. See `../M5_STATUS.md`.

## M6 — Mind Model

Persist values, behavioral rules, traits, exceptions, and contextual modifiers.

## M7 — Memory retrieval

Retrieve relevant prior experiences and memories for a decision.

## M8 — Prior-decision retrieval

Use similar historical decision cases as structured evidence.

## M9 — Calibration

Compare predicted and actual behavior; quantify systematic model error.

## M10 — Scenario simulator

Run counterfactual scenarios without recording them as actual decisions.

## M11 — Analytics

Expose calibration accuracy, recurring conflicts, factor importance, and model drift.

## M12 — Production hardening

Authentication, backups, deployment, observability, security review, and optional desktop packaging.

## M1 implementation note

The working UI shell was implemented locally after M0. GitHub synchronization is intentionally non-blocking; repository authorization can be repaired independently of product development.
