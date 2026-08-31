# KnapResume

KnapResume is a job-aligned resume optimization system that selects and rewrites profile
content using a constrained allocation approach, with provenance tracking for every claim.

## Current State

- First vertical slice is complete end-to-end (FastAPI backend, React/Vite frontend,
  PostgreSQL persistence).
- Implemented authentication with Argon2id passwords, revocable server-side sessions, and
  CSRF protection.
- Implemented manual synthetic fact entry, deterministic bullet normalization, and
  owner-scoped list/delete flows across backend and frontend.
- Current quality gates are green for the first slice (backend tests/lint and frontend
  build/tests).
- Development boundary remains loopback-only with synthetic data and no runtime external
  egress.

## Planned Outcomes

- Add JD parsing and role-type classification for job-targeted resume adaptation.
- Introduce hybrid candidate scoring (embedding similarity + keyword overlap).
- Implement global knapsack allocation for optimal space-constrained bullet selection.
- Add coherence/dedup, grounded rewriting with verification flags, and ATS-safety checks.
- Implement weakest-section feedback to guide profile improvement.
- Finalize DOCX/PDF template-driven export and unresolved provider/hosting/security decisions.

## Project References

- Status and active direction: `docs/STATUS.md`
- Detailed pipeline and architecture: `docs/ARCHITECTURE.md`
- Recorded decisions (ADRs): `docs/adr/`
