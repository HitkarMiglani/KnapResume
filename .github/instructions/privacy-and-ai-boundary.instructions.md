---
description: "Data Privacy and AI Provider Boundary Conventions — applies to AI client code, logging, routing, and binary processors"
applyTo: "backend/app/config.py,backend/app/jd_parsing.py,backend/app/resume_parsing.py,backend/app/routers/**,backend/app/dependencies.py"
---

# Data Privacy and AI Integration Boundary Instructions

These instructions define the strict rules for handling confidential user data, processing uploads, invoking external AI endpoints, and logging.

## 1. Upload & Text Extraction Boundaries
- **In-Memory Only**: Raw binary file uploads (PDF, DOCX, etc.) and extracted plain-text strings must stay in-memory (`io.BytesIO`). They must *never* be written to local system files, temporary folders, or cached on disk.
- **Maximum File Sizings**: Always enforce a maximum request payload size of **5MB** on file endpoints on both frontend client forms and backend validation routes.
- **Explicit Formats**: Only accept standardized `.pdf` (matching `application/pdf`) and `.docx` (matching `application/vnd.openxmlformats-officedocument.wordprocessingml.document`) formats. Maintain strict validation; reject extensions that masquerade as valid binaries.

## 2. External AI Egress Boundaries
- **Consent Checks**: Only invoke external AI providers when configured (`settings.ai_api_key` is present) and when data egress boundaries are satisfied.
- **Payload Minimization**: Send *only* the specifically required text segments (e.g. the specific bullet or job description) in the prompt messages. Never attach raw user identifiers, sessions, tokens, IP addresses, or metadata.
- **Enforced Timeouts**: All remote API requests must adhere to explicit timeouts (`settings.ai_timeout_seconds` or equivalent). Do not let remote connections hang or block event loop threads.
- **Safety Fallbacks**: Always provide robust, local, deterministic fallback mechanisms (regex, word lists) to support offline test suites and low-connectivity states.

## 3. Safe Logging and Redaction
- **No Credentials**: Never print, dump, or write to standard out (or files) any of the following fields:
  - Database URLs, usernames, passwords.
  - Authentication tokens, cookies, CSRF tokens, session keys, API keys.
  - User credentials (plain-text passwords, email addresses, phone numbers, or identity cards).
  - Raw binary stream representations, extracted unstructured documents, or vendor API request/response payloads.
- **Redacted Exceptions**: Ensure catch-all `Exception` block tracebacks do not leak any variable states containing raw user text or key variables. Redact any sensitive objects before raising.
