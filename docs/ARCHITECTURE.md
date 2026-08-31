# Architecture

Source of truth for the KnapResume pipeline design. Keep in sync with
`.github/copilot-instructions.md` (which has the condensed version for agent context) —
this file holds the fuller detail per stage.

## Implementation architecture

The application uses a FastAPI backend, a React and TypeScript frontend built with Vite,
and PostgreSQL persistence through SQLAlchemy, Alembic, and Psycopg 3. The first vertical
slice runs the backend and frontend natively with PostgreSQL 17 in Docker Compose. See
`docs/adr/0002-adopt-fastapi-react-stack-and-first-slice-boundary.md` for the decision and
its constraints.

The first slice supports email-and-password authentication and maps all owned data to a
stable internal user UUID. It accepts one synthetic manual fact, preserves the exact source
snapshot, deterministically normalizes one linked atomic bullet, and supports owner-scoped
listing and hard deletion. Authentication uses Argon2id password hashes, revocable
server-side sessions, and synchronizer-token CSRF protection. Browser API traffic stays
same-origin through the Vite development proxy. Google sign-in and all other external
services are deferred.

## Pipeline stages

1. **Profile Acquisition** — ingest existing resume (parsed), GitHub projects (selected
   repos), and manual entries. Normalized into atomic, tagged bullets.
2. **JD Processing** — job description is parsed (LLM structured extraction, regex
   fallback), boilerplate/bias filtered, and normalized into skills/keywords/seniority
   signals.
3. **Completeness Scoring** — weighted score per profile section, used both to warn the
   user of gaps and as an input to the weakest-section feedback loop.
4. **Structured Profile Store** — Postgres. Bullets are atomic and tagged (skill, section,
   evidence source) so they can be independently scored/selected.
5. **Role-Type Classification** — JD signals map to a section-weight profile (e.g. an IC
   engineering JD weights projects/skills higher than a management JD would).
6. **Per-Section Candidate Scoring** — hybrid embedding similarity + keyword overlap scores
   each bullet against the JD, per section.
7. **Global Knapsack Allocation** — treats total resume space (e.g. one page) as knapsack
   capacity; selects the highest-value combination of bullets under section + space
   constraints. This is the core differentiator vs. one-shot rewriting tools.
8. **Coherence & Dedup Pass** — removes redundant or conflicting bullets post-allocation.
9. **Grounded Rewriting** — LLM rewrites selected bullets for tone/JD-fit while keeping a
   provenance link back to the source fact; every claim gets a verified/unverified flag.
10. **ATS-Safety Validation** — checks parseability (no tables/graphics that break ATS
    parsers) and keyword coverage against the JD.
11. **Weakest-Section Ranking** — JD-specific ranking of which profile section is weakest;
    feeds back into Profile Acquisition, making the loop iterative rather than one-shot.
12. **DOCX / PDF Export** — template-driven rendering of the final resume.

## Data protection boundary

Resumes, profile entries, and imported account data are sensitive personal data. Before a
stage handles real user data or sends data to an external service, its accepted ADR or task
criteria must define retention/deletion, encryption, secret handling, log redaction,
minimum authorization scopes, and exactly which fields may leave the system. Development
and tests use synthetic data until those controls exist.

For the first slice, every service is loopback-only and the application has zero runtime
external egress. All profile and identity data is synthetic. Bullet deletion also deletes
its unshared source fact, and account deletion hard-deletes the identity, sessions, and all
owned profile data. Local development has no automated database backups. Logs exclude
credentials, tokens, personal fields, source facts, normalized bullets, headers, cookies,
and database URLs. Real profile data remains prohibited until a later accepted ADR defines
deployment encryption, backup retention, and deletion propagation.

## Why knapsack, not naive truncation

Existing tools rewrite content in a single LLM pass with no formal notion of space budget
vs. relevance trade-off. Modeling section space as knapsack capacity and bullet
relevance/length as value/weight lets the system make an optimal (not just "first N")
selection under real constraints (one page, per-section minimums, etc.).

## Why provenance/verification is a first-class layer, not a prompt instruction

LLM rewriting can hallucinate unsupported metrics or skills. Every generated claim carries
a pointer back to the source fact (resume line, GitHub commit/README, manual entry) and a
verified/unverified flag, so the UI can visibly flag anything that isn't grounded. This
must survive refactors of the rewriting stage — see the convention in
`.github/copilot-instructions.md`.

## Open design questions

See `docs/STATUS.md` → "Known open questions" and `docs/adr/` for decisions once made. In
addition to the stack, the first implementation ADR must resolve the sensitive-data boundary
for its slice; later integrations may add narrower ADRs when their provider and scopes are
known.
