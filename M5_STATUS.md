# M5 — AI Reasoning Integration

Status: implemented; offline/provider-contract and browser checks passed. Live OpenAI acceptance pending API access.

## Behavior

A saved decision's structured-context screen can request AI suggestions. The
request sends only that decision, its saved context, and candidate descriptions.
It does not send unrelated history or scoring weights/rules. The UI discloses
that OpenAI receives the decision context.

Suggestions appear in a separate preview containing a proposed problem, actors,
constraints, reported facts with source quotes, unknowns, assumptions, candidate
options with brief rationales, and a tradeoff summary. They cannot set scores,
weights, hard rules, personal values, or a final winner.

Generation does not overwrite the saved analysis. Applying is a separate explicit
user action. Applying replaces structured context/options with an unreviewed
draft, so the user must review and save it before scoring. Existing identical
option descriptions retain their IDs. Changed context invalidates old scores.

## Provider boundary and failures

- OpenAI adapter isolated behind a ReasoningProvider protocol.
- Official Python SDK Responses API with a strict Pydantic output schema.
- Prompt maintained separately as decision-context-v1.
- Configurable OPENAI_MODEL; initial default gpt-4o-mini. No API key is bundled.
- Server-side key only. A 30-second request timeout, no automatic retries, and
  max_output_tokens=2500 bound an individual request. store=False is sent.
- Handles refusals, incomplete output, invalid JSON/schema, timeouts, rate limits,
  authentication/service failures, empty details, duplicate options, and reported
  facts lacking exact source quotes. Provider error bodies are not shown to users.
- Matching quotes establish source traceability, not independent verification or
  proof that the model's paraphrase is faithful. Human review remains required.
- Missing access or provider failure returns an explicitly labeled manual fallback
  retaining the existing context; the fallback is never presented as AI reasoning.

## Persistence and approval

Non-destructive schema initialization adds an immutable suggestions table keyed
by suggestion UUID. Records retain model, prompt version, generation time, source,
proposal, notice, and the source-analysis fingerprint. Applying checks that
fingerprint inside a write transaction. Outdated previews cannot overwrite newly
edited context. Applied analyses retain a provenance reference after manual edits.
Historical suggestion records remain available by ID.

Endpoints under `/api/v1/decisions/{id}`:

- GET `/ai-suggestion`: configuration status and latest preview.
- POST `/ai-suggestion`: generate/persist an AI preview or labeled fallback.
- GET `/ai-suggestion/{suggestion_id}`: historical preview and source evidence.
- POST `/ai-suggestion/{suggestion_id}/apply`: explicit application, guarded against stale context.

## Verification

- 44 backend tests passed, including all M2–M4 regression tests.
- Real OpenAI SDK exercised with an HTTP mock transport for request schema,
  success, refusal, incomplete responses, invalid JSON, unsupported quotes,
  duplicates, blank values, timeout, rate limit, and authentication errors.
- Application tests cover no-key fallback, preservation of reviewed context,
  explicit apply, review, provenance/history, persistence across app sessions,
  and stale-preview rejection.
- Ruff, frontend TypeScript, and production build passed.
- Browser checks with no key and with an injected simulated provider passed.
  Covered preview, explicit apply, review/save, reload, stale-preview disabling,
  mobile overflow, and no browser runtime errors. Mobile and desktop screenshots
  are named `m5-fallback-*` and `m5-simulated-*` in `docs/verification/`.
- Simulated provider exists only in the verification harness, not production code.

## Remaining live check

No OpenAI API key was configured in this environment. No live request, model
quality test, account/model-access verification, or billable API call was made.
A securely configured key is needed to perform a live smoke test. No key should
be pasted into chat or committed to this source archive.

Official API reference used:
https://developers.openai.com/api/docs/guides/structured-outputs

No GitHub push or deployment was performed. The existing Starlette/httpx test
integration deprecation warning remains. M6 (Mind Model) is the next feature
milestone after live M5 validation.
