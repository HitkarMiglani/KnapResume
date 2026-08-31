# ADR 0003: First-slice session/CSRF mechanics and schema design

## Status

Accepted

## Context

ADR 0002 pins the security properties for the first slice (Argon2id, SHA-256-hashed opaque
session tokens, `HttpOnly`/`SameSite=Lax` cookie, 12-hour expiry with rotation on login,
synchronizer-token CSRF, no CORS). It does not pin the concrete cookie/header names, how the
CSRF token reaches the client, or the database schema. Those are needed to start
implementation and are hard to change once the frontend and backend both depend on them.

## Decision

**Cookies/headers**

- Session cookie name: `session_id`. Value is the opaque, high-entropy session token
  (`secrets.token_urlsafe(32)`); only its SHA-256 hex digest is stored server-side.
- CSRF header name: `X-CSRF-Token`. The synchronizer token is a second opaque random value
  generated at login/registration, stored server-side on the session row, and returned once
  in the JSON body of `POST /api/auth/login` and `POST /api/auth/register`. The React client
  holds it in memory (not a cookie, not `localStorage`) and sends it on every
  state-changing request (`POST`/`PATCH`/`DELETE`). `GET /api/auth/session` also returns the
  current CSRF token for the active session so a page reload can recover it.
- Requests missing/mismatching `X-CSRF-Token` for a state-changing route are rejected with
  `403` before touching the database.

**Schema (PostgreSQL, SQLAlchemy models, Alembic-managed)**

- `users`: `id UUID PK (server-generated)`, `email TEXT UNIQUE NOT NULL`,
  `password_hash TEXT NOT NULL`, `created_at TIMESTAMPTZ NOT NULL DEFAULT now()`.
- `sessions`: `id UUID PK`, `user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE`,
  `token_hash CHAR(64) UNIQUE NOT NULL`, `csrf_token TEXT NOT NULL`,
  `created_at TIMESTAMPTZ NOT NULL DEFAULT now()`, `expires_at TIMESTAMPTZ NOT NULL`.
- `source_facts`: `id UUID PK`, `user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE`,
  `section TEXT NOT NULL CHECK (section IN ('experience','project','education','skill'))`,
  `raw_text TEXT NOT NULL`, `created_at TIMESTAMPTZ NOT NULL DEFAULT now()`.
- `bullets`: `id UUID PK`, `user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE`,
  `source_fact_id UUID UNIQUE NOT NULL REFERENCES source_facts(id) ON DELETE CASCADE`,
  `normalized_text TEXT NOT NULL`, `created_at TIMESTAMPTZ NOT NULL DEFAULT now()`.
  The `UNIQUE` constraint on `source_fact_id` encodes "every source fact has at most one
  bullet" so bullet deletion can find its exactly-one, unshared source fact.
- Deleting a bullet deletes its `source_facts` row in the same transaction (application-level
  transaction, not `ON DELETE CASCADE` from bullet to fact, since the FK direction is
  fact → bullet). Deleting a user cascades to `sessions`, `source_facts`, and `bullets` via
  `ON DELETE CASCADE` at the database level.

## Consequences

- The CSRF token is never persisted client-side across a hard page reload except by calling
  `GET /api/auth/session`; this is acceptable for a first slice with no offline requirement.
- Because `source_fact_id` is unique on `bullets`, this schema cannot yet support a fact
  shared by multiple bullets; that is out of scope until a later slice needs it, matching
  ADR 0002's "one linked atomic bullet" boundary.
- Any later slice that changes cookie names, CSRF delivery, or adds a second session
  transport (e.g. a mobile client) must supersede this ADR rather than edit it in place.
