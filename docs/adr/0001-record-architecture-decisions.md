# ADR 0001: Record architecture decisions

## Status

Accepted

## Context

This project evolves across many sessions/contributors, but only one person works at a
time. Decisions (tech stack, storage choices, algorithm trade-offs) need to survive
outside any one person's memory or chat session, without bloating `docs/STATUS.md` (which
is for *current* state, not history) or `.github/copilot-instructions.md` (which is for
*stable* conventions, not decision rationale).

## Decision

We record every non-trivial, hard-to-reverse decision as an ADR (Architecture Decision
Record) in `docs/adr/`, numbered sequentially (`0001-...`, `0002-...`), using this
template:

```
# ADR NNNN: <title>

## Status
Proposed | Accepted | Superseded by ADR NNNN

## Context
<what problem forced this decision>

## Decision
<what was decided>

## Consequences
<what this makes easier/harder, what to revisit later>
```

## Consequences

- Any new session/contributor can read `docs/adr/` to understand *why* the system looks
  the way it does, without re-deriving it or re-reading the whole codebase.
- ADRs are append-only history; to change a decision, add a new ADR that supersedes the
  old one rather than editing it in place.
