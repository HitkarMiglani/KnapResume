# ADR 0002: Adopt FastAPI and React for the first slice

## Status

Accepted

## Context

KnapResume needs an implementation stack and a narrow first vertical slice before feature
development can begin. The first slice must prove that a user can enter one professional
fact, normalize it into an atomic bullet, retain its provenance, and persist it without
prematurely introducing resume parsing, job-description processing, LLM calls, or later
pipeline stages.

Profile content is sensitive personal data. Development must therefore establish ownership,
deletion, secret handling, and external-egress boundaries before real user data is allowed.

## Decision

The application will use:

- Python 3.13 with FastAPI for the backend API.
- React with TypeScript and Vite for the frontend.
- PostgreSQL 17 with SQLAlchemy, Alembic, and Psycopg 3 for persistence and migrations.
- `uv` for locked Python dependencies and npm for locked frontend dependencies.
- Pytest for backend tests, Vitest and React Testing Library for frontend tests, and Ruff
  for Python linting and formatting.
- Docker Compose for local PostgreSQL. The backend and frontend run natively during
  development, and all three services bind only to the loopback interface.

The first vertical slice is manual profile entry to a normalized atomic bullet with
provenance, persisted in PostgreSQL using synthetic data. It includes only:

- Email-and-password authentication. Passwords are hashed with Argon2id; plaintext
  passwords are never persisted or logged.
- Server-side sessions identified by a random opaque token. Only a SHA-256 hash of the token
  is stored in PostgreSQL. The host-only session cookie is `HttpOnly`, `SameSite=Lax`, scoped
  to `/`, and `Secure` outside loopback HTTP development. Sessions expire after 12 hours,
  rotate on login, and are revoked on logout or account deletion.
- Synchronizer-token CSRF protection for every state-changing request. The token is bound to
  the server-side session and sent by the React client in a custom header. The Vite
  development proxy keeps browser API requests same-origin; credentialed cross-origin
  requests are not allowed and CORS middleware is not enabled for this slice.
- A random internal UUID as each user's stable ownership key. Email addresses and future
  provider identifiers are attributes, not foreign keys or credentials for data access.
- Fixed profile sections: experience, project, education, and skill.
- An immutable manual source-fact snapshot and a linked normalized profile bullet. Every
  bullet must have a non-null source fact owned by the same user.
- Deterministic, non-generative normalization: Unicode NFC normalization, outer whitespace
  trimming, removal of one recognized leading bullet marker, horizontal-whitespace
  collapsing, rejection of empty or multiline input, and a documented maximum length.
- Owner-scoped create, list, bullet-delete, and account-delete behavior. Bullet deletion
  hard-deletes its unshared source fact in the same transaction; orphan source facts are not
  permitted. Account deletion hard-deletes the identity, sessions, and all owned profile
  data in one transaction.

The slice is localhost-only and synthetic-data-only, including account names and email
addresses. The frontend, backend, and PostgreSQL listeners bind to loopback; PostgreSQL uses
credentials and is not publicly exposed. Secrets and debug settings come from environment
variables; local `.env` files are ignored and only placeholders may be committed. Request
bodies, credentials, tokens, source facts, normalized bullets, email addresses, authorization
headers, cookies, and database URLs must not be logged.

Runtime profile and identity data has zero external egress. The application will not call
LLMs, GitHub, analytics, remote fonts, CDNs, error trackers, or identity providers. Google
sign-in is deferred because it would require an explicit exception defining identity-data
egress, provider retention, consent, account linking, and token lifecycle.

The application will use a separate backend and frontend within one repository because a
typed API boundary is an accepted project requirement. Django and server-rendered templates
were considered as a simpler monolith, but were not selected. No generic service layer,
background worker, cache, object store, or future pipeline package will be added for this
slice.

## Consequences

- The API contract, authentication cookies, session rotation and revocation, CSRF protection,
  same-origin boundary, and validation behavior must be tested across the frontend/backend
  boundary.
- Separate Python and Node.js toolchains add setup and CI work compared with a server-rendered
  monolith, but preserve the selected React client architecture.
- Tests and demonstrations may use only clearly fictional data until a later accepted ADR
  defines encryption at rest, deployment, backups, retention, and deletion propagation for
  real personal data.
- Google sign-in, managed PostgreSQL, LLM and embedding providers, resume and GitHub import,
  scoring, allocation, rewriting, export, and production deployment remain undecided.
