# ADR 0005: Third slice uses PDF/DOCX text extraction and structured parsing

## Status

Accepted

## Context

With JD parsing and completeness scoring implemented (ADR 0004), the next major stage in `docs/ARCHITECTURE.md` is **Profile Acquisition (stage 1)**. Currently, the application only supports manual entry of synthetic profile facts. The product requirements outline automated PDF/DOCX resume ingestion and structured fact extraction as the bridge enabling realistic tailoring pipeline testing.

This next vertical slice requires:
1. Support for PDF (`.pdf`) and Word Document (`.docx`) file uploads.
2. In-memory, non-logging text extraction from these binaries using reliable python packages.
3. Structured parsing of extracted text into sectioned source facts and normalized, provenance-linked bullets.
4. Support for the deletion of imports, which must cascade-delete all derived facts and bullets.
5. Integration with the existing auth-scoped, same-origin, CSRF-protected React/FastAPI scaffold.

## Decision

We will implement the third vertical slice as **Resume binary upload → Local text extraction → AI structured profile parsing (with deterministic fallback) → Atomic bullet normalization and persistence**, structured as follows:

### 1. External dependencies
- **PDF Extraction**: `pypdf` (a lightweight, modern, and pure-python PDF parser).
- **DOCX Extraction**: `python-docx` (the standard python package for reading OpenXML `.docx` files).
Both dependencies will be added using command `uv add`.

### 2. Database Schema
We introduce a new `resume_imports` table:
- `id`: UUID primary key.
- `user_id`: UUID foreign key to `users.id` (`ON DELETE CASCADE`), ensuring owner isolation.
- `filename`: String (the user's original filename).
- `file_type`: String (e.g., `pdf` or `docx`).
- `status`: String with values `processing` | `completed` | `failed`. Since we choose to perform parsing synchronously (see below), this status primarily serves as a point-in-time record for listings and future asynchronous growth.
- `created_at`: DateTime.

We alter the `source_facts` table to add a nullable foreign key:
- `import_id`: UUID foreign key to `resume_imports.id` (`ON DELETE CASCADE`), nullable=True (to support manual fact entries).

### 3. Synchronous Binary Processing
To keep the architecture simple and aligned with the "Prevent over-engineering" principle, parsing will run synchronously inside the POST API call handler. A background task queue (like Celery or Redis) is deferred until scale requirements demand it. To mitigate timeout risks, a file size limit of **5MB** is enforced.

### 4. Text Extraction and Validation
- **Upload Endpoint**: `POST /api/profile/import` taking a `multipart/form-data` file upload.
- **Validation**: Enforce extension-to-mime-type alignment. Only `.pdf` (matching `application/pdf`) and `.docx` (matching `application/vnd.openxmlformats-officedocument.wordprocessingml.document`) are accepted. Reject files exceeding 5MB.
- **Privacy Boundary**: Extracted text and raw binary bytes are never stored on disk, never logged to terminal/files, and are processed entirely in memory.

### 5. Structured Parsing (AI + Fallback)
- **AI Parser**: Uses the same OpenAI-compatible Chat Completions configuration (`AI_API_KEY`, etc.) introduced in ADR 0004. Instructs the model to output a strict JSON array of facts, each containing raw text and one of the four sections: `experience`, `project`, `education`, `skill`.
- **Local Fallback Parser**: Parses plain text lines. Detects headers (e.g. "Experience", "Projects", "Education", "Skills") via regex keyword matching to set the target section context, and extracts non-empty lines as individual facts.
- **Normalization**: Every extracted fact automatically goes through the existing `normalize_fact()` logic from `app/normalization.py` to produce a corresponding `Bullet` in the database.

### 6. API Service Endpoint Surface
- `POST /api/profile/import`: Ingests binary, extracts text, writes `resume_imports` record, parses facts & bullets, and returns list of created bullets.
- `GET /api/profile/imports`: Lists metadata for all `resume_imports` owned by the user.
- `DELETE /api/profile/imports/{id}`: Deletes an import record. Cascade-deletes dependent `source_facts` and `bullets` in a single transaction.

### 7. Frontend UI Integration
- Add an "Import Resume" section to `ProfilePage.tsx` with clear file drop/selection constraints.
- Display uploaded imports as a sub-list (showing filename, upload date, status, and a delete button).
- Reloading the page or importing automatically updates both the imports list and the active bullets list.

## Consequences

- The application can now ingest standard professional resumes directly, providing a high-fidelity input vector for subsequent pipeline phases.
- Deletion of an import cleanses all derived data automatically due to `ON DELETE CASCADE` foreign keys.
- Processing remains fast, local, and synchronous, requiring no extra worker infrastructure.
- Zero-egress rules are respected: uploaded resumes do not touch local disk, and only extracted text from the profile upload is sent to the LLM (when configured) under the existing metadata consent boundaries.
