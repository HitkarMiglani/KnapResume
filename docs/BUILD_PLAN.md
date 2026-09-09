# KnapResume Build Plan

This document defines the next implementation steps for KnapResume, including planned
features, technology choices, architecture, data flow, and delivery phases.

## Current State

Completed:

- Email/password authentication with Argon2id, server-side sessions, and CSRF protection.
- Manual profile fact entry and deterministic bullet normalization.
- Job-description paste input with AI-backed structured parsing and deterministic fallback.
- Owner-scoped job-description persistence and deletion.
- Profile completeness scoring by section.

The next goal is to turn the stored profile and parsed job description into a complete,
grounded, space-constrained tailored resume.

## Product Features

### Profile Acquisition

- Upload PDF and DOCX resumes.
- Extract text and preserve the original import metadata.
- Convert resume content into sectioned source facts and atomic bullets.
- Continue supporting manual fact entry and deletion.
- Add optional GitHub project import with narrowly scoped authorization. Backlogged behind
  Phase 1 resume ingestion; see Recommended Next Slice for sequencing.

### Job Description Processing

- Accept pasted or uploaded job descriptions.
- Extract skills, keywords, seniority, role type, responsibilities, and requirements.
- Remove boilerplate and duplicate signals.
- Show parsing confidence and allow user corrections.

### Tailoring Engine

- Classify the target role and calculate section weights.
- Score every profile bullet against the job description.
- Combine semantic similarity, exact keyword overlap, and evidence quality.
- Select bullets under a one-page or two-page space budget.
- Enforce section minimums and maximums.
- Remove redundant or conflicting bullets.

### Grounded AI Rewriting

- Rewrite selected bullets for relevance and clarity.
- Preserve source facts, dates, technologies, and numeric claims.
- Link every generated bullet to its source bullet.
- Flag unsupported or unverifiable claims.
- Allow users to accept, reject, or edit generated bullets.

### ATS Validation and Feedback

- Check required JD keyword coverage.
- Validate ATS-safe structure and formatting.
- Rank the weakest profile section against the current JD and feed that ranking back into
  profile intake so the user can improve the profile before the next tailoring pass.
- Detect duplicate content and excessive keyword stuffing.
- Show an explainable score rather than an opaque single rating.

### Resume Workspace and Export

- Provide an interactive tailoring workspace.
- Let users toggle bullets and reorder sections.
- Show live page and line-budget usage.
- Preview the final resume.
- Export ATS-safe PDF and editable DOCX.
- Persist resume versions for later editing and download.

## Target Architecture

```mermaid
flowchart TD
    UI[React + TypeScript UI] --> API[FastAPI API]
    API --> AUTH[Authentication and Authorization]
    API --> PROFILE[Profile Service]
    API --> JD[JD Processing Service]
    API --> TAILOR[Tailoring Orchestrator]
    API --> EXPORT[Export Service]

    PROFILE --> DB[(PostgreSQL)]
    JD --> DB
    TAILOR --> DB
    EXPORT --> DB

    JD --> LLM[OpenAI-compatible AI Provider]
    TAILOR --> LLM
    TAILOR --> EMB[Embedding Provider]
    EXPORT --> RENDER[PDF/DOCX Renderer]

    UI -->|same-origin API calls| API
```

### Architectural Principles

- Keep the FastAPI application modular by domain rather than by generic utility type.
- Store immutable source facts separately from normalized and generated content.
- Treat AI output as untrusted data that must pass schema validation and provenance checks.
- Keep deterministic scoring, allocation, validation, and authorization in application code.
- Keep provider calls behind interfaces so models and vendors can be changed later.
- Do not send profile data to external providers until consent, retention, deletion, and
  encryption requirements are documented and implemented.
- Keep all user-owned queries scoped by authenticated user ID.

## Technology Stack

| Layer | Technology | Responsibility |
| --- | --- | --- |
| Frontend | React, TypeScript, Vite | Authentication, profile management, tailoring workspace, preview |
| UI testing | Vitest, Testing Library | Component and interaction tests |
| Backend | Python 3.13, FastAPI | HTTP API, orchestration, authorization, validation |
| Persistence | PostgreSQL 17, SQLAlchemy 2, Alembic | User data, source facts, parsed JDs, resume versions |
| Authentication | Argon2id, server-side sessions, CSRF tokens | Account and browser session security |
| AI | OpenAI-compatible Chat Completions API | Structured extraction and grounded rewriting |
| Similarity | Provider embeddings or local vector implementation | Semantic bullet/JD comparison |
| Optimization | Deterministic Python solver, then PuLP or OR-Tools if needed | Space-constrained bullet allocation |
| PDF parsing | `pypdf` | PDF text extraction |
| DOCX parsing | `python-docx` | DOCX text extraction |
| PDF export | HTML/CSS renderer or ReportLab | ATS-safe PDF output |
| DOCX export | `docxtpl` or `python-docx` | Editable document output |
| Development | Docker Compose, PostgreSQL, pytest, Ruff | Reproducible local development and quality gates |

## Pipeline

```mermaid
flowchart LR
    A[Resume Sources] --> B[Text Extraction]
    B --> C[Structured Profile Parsing]
    C --> D[Source Facts]
    D --> E[Atomic Bullets]

    F[Job Description] --> G[JD AI Parsing]
    G --> H[JD Signals]

    E --> I[Role Classification]
    H --> I
    I --> J[Candidate Scoring]
    J --> K[Line Budget Allocation]
    K --> L[Coherence and Deduplication]
    L --> M[Grounded Rewriting]
    M --> N[Provenance Verification]
    N --> O[ATS Validation]
    O --> P[Interactive Resume]
    P --> Q[PDF/DOCX Export]
```

## Data Model

```mermaid
erDiagram
    USERS ||--o{ SESSIONS : owns
    USERS ||--o{ SOURCE_FACTS : owns
    USERS ||--o{ BULLETS : owns
    USERS ||--o{ JOB_DESCRIPTIONS : owns
    USERS ||--o{ RESUME_IMPORTS : creates
    USERS ||--o{ TAILORED_RESUMES : creates
    SOURCE_FACTS ||--o{ BULLETS : normalizes
    RESUME_IMPORTS ||--o{ SOURCE_FACTS : produces
    JOB_DESCRIPTIONS ||--o{ TAILORED_RESUMES : targets
    TAILORED_RESUMES ||--o{ TAILORED_BULLETS : contains
    BULLETS ||--o{ TAILORED_BULLETS : grounds

    USERS {
        uuid id PK
        string email
        string password_hash
        datetime created_at
    }
    RESUME_IMPORTS {
        uuid id PK
        uuid user_id FK
        string filename
        string file_type
        string status
        datetime created_at
    }
    SOURCE_FACTS {
        uuid id PK
        uuid user_id FK
        uuid import_id FK
        string section
        text raw_text
        datetime created_at
    }
    BULLETS {
        uuid id PK
        uuid source_fact_id FK
        uuid user_id FK
        string section
        text normalized_text
        string_array skill_tags
        datetime created_at
    }
    JOB_DESCRIPTIONS {
        uuid id PK
        uuid user_id FK
        text raw_text
        string_array skills
        string_array keywords
        string seniority
        string role_type
        datetime created_at
    }
    TAILORED_RESUMES {
        uuid id PK
        uuid user_id FK
        uuid job_description_id FK
        string status
        int page_target
        float ats_score
        datetime created_at
    }
    TAILORED_BULLETS {
        uuid id PK
        uuid tailored_resume_id FK
        uuid bullet_id FK
        text rewritten_text
        float relevance_score
        boolean is_grounded
        int estimated_lines
        int display_order
    }
```

## Tailoring Request Flow

```mermaid
sequenceDiagram
    actor User
    participant UI as React UI
    participant API as FastAPI
    participant DB as PostgreSQL
    participant AI as AI Provider
    participant Solver as Allocation Engine

    User->>UI: Select JD and page target
    UI->>API: POST /api/tailor/generate
    API->>DB: Load JD and owned bullets
    DB-->>API: JD signals and profile candidates
    API->>AI: Request role classification and candidate signals
    AI-->>API: Validated structured scores
    API->>Solver: Allocate bullets under line budget
    Solver-->>API: Selected bullet IDs and section allocation
    API->>AI: Rewrite selected bullets with source facts
    AI-->>API: Structured rewritten bullets
    API->>API: Verify provenance and ATS constraints
    API->>DB: Store resume version and bullet links
    DB-->>API: Resume version
    API-->>UI: Tailored resume and diagnostics
    UI-->>User: Interactive workspace and preview
```

## Implementation Phases

```mermaid
gantt
    title KnapResume Delivery Roadmap
    dateFormat YYYY-MM-DD
    section Foundation
    Re-run frontend quality gates       :done, gates, 2026-09-10, 1d
    Define AI data governance ADR        :gov, after gates, 3d
    section Profile Ingestion
    PDF/DOCX upload and extraction       :ingest, after gov, 5d
    Structured resume fact parsing       :parse, after ingest, 5d
    Import review and rollback UI        :review, after parse, 3d
    section Tailoring Core
    Role classification                  :role, after review, 3d
    Candidate scoring                    :score, after role, 5d
    Line budget allocator                :allocate, after score, 5d
    Deduplication and coherence          :dedup, after allocate, 3d
    section Generation
    Grounded rewriting                  :rewrite, after dedup, 5d
    Provenance and ATS validation        :validate, after rewrite, 5d
    Weakest-section feedback loop        :feedback, after validate, 3d
    section Product
    Tailoring workspace                  :workspace, after feedback, 7d
    PDF and DOCX export                  :export, after workspace, 5d
```

### Phase 0: Quality and Governance

- Re-run backend and frontend quality gates.
- Add an ADR for AI provider retention, consent, deletion, and logging boundaries.
- Add provider timeout, retry, rate-limit, and error telemetry policy.
- Keep synthetic data as the default test fixture.

### Phase 1: Resume Ingestion

- Add `resume_imports` and import status fields.
- Add authenticated `POST /api/profile/import` multipart endpoint.
- Validate file type, size, content, and ownership.
- Extract PDF/DOCX text without logging uploaded content.
- Parse extracted text into reviewable source facts.
- Make import deletion remove dependent facts and bullets.

### Phase 2: Tailoring Scoring

- Add role-type classification with deterministic fallback.
- Implement keyword overlap and semantic similarity scoring.
- Expose a preview endpoint before generation.
- Store score explanations so users can understand selection decisions.

### Phase 3: Space-Constrained Allocation

- Define page templates and line-budget rules for the one-page baseline budget.
- Estimate bullet line usage deterministically.
- Implement 0/1 allocation with section constraints.
- Add tests for budget overflow, required sections, and tie-breaking.
- Add coherence and duplicate detection after selection.
- A two-page budget is out of scope for this phase; propose it as a separate ADR if needed.

### Phase 4: Grounded Generation and ATS Safety

- Rewrite only selected bullets and pass source facts as grounding context.
- Require structured AI output for every rewrite.
- Verify dates, technologies, metrics, and entities against source content.
- Flag uncertain claims rather than silently accepting them.
- Add ATS keyword and formatting diagnostics.
- Compute the JD-specific weakest profile section and expose it as a feedback signal that
  the profile intake UI can surface for iterative improvement.

### Phase 5: Workspace and Export

- Add `/tailor/:jobDescriptionId` workspace route.
- Display selected bullets, rejected candidates, budget usage, and warnings.
- Support user toggles, ordering, edits, and regeneration.
- Persist named resume versions.
- Add PDF and DOCX exports with deterministic templates.
- Add end-to-end tests for generation, editing, and download.

## Initial API Surface

| Endpoint | Purpose |
| --- | --- |
| `POST /api/profile/import` | Upload and parse a PDF/DOCX resume |
| `GET /api/profile/imports` | List the user's imports |
| `DELETE /api/profile/imports/{id}` | Delete an import and derived facts |
| `POST /api/tailor/score` | Score profile bullets against a JD |
| `POST /api/tailor/generate` | Allocate and generate a tailored resume |
| `GET /api/tailor/{id}` | Retrieve a tailored resume version |
| `PATCH /api/tailor/{id}` | Save user edits and ordering |
| `POST /api/tailor/{id}/export` | Generate PDF or DOCX output |

## Quality Gates

- Every endpoint has authentication, ownership, validation, and error-path tests.
- AI responses use schema validation and bounded input/output sizes.
- Generated claims retain source-bullet provenance.
- Deterministic fallback behavior exists for extraction and scoring where practical.
- Allocation never exceeds the configured page budget.
- Uploaded content and provider payloads are excluded from logs.
- Backend: `pytest` and `ruff check` pass.
- Frontend: `npm test -- --run` and `npm run build` pass.
- Migration tests cover account deletion and owner isolation.

## Recommended Next Slice

Implement **Phase 0 followed by Phase 1**. Resume ingestion creates the missing bridge between
the existing manual profile workflow and the automated tailoring pipeline. It should be built
before scoring or rewriting so all later features operate on realistic, provenance-linked
profile data.

GitHub project import is deferred behind Phase 1 (PDF/DOCX ingestion) and is not yet assigned
a phase; revisit it once Phase 1 ships so it doesn't silently drop out of scope.
