# M4 — Rules and Scoring

Status: implemented and verified.

## User workflow

Save reviewed structured context containing at least two candidate options, then
open Rules and scoring. Add named criteria and importance weights (0–10), rate
each option (0–10, higher is better), optionally add rules and a stated preferred
option, then Evaluate and save. Blank ratings represent unknown information.
No personal weights or rules are preselected. New criteria start at weight zero
and cannot contribute to a recommendation until a positive weight is entered.

Results show a contribution for each criterion, each rule's condition and whether
it triggered, exclusion status, penalties, the final score, and any preference
conflict. Changing an input hides the old result until reevaluation. Save errors
preserve the entered inputs for retry.

## Deterministic semantics

- Contribution = rating × weight × 10 / sum of all criterion weights.
- Base score is the sum of contributions (0–100).
- A zero-weight criterion contributes zero; its value can still trigger a rule.
- Rule conditions use strict above/below comparisons against a criterion rating.
- Hard rules exclude options regardless of score. Soft rules subtract configured
  points. Final scores are floored at zero.
- Unknown positively weighted ratings and unknown applicable rule conditions
  prevent a recommendation unless the affected option is already definitively
  excluded by a hard rule. Unknown values are never silently scored as zero.
- A complete comparison selects the highest-scoring eligible option. Ties do not
  select an arbitrary winner. All-excluded comparisons return no recommendation.
- A preferred option excluded by a hard rule or differing from the top result
  produces an explicit conflict message.
- Scores are arithmetic outcomes of user-entered assumptions, not calibrated
  confidence percentages or predictions of the owner's behavior.

## Persistence and validation

A non-destructive initialization adds `decision_evaluations`. Typed schemas
validate scores, weights, rule penalties, option and criterion references, and
unique IDs. GET `/api/v1/decisions/{id}/evaluation` returns the current analysis
signature and any saved evaluation. PUT validates, evaluates, and saves.

The saved input includes a fingerprint of its structured context. Changed context
marks old evaluations stale. Writes check the fingerprint again inside a SQLite
write transaction to prevent a concurrent context change from producing a saved
result that appears current. The UI requires a fresh evaluation for changed
context. Old saved data is retained until replaced by an explicit evaluation.

## Verification

- 32 backend tests passed, covering existing M2/M3 behavior, weighted contributions,
  deterministic output, hard overrides, soft penalties, threshold boundaries,
  zero weights, ties, unknown ratings/rules, invalid inputs, persistence across
  application sessions, failed writes, and stale-context rejection.
- Ruff passed.
- Frontend TypeScript check and production build passed.
- Live browser checks passed for the M2/M3 workflow and M4 criterion/rating input,
  a weighted winner, hard exclusion overriding that winner, a soft penalty,
  simulated save failure with input retention, retry, persistence after reload,
  and removal of outdated results when structured context changes.
- Mobile 390 × 844: no horizontal overflow. Desktop 1440 × 1000 and mobile
  screenshots inspected. No browser page errors.
- Screenshots: `docs/verification/m4-mobile.png` and `m4-desktop.png`.

Synthetic test inputs only; no personal test data or database is packaged.
The existing Starlette/httpx test dependency deprecation warning remains.
No AI call, GitHub push, or deployment was performed.

## Next

M5 — AI reasoning integration. Personal model values and durable behavioral rules
remain a separate later milestone; the current settings are per-decision inputs.
