# Architecture

## System layers

```text
User Interface
      ↓
Decision Engine API
      ↓
Rules + Scoring + AI Orchestration
      ↓
Mind Model + Memory Retrieval
      ↓
Persistence + Calibration Data
```

## Boundary rules

### Frontend
Owns presentation, local UI state, form validation, and API interaction. It must not contain core decision policy.

### Backend API
Owns HTTP contracts, validation, orchestration, authentication later, and persistence boundaries.

### Decision Engine
Owns option generation, deterministic rules, scoring, conflict detection, recommendation synthesis, and confidence calculations. AI calls are injected into this layer rather than embedded everywhere.

### Mind Model
Owns values, traits, behavioral rules, exceptions, contextual modifiers, and model confidence.

### Memory
Owns retrieval of relevant prior decisions, experiences, relationships, lessons, and contextual records.

### Calibration
Owns comparison of predicted versus actual choices, reasoning, and outcomes. Calibration data must be retained separately from raw inference output.

## Initial data flow

```text
free-form situation
      ↓
structured context
      ↓
option set
      ↓
relevant mind-model retrieval
      ↓
rules / criteria / scoring
      ↓
AI-supported reasoning
      ↓
recommendation + explanation + confidence
      ↓
persist decision case
      ↓
actual outcome feedback
      ↓
calibration
```

## Persistence strategy

Start with SQLite for local development and low operational complexity. Keep database access behind repository/service boundaries so PostgreSQL can replace SQLite without changing decision-engine behavior.

## AI provider strategy

The OpenAI client will live behind an adapter. Decision-engine code should consume typed internal interfaces, not provider-specific response objects. This prevents provider coupling and makes testing deterministic.

## M2 persistence flow

The existing form submits through a small typed API client. Next.js proxies
same-origin `/api/v1` requests to FastAPI. FastAPI validates the request and
uses a SQLite repository; database details do not enter the UI or future
reasoning engine. An application factory initializes the schema at startup
and supports isolated test databases. Every operation closes its connection.
There is one decisions table; no speculative future-model tables exist.

## M3 structured context boundary

A deterministic extraction module converts explicit source labels into typed
context and stable-ID candidate options. Unclassified prose remains in the
original situation, and missing detail stays empty. Review edits are validated
and stored in a separate analysis table. Reopening never regenerates over a
reviewed payload. No provider, scoring rules, or personal weights are involved.

## M4 evaluation boundary

The scoring module is a pure deterministic function of validated structured
analysis and user-configured evaluation inputs. It has no database or AI calls.
API handlers validate the saved option set, enforce reviewed context, and persist
inputs plus explanation results through the repository. Context fingerprints
identify outdated evaluations; a transaction repeats the fingerprint check on
write. Personal model defaults are not inferred or silently stored.

## M5 provider and review boundary

The reasoning provider returns a typed proposal, not an executable action or a
score. A service creates a persistent preview with source metadata. Only the
explicit apply endpoint can change structured context, and it rechecks the
source fingerprint transactionally and marks the draft unreviewed. The scoring
engine stays deterministic and cannot consume an unreviewed AI replacement.
Original suggestions remain immutable for provenance after subsequent edits.
