# Changelog

All notable changes to this project are documented here.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- Phase 0 (Quality and Governance) completion: ADR 0006 (AI Provider Data Governance and 
  External Egress Boundary) accepted, defining OpenAI-compatible Chat Completions as the 
  provider for Phases 1–3, data-egress boundaries (JD text, extracted resume text, selected 
  bullets only; no user identity or metadata), retention/deletion/logging policies, user 
  consent requirements before production Phase 4+ deployment, and provider-selection criteria 
  for future migrations (`docs/adr/0006-ai-provider-data-governance-and-egress-boundary.md`).
- Phase 1 (Resume Ingestion) implemented per `docs/adr/0005-third-slice-resume-ingestion-pdf-docx-parsing.md`.
- Added pure-python binary extraction dependencies `pypdf>=5.0.0` and `python-docx>=1.1.0` (`backend/pyproject.toml`).
- Created `ResumeImport` model and database schema migration `0003_resume_imports` supporting owner isolation and cascade-deletion (`backend/app/models.py`, `backend/migrations/versions/0003_resume_imports.py`).
- Implemented file text extraction and structured parsing using LLM with deterministic fallback (`backend/app/resume_parsing.py`).
- Created profile import group routes `POST /api/profile/import` (synchronized, max 5MB limit, extensions check), list active imports `GET /api/profile/imports`, and delete imports `DELETE /api/profile/imports/{id}` (`backend/app/routers/profile_imports.py`).
- Enhanced frontend same-origin API client (`frontend/src/api/client.ts`) to natively support raw `FormData` uploads without JSON serialization.
- Built interactive "Import Resume" section in `frontend/src/pages/ProfilePage.tsx` with file validations, active import records tables, delete triggers, and live data synchronization.
- Created robust backend test suites `test_resume_parsing.py` and `test_profile_imports.py` and frontend coverage `ProfilePage.test.tsx`.
- AI-backed JD extraction through a configurable OpenAI-compatible Chat Completions API,
  with validated structured output and a deterministic fallback when no API key is configured.
- Second-slice scope decided: JD paste input, AI-backed skills/keywords/seniority extraction
  with deterministic fallback, and completeness scoring (`docs/adr/0004-second-slice-regex-only-jd-processing-and-completeness-scoring.md`).
- Second slice implemented: `JobDescription` model + migration `0002_job_descriptions`
  (`backend/app/models.py`, `backend/migrations/versions/0002_job_descriptions.py`);
  deterministic JD parsing (`backend/app/jd_parsing.py`) and completeness scoring
  (`backend/app/completeness.py`), both zero-network-I/O; owner-scoped, CSRF-protected
  `job_descriptions` CRUD router and `GET /api/profile/completeness`
  (`backend/app/routers/job_descriptions.py`); frontend `JobDescriptionPage.tsx` (paste
  form, JD list with extracted skills/keywords/seniority, delete, completeness display),
  wired into `App.tsx`.
- Backend tests: `test_jd_parsing.py`, `test_completeness.py`, `test_job_descriptions.py`.
  Frontend tests: `JobDescriptionPage.test.tsx`.
- Initial repository scaffolding: `.github/` agent instructions, issue/PR templates, CI
  skeleton, `docs/STATUS.md`, `docs/ARCHITECTURE.md`, `docs/adr/`.
- Frontend app entry point (`frontend/src/main.tsx`, `frontend/src/App.tsx`) wiring
  `AuthProvider` with a login/register toggle, completing the first-slice frontend
  scaffold alongside the existing `api/client.ts`, `auth/AuthContext.tsx`, and
  `pages/{Login,Register}Page.tsx`.
- Frontend tests for the auth client, `AuthContext`, and the login/register pages
  (`frontend/src/api/client.test.ts`, `frontend/src/auth/AuthContext.test.tsx`,
  `frontend/src/pages/LoginPage.test.tsx`, `frontend/src/pages/RegisterPage.test.tsx`).

### Fixed
- Phase 0 quality-gate re-verification: frontend `npm run build && npm test -- --run` 
  passing (6 test files, all green); fixed unused parameter warning in 
  `ProfilePage.test.tsx` (line 168); backend `pytest` 62 passed, `ruff check` clean after 
  fixing line-length violation in `app/routers/job_descriptions.py` (line 30).
- Added missing `email-validator` dependency required by `pydantic.EmailStr`
  (`backend/pyproject.toml`).
- Resolved all 26 `ruff` findings: configured `extend-immutable-calls` for FastAPI
  `Depends` (avoids B008 false positives on the standard DI pattern), plus import-sort
  and line-length fixes in `app/routers/auth.py` and `tests/test_auth.py`.
- Code Reviewer remediation: added the missing frontend fact-entry UI
  (`frontend/src/pages/ProfilePage.tsx` + tests) so the first slice is actually
  end-to-end; `AuthContext` now restores an existing session on mount instead of always
  showing the logged-out view after a reload; `test_account_deletion_revokes_session` now
  asserts bullets/source_facts are actually cascade-deleted; fixed a naive-datetime
  timezone-handling bug in `get_current_session` (`backend/app/dependencies.py`).
- Second-slice Code Reviewer remediation: fixed an `ARRAY(String)`/`ARRAY(Text)`
  model/migration type mismatch on `JobDescription.skills`/`keywords`
  (`backend/app/models.py`); added a `job_descriptions` cascade-delete assertion to
  `test_account_deletion_revokes_session`; added error handling to
  `JobDescriptionPage.handleDelete` so a failed delete surfaces a user-visible error
  instead of an unhandled rejection.
