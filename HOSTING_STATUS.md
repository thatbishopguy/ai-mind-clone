# Free hosting preparation — October 6, 2026

Owner approved free hosting, PostgreSQL support, and private sign-in.

Implemented:
- SQLite local development retained; hosted PostgreSQL supported with psycopg.
- Bound parameters, dictionary rows, persistent schema creation, suggestion
  ordering, and transactional stale-analysis protection on both databases.
- Single-owner HTTP Basic sign-in on frontend and backend. Missing production
  credentials prevent access. Public health endpoint has no personal data.
- Free Render backend Blueprint and Vercel/Neon setup documented.

Verification:
- 47 backend tests passed, including three private-access tests.
- Six existing persistence/analysis/suggestion/evaluation workflows passed on
  PGlite's embedded PostgreSQL engine through the PostgreSQL wire protocol.
  This checks SQL compatibility and application-session persistence; it does
  not replace hosted Neon TLS or real multi-session concurrency verification.
- Frontend TypeScript check and production build passed.
- Changed Python files passed Ruff.
- Live local HTTP checks passed for unauthenticated/invalid/valid access to
  frontend and direct backend; authenticated proxy decision save/reopen passed.
- Render YAML parses with plan `free` and automatic deployment disabled.

Not deployed. Neon, Render, and Vercel account connections are pending. No
paid infrastructure was started, public domain created, or live OpenAI request
made. No real credentials are present in source.

Before release: configure matching credentials as provider secrets, provision
only free resources, verify Neon TLS and transaction concurrency, check hosted
access and proxy behavior, and save/reopen a decision across backend restart.
Existing SQLite data is not automatically migrated.

Railway's earlier staged configuration remains unapplied; it is not the selected
hosting path and must not be accepted or deployed.
