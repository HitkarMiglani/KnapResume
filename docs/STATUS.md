# Project Status

> Living document. This is the FIRST place any new session/contributor should read after
> `.github/copilot-instructions.md`. Update this at the end of every session that changes
> what's done, what's in progress, or what's next. Keep it short — link to code/PRs/ADRs
> instead of duplicating detail.

## Last updated

2026-08-31 — Code Reviewer pass surfaced two blocking gaps (missing frontend fact-entry
UI, stale/contradictory Blockers section) and three non-blocking issues, all now fixed:
added `ProfilePage` (manual fact entry/list/delete, wired into `App.tsx`), added
session-restore-on-mount to `AuthContext`, added a cascading hard-delete assertion to
`test_account_deletion_revokes_session`, and fixed a latent timezone-handling bug in
`get_current_session`. All quality gates re-verified green after the fixes.

## Current phase

First vertical slice implementation complete end-to-end (backend + frontend) with all
quality gates green. Code Reviewer approved with one trivial follow-up (a dead line in
a test), which has been applied. The slice is closed.

## Done

- Project synopsis reviewed (`Synopsys_2310993837.docx`).
- Repo conventions and agent-facing docs scaffolded (`.github/`, `docs/`).
- Agent delegation, test ownership, review remediation, and handoff rules clarified.
- FastAPI, React, and PostgreSQL stack accepted
   (`docs/adr/0002-adopt-fastapi-react-stack-and-first-slice-boundary.md`).
- First-slice synthetic-data, ownership, deletion, and zero-egress boundaries defined.
- Session/CSRF mechanics and schema pinned
   (`docs/adr/0003-first-slice-session-csrf-and-schema-design.md`).
- Backend scaffolded: FastAPI app, SQLAlchemy models, Alembic migration `0001_initial`,
   `auth` and `profile` routers, deterministic bullet normalization
   (`backend/app/`, `backend/tests/`).
- Frontend scaffolded: Vite/React app entry (`src/main.tsx`, `src/App.tsx`), same-origin
   `apiFetch` client with CSRF header handling (`src/api/client.ts`), `AuthProvider`
   (`src/auth/AuthContext.tsx`), and login/register pages (`src/pages/`).
- All first-slice quality gates passing: backend `pytest` (20 passed) and `ruff check`
   (clean); frontend `npm install`, `npm run build`, and `vitest run` (all green).
- Frontend `ProfilePage` (`src/pages/ProfilePage.tsx`): manual synthetic fact entry, list,
   and delete, wired into `App.tsx` — completes the end-to-end first-slice fact-entry flow
   started server-side by `backend/app/routers/profile.py`. Covered by
   `ProfilePage.test.tsx`.
- `AuthContext` now restores an existing session on mount via `GET /api/auth/session`, so
   a page reload no longer incorrectly drops an authenticated user to the login page.

## In progress

- Nothing — the first slice is closed. Next up: decide and scope the second slice (see
   Known open questions below for candidate directions).

## Next steps

1. ~~Scaffold the loopback-bound FastAPI backend, React/Vite frontend, and PostgreSQL 17
   development service using official project layouts and a same-origin Vite API proxy.~~
   Done.
2. ~~Implement Argon2id email-and-password authentication, revocable server-side sessions,
   synchronizer-token CSRF protection, internal UUID ownership, and hard account
   deletion.~~ Done (`backend/app/routers/auth.py`, `backend/tests/test_auth.py`).
3. ~~Implement manual synthetic fact entry → deterministic atomic-bullet normalization →
   provenance-linked PostgreSQL persistence.~~ Done end-to-end, backend
   (`backend/app/normalization.py`, `backend/app/routers/profile.py`) and frontend
   (`frontend/src/pages/ProfilePage.tsx`).
4. ~~Install dependencies and run the quality gates.~~ Done — backend and frontend gates
   all pass. Remaining: final Code Reviewer confirmation pass before closing the slice.

## Known open questions

- Which LLM/embeddings provider (cost vs. quality vs. offline-capability)?
- Which PostgreSQL hosting model should production use?
- DOCX/PDF export engine choice (template-driven rendering).
- What encryption-at-rest, backup-retention, and deletion-propagation rules are required
   before accepting real personal data?
- Which profile fields may be sent to an LLM provider, and with what user consent?
- What minimum GitHub authorization scopes and token-lifecycle rules will import require?
- Should Google sign-in be added later, and what identity metadata, retention, consent,
   account-linking, and token-lifecycle rules would apply?

## Blockers

- None currently. Local Postgres `knapresume`/`knapresume_test` databases and role are
   provisioned on this machine; a fresh environment will need the same setup (see
   `docker-compose.yml` for the intended containerized alternative, or provision an
   equivalent native Postgres role/db).
