# Project Status

> Living document. This is the FIRST place any new session/contributor should read after
> `.github/copilot-instructions.md`. Update this at the end of every session that changes
> what's done, what's in progress, or what's next. Keep it short — link to code/PRs/ADRs
> instead of duplicating detail.

## Last updated

2026-08-31 — implementation stack and first vertical slice accepted in ADR 0002.

## Current phase

Planning complete for the first vertical slice; implementation scaffolding is next.

## Done

- Project synopsis reviewed (`Synopsys_2310993837.docx`).
- Repo conventions and agent-facing docs scaffolded (`.github/`, `docs/`).
- Agent delegation, test ownership, review remediation, and handoff rules clarified.
- FastAPI, React, and PostgreSQL stack accepted
   (`docs/adr/0002-adopt-fastapi-react-stack-and-first-slice-boundary.md`).
- First-slice synthetic-data, ownership, deletion, and zero-egress boundaries defined.

## In progress

- Nothing yet — the accepted first slice is ready for scaffolding.

## Next steps

1. Scaffold the loopback-bound FastAPI backend, React/Vite frontend, and PostgreSQL 17
   development service using official project layouts and a same-origin Vite API proxy.
2. Implement Argon2id email-and-password authentication, revocable server-side sessions,
   synchronizer-token CSRF protection, internal UUID ownership, and hard account deletion.
3. Implement manual synthetic fact entry → deterministic atomic-bullet normalization →
   provenance-linked PostgreSQL persistence.
4. Add focused backend/frontend tests, run the quality gates, and complete Code Reviewer
   approval before closing the slice.

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

- None currently.
