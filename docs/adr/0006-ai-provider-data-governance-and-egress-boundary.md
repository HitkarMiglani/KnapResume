# ADR 0006: AI provider data governance and external egress boundary

## Status

Accepted

## Context

The first three slices (ADRs 0002–0005) use AI-backed parsing for JD and resume content
(optional, with deterministic regex fallback), but defer the production data-governance
boundary. `docs/BUILD_PLAN.md` Phase 0 requires this ADR before Phase 2+ (scoring, rewriting)
can proceed with real personal data. The system currently uses an OpenAI-compatible Chat
Completions API, configured by environment variables, supporting any OpenAI-compatible
provider (OpenAI, Azure, Ollama, local).

The open questions are:
- Which AI provider will production use, and what are its data retention and compliance terms?
- Which user data fields may be sent to the provider, and with what user consent?
- What user data must never leave the system (e.g. raw resumes, profiles)?
- How will the system handle provider timeouts, rate limits, and credential rotation?
- What audit trail and deletion-propagation rules apply to provider data?
- When can the system transition from synthetic-only test data to real personal data?

## Decision

### 1. Provider Selection

**Current choice for Phase 1–3 (Synthesis + Development)**

- **Primary provider**: OpenAI Chat Completions API (or OpenAI-compatible endpoint).
- **Rationale**: Industry-standard, well-documented, cost-transparent, supports structured JSON
  output (necessary for extraction tasks), widely available, and covers both JD parsing and
  grounded rewriting stages.
- **Fallback**: Local deterministic regex/keyword-list parser (always enabled) for offline
  testing, CI/CD, and development without credentials.
- **Flexibility**: The implementation uses an abstraction layer (`app/config.py`,
  `app/jd_parsing.py`, `app/resume_parsing.py`) so providers can be swapped in later (e.g.
  Anthropic, local LLaMA) without rewriting parsing logic.

**Production provider selection criteria** (to be resolved before Phase 4 + real data)

Future production deployments must select a provider that satisfies:
- **Data residency**: Where are user inputs stored? (EU, US, other?)
- **Retention policy**: How long does the provider retain input/output? (delete-on-request,
  30-day auto-purge, indefinite, etc.)
- **Compliance**: SOC 2 Type II, GDPR-compliant, HIPAA, PCI-DSS if required.
- **Audit trail**: Can the user/operator retrieve a log of what data was sent and when?
- **Cost model**: Per-token, per-request, or subscription? What are growth/scale costs?
- **IP ownership**: Who owns the copyrights to generated outputs?

### 2. Data Egress Boundaries

**Permitted to send to AI provider (when `ai_api_key` is configured)**

- **Plain-text job descriptions**: The raw user-pasted JD (`raw_text` field) is sent to extract
  skills, keywords, and seniority. The system sends only the text, no metadata/IDs.
- **Plain-text extracted resume content**: For structured resume parsing, only the extracted
  plain-text lines from PDF/DOCX (no binary) are sent. No user ID, file name, or source
  metadata.
- **Selected profile bullets (only during rewriting)**: In Phase 4, the system rewriting
  selected bullets sends only the bullet text and the job description to preserve grounding
  context. No user identity, bullet IDs, or session tokens.

**Explicitly forbidden to send to provider**

- **User identity**: No email, user ID, account names, or authentication state.
- **Raw binary content**: PDF/DOCX files are never sent; only extracted text.
- **Metadata**: Session tokens, CSRF tokens, API keys, database IDs, or other system
  identifiers.
- **Sensitive profile fields** (future phases): Any personal information (phone, address,
  SSN, date of birth) must be redacted before sending, even if extracted from a resume.

### 3. Retention and Deletion

**Provider data retention (current phase)**

- The system treats all AI provider interactions as **ephemeral**. No explicit retention
  request is sent; the provider's default retention policy applies.
- The system does not request the provider to persist parsed output. Parsed results are
  stored locally in PostgreSQL under the user's ownership.
- User deletion (via `DELETE /api/auth/account`) deletes all locally stored parsed results
  and metadata. **The system cannot request deletion from the provider**, so deployments must
  rely on the provider's automatic retention policy or request deletion through the provider's
  user account.

**Future production requirement**

Before production deployment with real data, the selected provider must support:
- **Deletion-on-request**: User deletion triggers a system-initiated API call to the provider
  to delete all associated input/output data.
- **Data export**: The system can retrieve a copy of all data sent to the provider (GDPR
  subject-access requirement).
- **Audit logging**: The provider offers a queryable log of when data was sent, processed, and
  deleted.

### 4. Logging and Error Handling

**What is NOT logged (ever)**

- Raw user text (job descriptions, resume content, profile bullets).
- AI provider request/response payloads.
- API credentials (API key, auth header).
- User identity (email, ID).
- Extracted structured data if it contains PII.

**What IS logged** (in DEBUG mode, only for troubleshooting)

- Provider endpoint URL (without auth header).
- HTTP status code (200, 429, 500, timeout).
- Parsing failure reason (e.g. "timeout", "invalid JSON response", "API key missing").
- Token usage (if provider returns usage metadata): only counts, no content.

**Error handling**

- If the AI provider is unavailable (timeout, 5xx error, invalid key), the system falls back
  to the deterministic regex parser without retrying the provider.
- If the provider returns malformed JSON, the deterministic parser is used as fallback.
- The end-user sees a success/failure message (e.g. "Parsed successfully" or "Using
  offline parser due to connectivity issue") but does not see provider-specific errors in the
  UI.
- Operator logs (backend stdout) only include timeout/HTTP-status-level failures, never raw
  payloads.

### 5. User Consent and Transparency

**Current phase (synthetic data only)**

- No user consent is collected yet; all test data is fictional.

**Before Phase 4+ (real data)**

- **Consent prompt**: Users must acknowledge that job descriptions and extracted profile
  text will be sent to the configured AI provider for parsing. The prompt must name the
  provider and link to its privacy policy.
- **Opt-out**: Users can disable AI parsing by not providing an API key (defaults to
  deterministic fallback).
- **Privacy notice**: The login/onboarding flow must state that profile data is stored
  locally and processed with the configured AI provider; user agreements must reflect this.

### 6. Cost and Rate Limiting

**Current implementation**

- No cost tracking or rate-limit enforcement in-app. Costs are managed at the provider
  account level.
- Deployments must monitor provider API usage and alerts independently.

**Future operations (Phase 4+)**

- The system should log (to secure audit trail, not stdout) token counts returned by the
  provider per user per month.
- If rate limits are hit (429 response), the system backs off and uses the fallback parser.
- Deployments should implement budget caps and alerts (provider-side or proxy-side) to
  prevent runaway costs.

### 7. Credential Management

**Configuration**

- AI provider credentials are supplied via environment variables:
  - `AI_API_KEY`: The API key (never committed to git, ignored by `.gitignore`).
  - `AI_BASE_URL`: The endpoint URL (defaults to OpenAI if not set).
  - `AI_MODEL`: The model name (defaults to `gpt-4-turbo`).
  - `AI_TIMEOUT_SECONDS`: HTTP request timeout (defaults to 30s).
- Credentials are never logged, never stored in the database, and never passed to the client.

**Rotation**

- Environment variables are read at application startup. Credential rotation requires
  restarting the application (acceptable for Phase 1–3 development; production deployments
  should use a credential-management service like AWS Secrets Manager or HashiCorp Vault).

### 8. Transition from Synthetic to Real Data

**Phase 1–3 (Now through Phase 2–3 completion)**

- All test fixtures use synthetic/fictional data (names, emails, job descriptions).
- AI provider (if configured) receives only synthetic test data.
- Real user data is not stored, ingested, or tested.

**Phase 4+ (Grounded Rewriting and Production)**

This ADR must be superseded or extended by a production-specific ADR before real data flows,
addressing:
- Which provider is selected, and what are its compliance certifications?
- Has user consent been integrated into the onboarding flow?
- Has audit logging (deletion timestamps, provider egress logs) been implemented?
- Has encryption-at-rest for stored profile data been implemented?
- What data retention and backup schedules apply?

**Unblocking Phase 4**

Phase 4 (Grounded Rewriting + ATS Validation) can proceed in a development environment with
synthetic data once this ADR is accepted. Production deployment of Phase 4 is blocked until a
separate production-data ADR is accepted.

## Consequences

- Deployments without an `AI_API_KEY` will use the deterministic fallback parser. This is
  fully supported and sufficient for development, testing, and offline scenarios.
- AI-backed parsing (when configured) sends text-only payloads to the provider, never binary
  or metadata. This aligns with the privacy-and-ai-boundary instructions and minimizes data
  egress.
- User deletion does not (yet) request deletion from the provider. This is acceptable for
  Phase 1–3 (synthetic data); production deployments must add provider-side deletion API
  calls.
- The provider abstraction (`app/config.py`, parsing modules) makes it straightforward to
  swap providers later (e.g. move to Anthropic, local LLaMA, or a different cost/compliance
  model) without refactoring calling code.
- Operator logs exclude sensitive payloads and credentials, reducing compliance risk and
  making logs safe for auditing.
