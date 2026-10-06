# Free hosting preparation

Approved by the owner on October 6, 2026: Vercel Hobby frontend, Render Free
FastAPI backend, Neon Free PostgreSQL, and private owner access. Keep SQLite
available for local development. No paid service is authorized.

## Deployment configuration

- Neon: create a Free project and use its supplied TLS PostgreSQL connection
  string as backend `DATABASE_URL`. Tables initialize on backend startup.
- Render: use `render.yaml`; explicitly verify `plan: free`. The backend needs
  `APP_ENV=production`, `DATABASE_URL`, `OWNER_USERNAME`, `OWNER_PASSWORD`.
  Optional `OPENAI_API_KEY` must be a replacement for the previously exposed
  key and must only be set as a backend secret.
- Vercel: select `frontend` as the root directory, Next.js framework and Hobby
  plan. Set server-only `API_BASE_URL` to the Render HTTPS URL and set the same
  `OWNER_USERNAME` and `OWNER_PASSWORD` as the backend before deployment.
  Changing `API_BASE_URL` requires a new build because Next.js builds rewrites.
- Never expose credentials through `NEXT_PUBLIC_` variables, source files,
  command output, or GitHub. Only use provider secret settings.
- No direct `NEXT_PUBLIC_API_BASE_URL` override: browser API requests stay
  same-origin, and the authenticated rewrite forwards the Authorization header.

## Private access

The browser asks for the owner's username/password using HTTP Basic auth.
The frontend checks every page and API request except public static assets.
The backend separately checks all application endpoints. Its health endpoint
is public and contains no decision data; production API documentation is disabled.
Production backend refuses to start without credentials; production frontend
returns 503 if credentials are missing. Both sides need HTTPS in hosting.

This is a single-owner sign-in, with no registration, password recovery, or
multi-user roles. Browsers may retain Basic credentials until closed; change the
password in both providers to revoke access. Hosting operators retain access to
infrastructure and stored data.

## Limits and release checks

Render Free sleeps after inactivity and has an ephemeral filesystem. PostgreSQL
keeps decisions outside that filesystem. Free-tier limits apply to all three
providers; OpenAI billing is separate. Check current provider limits before
provisioning and never upgrade a plan automatically.

Existing local SQLite files are not automatically imported into Neon. Preserve
them and arrange a tested import if real decisions need migration. A new Neon
database starts empty.

Before publishing: test PostgreSQL persistence and concurrent stale-analysis
checks, check missing/invalid/valid credentials on both deployed services,
verify the frontend-to-backend rewrite, and save/reopen a decision after restart.
No public deployment or OpenAI request has been made during preparation.
