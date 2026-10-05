# M2 Status — Persistent Decisions

Status: **Complete — backend, production build, live HTTP persistence, and browser acceptance verified.**

## Implemented

- Persistent SQLite decisions with UUIDs, situation, domain, stakes, time pressure, and UTC timestamps.
- Versioned create/list/fetch endpoints; validated fields and missing-record responses.
- Deterministic non-destructive schema initialization at API startup.
- Database location configured by DATABASE_URL; connections closed after each operation.
- Existing New Decision form connected to the API with saving, success, and error states.
- Decisions list and saved-detail screen with loading, empty, error, and retry states.
- Saved detail IDs in the URL so a direct reload can reopen the same record.
- Dashboard saved-decision count from the backend.
- Same-origin Next.js API proxy so a phone does not need to contact its own localhost.
- Existing responsive styling retained, with wrapping for saved situation text.
- Frontend package lock added for repeatable dependency installation.

## Verification performed

- Baseline: backend health test passed; frontend TypeScript and production build passed.
- Final backend suite: **13 passed**, covering creation, listing order, fetch, invalid and missing fields, missing records, text preservation, and persistence across separate application instances.
- Python Ruff check: passed.
- Frontend `npm run typecheck`: passed.
- Frontend `npm run build`: passed (Next.js 16.3.6).
- Started the production Next.js server and Uvicorn. Verified create/list/fetch through the Next.js proxy against SQLite, restarted the backend process, then verified the identical saved record could still be listed and fetched.
- Used a temporary verification database; no personal data or test database included in the project.

## Browser acceptance — retry passed

The standard browser download still returned an invalid archive. An alternative
packaged Chromium executable successfully ran the production application under
Playwright. No application code changes were needed.

Verified at a 390 × 844 mobile viewport and a 1440 × 1000 desktop viewport:

- Minimum-length save validation.
- Simulated server failure shows an error and retains the entered situation.
- Retrying the save succeeds; the saved button prevents immediate duplicate submission.
- Saved details preserve situation text and selected domain.
- Reload reopens the same saved record through its URL.
- Decisions list opens the saved details.
- Dashboard displays the persisted decision count.
- Neither checked viewport has horizontal overflow.
- No browser page errors occurred.
- Mobile saved-detail and desktop list screenshots were visually inspected.

Evidence screenshots are in `docs/verification/`. Tests used a temporary database
and synthetic decision text; the database is not included.

A dependency deprecation warning from Starlette's TestClient/httpx integration appeared; the tests passed.

## Next

M3 — Structured Decision Analysis. No scoring, AI integration, editing, or deletion was added in M2.

The source has not been pushed to GitHub or deployed.
