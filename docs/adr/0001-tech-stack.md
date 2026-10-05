# ADR 0001 — Initial technology stack

**Status:** Accepted for M0

## Decision

Use:

- Next.js + React + TypeScript for the frontend
- FastAPI + Python for the backend and decision-analysis layer
- SQLite initially, with PostgreSQL as the production migration target
- OpenAI API behind a provider adapter
- Git/GitHub for source control
- Optional Tauri packaging only after the web application is mature

## Rationale

The frontend benefits from the React/TypeScript ecosystem and responsive web delivery. Python provides a strong environment for structured reasoning, scoring, experimentation, embeddings, statistical calibration, and future machine-learning work. Separating the two layers lets the product UI evolve independently from the behavioral model.

## Consequences

The application has two development runtimes. API contracts therefore need explicit schemas and tests. This cost is accepted because it gives the project cleaner boundaries and substantially more flexibility for later decision-model research.
