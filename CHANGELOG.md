# Changelog

All notable changes to this project are documented here.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
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
