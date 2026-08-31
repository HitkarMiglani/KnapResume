# KnapResume — Agent Instructions

> Read this file first, every session. It replaces re-reading the whole codebase.
> Keep it updated whenever architecture, stack, or conventions change — this is the
> single source of truth a new chat session (or new contributor) uses to get up to speed.

## What this project is

**KnapResume: Optimal Content Allocation and Provenance Tracking for Job-Aligned Resumes**
(Co-op project, Chitkara University — Hitkar Miglani, 2310993837).

A tool that turns a user's raw professional data (existing resume, GitHub projects, manual
entries) into a **job-description-tailored, ATS-friendly resume**, treating resume generation
as a **constrained optimization problem** instead of one-shot text generation.

Core differentiators vs. existing AI resume tools (Rezi, Teal, Kickresume):
1. **Section-aware, knapsack-based content allocation** — fits the most relevant bullets into a
   fixed space budget (e.g. one page) instead of naive rewriting.
2. **Provenance & verification layer** — every generated claim must trace back to a fact the
   user actually provided; flags anything unverified.
3. **Weakest-section feedback loop** — per-JD analysis of which profile section is weakest,
   feeding back into profile intake for iterative improvement (not a single-shot document).

## Pipeline (see docs/ARCHITECTURE.md for details)

```
User Profile Intake (resume upload / GitHub / manual) ─┐
Job Description Input (paste/upload)                    ├─> parallel intake
                                                         ┘
JD Parsing (LLM extraction + regex fallback) → skills/keywords/seniority
Completeness Scoring → weighted score per profile section
Structured Profile Store (Postgres: atomic, tagged bullets)
Role-Type Classification → section weight profile
Per-Section Candidate Scoring (embedding similarity + keyword overlap, hybrid)
Global Knapsack Allocation → fits selected bullets to space budget
Coherence & Dedup Pass → removes redundant/conflicting bullets
Grounded Rewriting → provenance-tracked, verified flag per claim
ATS-Safety Validation → parseability + keyword coverage score
Weakest-Section Ranking (JD-specific) → feeds back into profile intake
DOCX / PDF Export (template-driven)
```

## Tech stack

- Backend: Python 3.13, FastAPI, SQLAlchemy, Alembic, Psycopg 3; `uv` for dependencies
- Frontend: React, TypeScript, Vite; npm for dependencies
- Database: PostgreSQL 17 (local Docker Compose for the first slice)
- Tests/quality: Pytest, Vitest, React Testing Library, Ruff
- LLM/embeddings provider: Not yet decided
- Export/rendering engine (DOCX/PDF): Not yet decided

See `docs/adr/0002-adopt-fastapi-react-stack-and-first-slice-boundary.md`. Until a later
data-protection ADR is accepted, every service is loopback-only, all profile and identity
data is synthetic, and no runtime external egress is permitted.

## Working model

- Single active developer at a time (even though multiple people may contribute over time).
  There is no need to reason about concurrent-edit conflicts within a session — but every
  session/handoff MUST leave the repo in a state the next person/session can pick up from
  `docs/STATUS.md` alone.
- All versioning/history lives in git. Do not keep parallel "current state" docs outside
  `docs/STATUS.md` and `CHANGELOG.md`.
- Branching: `main` is always releasable. Work happens on `feat/<slug>`, `fix/<slug>`,
  `chore/<slug>` branches, merged via PR (see `.github/PULL_REQUEST_TEMPLATE.md`).
- Before ending a session that changed the plan, architecture, or status: update
  `docs/STATUS.md` and, for any non-trivial/irreversible decision, add an ADR under
  `docs/adr/`.

## Conventions

- Keep provenance/verification metadata attached to every generated resume claim — never
  strip it silently, even in intermediate refactors.
- The knapsack allocation logic touches scoring + allocation together; don't split them
  across modules without updating this file and `docs/ARCHITECTURE.md`.
- Treat resumes, profile entries, and imported account data as sensitive personal data.
  Before a slice handles real user data or calls an external provider, its accepted ADR or
  task criteria must define data retention/deletion, encryption, secret handling, log
  redaction, minimum authorization scopes, and what data may leave the system.

## Follow standard project structure

- Use the conventional, idiomatic layout for whatever stack is chosen (e.g. a standard
  Next.js/Django/Spring layout) — don't invent a custom folder structure. If unsure what's
  standard for the chosen stack, say so and use the framework's official scaffold/CLI
  rather than guessing.
- One clear place for each concern: source in `src/` (or the stack's convention), tests
  mirroring source layout, config at repo root. Don't scatter config or create ad-hoc
  `utils`/`common`/`shared` dumping grounds.
- New top-level folders or major structural changes are a decision — record them as an ADR
  (`docs/adr/`), don't introduce them silently mid-task.

## Prevent over-engineering

- Build only what the current task needs. Do not add abstraction layers, config options,
  extensibility hooks, or speculative future stages "while you're in there."
- Do not create agents, skills, helper modules, or docs for a stage/feature that doesn't
  exist in code yet. Write them when the code they support actually exists, not in advance.
- Prefer the smallest change that satisfies the request. If a task seems to require a new
  pattern/dependency/architecture, stop and ask or propose it as an ADR before building it.
- No unused code paths, no unrequested tests/config for hypothetical scenarios, no
  "just in case" parameters.

## Where to look before asking / re-deriving things

| Need | Look here first |
|---|---|
| Current status / in-progress work / next steps | `docs/STATUS.md` |
| Why a past decision was made | `docs/adr/` |
| High-level architecture & pipeline detail | `docs/ARCHITECTURE.md` |
| Original problem statement / academic framing | `Synopsys_2310993837.docx` |
| Coding conventions for a specific area | `.github/instructions/*.instructions.md` |
| Planning/coordinating a feature, task breakdown | `Architect` agent (`.github/agents/`) |
| Backend/API/DB/pipeline implementation | `Backend Developer` agent (`.github/agents/`) |
| Frontend/UI implementation | `Frontend Developer` agent (`.github/agents/`) |
| Writing tests / code quality checks | `Tester` agent (`.github/agents/`) |
| Read-only review gate before merge | `Code Reviewer` agent (`.github/agents/`) |
| End-of-session handoff (status/ADR/changelog) | `.github/prompts/update-status.prompt.md` |

## Team workflow

For non-trivial feature work, use the agent team instead of one flat session:
`Architect` (plans, owns ADRs, delegates, prevents drift) → `Backend Developer` /
`Frontend Developer` (implement one scoped task each) → `Tester` (coverage) →
`Code Reviewer` (read-only gate). The Architect supplies the exact change-set, routes any
requested changes back to the responsible developer, reruns affected checks, and repeats
review until approved or blocked before closing out `docs/STATUS.md`. Don't skip
`Code Reviewer` for non-trivial changes.
