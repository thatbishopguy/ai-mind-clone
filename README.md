# AI Mind Clone

AI Mind Clone is a modular decision-modeling application. The first product surface is the Decision Engine: a system that captures a situation, generates and evaluates options, applies explicit rules and values, retrieves relevant memories, and records predictions for later calibration.

## Current state

**Milestone M5 — AI Suggestions (live API validation pending)**

The app saves decision context in SQLite, lists saved decisions, and reopens their details. Backend tests, type checking, the production build, and a live HTTP persistence check passed. Browser acceptance also passed on retry; see `M2_STATUS.md`. M3 adds conservative context extraction and an editable review workflow; see `M3_STATUS.md`. M4 adds user-configured scoring and rules; see `M4_STATUS.md`. M5 implements AI suggestions for review; offline and simulated browser checks passed. Live API validation requires access; see `M5_STATUS.md`.

## Repository layout

```text
ai-mind-clone/
├── frontend/               # Next.js + TypeScript application
├── backend/                # FastAPI/Python services
│   └── app/
│       ├── api/            # HTTP endpoints
│       ├── core/           # configuration
│       ├── decision_engine/# deterministic decision logic
│       ├── memory/         # memory/retrieval layer
│       └── models/         # domain/data models
├── docs/                   # architecture and development decisions
└── .env.example
```

## Local development

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Backend health check: `http://localhost:8000/api/v1/health`

### Frontend

```bash
cd frontend
npm ci
npm run dev
```

Frontend: `http://localhost:3000`

## Development principles

1. The LLM is a component, not the entire Decision Engine.
2. Explicit rules, scoring, memory retrieval, and AI reasoning remain separable modules.
3. The system records predictions and actual outcomes so it can be calibrated empirically.
4. User-facing structure should exist early, even while intelligence is progressively implemented.
5. Model behavior must be inspectable: recommendations should expose factors, assumptions, conflicts, and confidence.

## Current UI

The existing responsive navigation and New Decision workspace now support Save Decision, success/error states, a Decisions list, and saved details. Opening a saved decision places its ID in the URL for reload. The dashboard reads the saved count from the API.

## Next milestone

Live M5 validation, then **M6 — Mind Model**.

## Persistence and configuration

The backend initializes `backend/data/ai_mind_clone.db` when started from `backend/`.
Override `DATABASE_URL` in `backend/.env` or the process environment. Use
`sqlite:////absolute/path/decisions.db` for an absolute location. Existing records
are retained on restart; database files and sidecars are excluded from source.

Browser requests use `/api/v1/decisions` on the frontend origin. Next.js proxies
them to `http://127.0.0.1:8000` by default. Override `API_BASE_URL` in
`frontend/.env.local` when the backend is elsewhere, and rebuild/restart Next.js.
Leave `NEXT_PUBLIC_API_BASE_URL` unset to keep same-origin behavior on phones.
The root `.env.example` documents both processes; neither process automatically
loads a root-level `.env` when started from its own directory.

## API

- `POST /api/v1/decisions` — create (201)
- `GET /api/v1/decisions` — list newest first
- `GET /api/v1/decisions/{id}` — reopen a decision (404 if absent)

Create body:

```json
{
  "situation": "Should I accept this cabinet installation project?",
  "domain": "Work",
  "stakes": "High",
  "time_pressure": "Moderate"
}
```

The backend validates the form's allowed choices and a trimmed situation of at
least ten characters. Responses include `id`, `created_at`, and `updated_at`.

## Verification commands

From `backend/`: `python -m pytest` and `python -m ruff check app tests`.
From `frontend/`: `npm run typecheck` and `npm run build`.

This is a local development build, not an authenticated hosted application.

## Structured context

Open a saved decision, then **Open structured context**. Review the problem,
people, reported facts, constraints, unknowns, and candidate options. Use
**Save reviewed context** to retain changes across reloads.

M3 extracts explicit labeled lines, such as `Actor: Brian` or `Option: Ask for
a delivery date`. It preserves unlabeled prose for manual review. It does not
perform AI interpretation, fact verification, or option scoring. Reopening
returns the saved review instead of regenerating over it.

## Rules and scoring

After saving reviewed context with two or more options, use **Open scoring**.
Add criteria and weights, enter option ratings, and optionally define threshold
rules and a preferred option. **Evaluate and save** persists both the inputs and
explanation. Ratings use 0–10 with higher always better; name cost/risk criteria
accordingly (for example, affordability or safety). Blank ratings stay unknown.

Hard rules exclude options; soft rules subtract points. Every contribution and
triggered rule is visible. Unknowns and ties do not produce an invented winner.
Editing saved context invalidates previous results until a fresh evaluation is
entered. These settings are per-decision inputs, not inferred personal values.

## AI suggestions

Open saved structured context, then **Generate AI suggestions**. This sends the
current decision and context to OpenAI and displays a separate preview. Review
source quotes, assumptions, and options. **Apply suggestions for review** explicitly
replaces the context with an unreviewed draft; review and save before scoring.
AI suggestions do not set your scores, weights, rules, or personal values.

Without server-side OPENAI_API_KEY configuration, manual context and scoring
remain available, and the UI identifies its fallback as not an AI result.
OPENAI_MODEL is configurable (initial default: gpt-4o-mini). API requests have a
30-second timeout and do not automatically retry. No live model call was verified
in this build. Never put a key in frontend variables or committed files.
