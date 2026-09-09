# ADR 0004: Second slice uses AI JD processing with deterministic fallback

## Status

Accepted

## Context

The first slice (ADR 0002, ADR 0003) closed with manual fact entry → normalized,
provenance-linked bullets, zero runtime external egress, and synthetic data only. The next
unimplemented pipeline stages per `docs/ARCHITECTURE.md` are JD Processing (stage 2) and
Completeness Scoring (stage 3).

`docs/STATUS.md` lists open questions about the provider and data-egress consent. This slice
resolves the provider interface as an OpenAI-compatible Chat Completions API, configured by
environment variables, while keeping the prompt limited to the pasted job description.

Stage 2 (per `docs/ARCHITECTURE.md`) names LLM extraction with a regex fallback. Stage 3
(Completeness Scoring) remains local and only needs per-section counts already present in
the existing `source_facts`/`bullets` schema.

## Decision

The second vertical slice is: **JD paste input → AI structured skills/keywords/seniority
extraction (with deterministic fallback when AI is not configured) → owner-scoped
persistence, plus completeness scoring over the existing profile schema.** It includes only:

- **JD input**: plain-text paste only (a `raw_text` field), submitted by an authenticated
  user. File/document upload and resume parsing remain deferred, matching the first slice's
  "no resume/GitHub parsing yet" boundary — paste is the smallest input path that lets JD
  processing start.
- **JD parsing**: an OpenAI-compatible Chat Completions request asks for strict JSON with
  skills, keywords, and seniority. The response is validated and normalized before storage.
  If no API key is configured, the deterministic regex/keyword-list parser is used. If AI is
  configured but unavailable or invalid, the request fails rather than silently storing a
  lower-quality parse.
- **Persistence**: a new `job_descriptions` table, owned by the requesting user
  (`user_id` FK, `ON DELETE CASCADE`), storing `raw_text` and the regex-derived
  `skills`, `keywords`, and `seniority` as a snapshot of that parse. Owner-scoped create,
  list, get-by-id, and delete. No update endpoint — a changed JD is a new paste, consistent
  with the first slice's "no partial edit" simplicity.
- **Completeness scoring**: a read-only endpoint computed live from existing
  `source_facts` grouped by the four fixed sections (`experience`, `project`, `education`,
  `skill`). Each section gets a bounded `0.0–1.0` score (count against a fixed per-section
  target constant) and the response includes an overall score. No new schema, no
  persistence — this is a derived view, not new stored state, so there is nothing to keep
  in sync if the scoring formula changes later.
- **External AI boundary**: AI processing is opt-in through `AI_API_KEY`, `AI_BASE_URL`,
  `AI_MODEL`, and `AI_TIMEOUT_SECONDS`. Only the pasted JD is sent in the request. Deployments
  must provide provider retention, encryption, and consent controls before real personal data
  is enabled.

Explicitly out of scope for this slice, deferred to later ADRs/slices:

- Embeddings and all later LLM pipeline stages.
- JD file/document upload and parsing.
- Role-type classification, per-section candidate scoring, knapsack allocation, coherence/
  dedup, grounded rewriting, ATS validation, weakest-section ranking, and export (pipeline
  stages 5–12) — all still depend on the deferred LLM decision or on stages not yet built.
- Any change to session/CSRF/auth mechanics (ADR 0003 stands unmodified).

## Consequences

- Stage 2 now uses richer AI extraction when configured while retaining a deterministic local
  fallback for development and offline operation.
- The external provider boundary is explicit: the API key is never logged, and only the JD
  text is included in the AI request.
- The `job_descriptions` schema stores a point-in-time parse snapshot rather than being
  recomputed on read; if the regex rules change later, existing rows keep their original
  parse until the user submits a new paste. This mirrors the immutable-snapshot pattern
  `source_facts` already uses.
- A later ADR must resolve production provider retention, consent, and deployment controls
  before real personal data is sent to the AI provider.
