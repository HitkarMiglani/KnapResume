# Project Status

> Living document. This is the FIRST place any new session/contributor should read after
> `.github/copilot-instructions.md`. Update this at the end of every session that changes
> what's done, what's in progress, or what's next. Keep it short — link to code/PRs/ADRs
> instead of duplicating detail.

## Last updated

2026-09-09 (PM) — Phase 0 (Quality and Governance) completed. Frontend quality gates
re-verified: `npm run build` and `npm test -- --run` both passing (6 test files, all green).
Backend quality gates confirmed green: `pytest` 62 passed, `ruff check` clean (fixed
line-length issue in `app/routers/job_descriptions.py`). ADR 0006 (AI Provider Data
Governance and External Egress Boundary) accepted, defining OpenAI-compatible Chat
Completions as Phase 1–3 provider, data egress boundaries, retention/deletion policies,
logging/redaction rules, and the requirement for a production-specific ADR before Phase 4+
real-data deployment. All Phases 1–3 slices (manual entry, JD parsing, resume ingestion)
are implementation-complete and quality-gated. Ready to scope Phase 2 (Tailoring Core:
role classification + candidate scoring).

## Current phase

Third vertical slice closed. Phase 1 Resume Ingestion is 100% completed, reviewed, and fully verified. Local PDF/DOCX text extraction using `pypdf` and `python-docx`, structured profile parsing (AI extraction with deterministic fallback), and same-origin authenticated endpoints with CSRF protection, plus React frontend UI.

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
- Second slice implemented per ADR 0004: `JobDescription` model + migration
  `0002_job_descriptions` (owner-scoped, cascade-delete); `app/jd_parsing.py`
  (AI structured skills/keywords/seniority extraction with deterministic fallback);
  `app/completeness.py` + `GET /api/profile/completeness` (per-section + overall
   score from existing `source_facts`); `app/routers/job_descriptions.py` (owner-scoped
   CRUD, CSRF-protected mutations); frontend `JobDescriptionPage.tsx` (paste form, JD list
   with extracted fields, delete, completeness display), wired into `App.tsx`.
- Backend tests: `test_jd_parsing.py`, `test_completeness.py`, `test_job_descriptions.py`
   (owner-scoping, CSRF, bounds, cascade-delete including the new `job_descriptions` table
   in `test_account_deletion_revokes_session`). Frontend: `JobDescriptionPage.test.tsx`.
- All second-slice quality gates passing: backend `pytest` (40 passed) and `ruff check`
   (clean, after fixing an `ARRAY(String)`/`ARRAY(Text)` model/migration mismatch).
- Third slice implemented per ADR 0005: `ResumeImport` database model + migration `0003_resume_imports` (owner-scoped, cascade-delete); `app/resume_parsing.py` (local PDF extraction with `pypdf`, DOCX extraction with `python-docx`, structured profile parsing with AI model + deterministic local fallback); `app/routers/profile_imports.py` (owner-scoped file upload `POST /api/profile/import`, listings `GET /api/profile/imports`, and deletes `DELETE /api/profile/imports/{id}`); frontend `ProfilePage.tsx` upgraded with file drop / input form, upload validations (under 5MB, accepted formats), active resume imports listings tables, and cascade delete action listeners.
- Backend tests: `test_resume_parsing.py` (8 passed), `test_profile_imports.py` (10 passed) including owner scoping, CSRF, bounds, file-size validations, same-origin, and cascade-delete verification. Frontend: `ProfilePage.test.tsx` upgraded with complete multipart form upload mocks, size limit checks, file-format alerts, listings data maps, and delete callbacks.
- All third-slice quality gates passing: backend `pytest` (50 passed) and ruff checks clean; frontend tests verified green and clean.
- ADR 0006 (AI Provider Data Governance and External Egress Boundary) accepted: defines
  OpenAI-compatible Chat Completions as primary provider for Phases 1–3, data-egress
  boundaries (JD text, extracted resume text, selected bullets only; no user ID/email/
  metadata), retention/deletion/logging policies, user consent requirements before Phase 4+,
  and provider-selection criteria for production deployment.

## In progress

- Nothing in progress. Third slice closed.

## Next steps

1. Scope a fourth slice. The most likely next step is Phase 2 (Tailoring Core) which builds role-type classification and candidate scoring (stages 5 & 6 of pipeline).

## Known open questions

- Which PostgreSQL hosting model should production use?
- DOCX/PDF export engine choice (template-driven rendering).
- What encryption-at-rest, backup-retention, and deletion-propagation rules are required
   before accepting real personal data? (Deferred to production-phase ADR per ADR 0006)
- Which profile fields may be sent to an LLM provider, and with what user consent?
- What minimum GitHub authorization scopes and token-lifecycle rules will import require?
- Should Google sign-in be added later, and what identity metadata, retention, consent,
   account-linking, and token-lifecycle rules would apply?

## Blockers

- None currently. Local Postgres `knapresume`/`knapresume_test` databases and role are
   provisioned on this machine; a fresh environment will need the same setup (see
   `docker-compose.yml` for the intended containerized alternative, or provision an
   equivalent native Postgres role/db).
