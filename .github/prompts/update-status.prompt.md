---
description: "End-of-session handoff: update docs/STATUS.md (and an ADR if a non-trivial decision was made) so the next session/contributor doesn't need to re-read the codebase."
---

Review the changes made in this session and update `docs/STATUS.md`:

1. Update "Last updated" date and "Current phase".
2. Move finished items from "In progress"/"Next steps" into "Done".
3. Add any new "Next steps", "Known open questions", or "Blockers" that emerged.
4. If a non-trivial or hard-to-reverse decision was made this session (tech stack choice,
   storage/schema choice, algorithm trade-off), create a new ADR in `docs/adr/` following
   the template in `docs/adr/0001-record-architecture-decisions.md`, and link it from
   `docs/STATUS.md`.
5. If the session made a notable user-facing or operational change, add a bullet to
    `CHANGELOG.md` under `[Unreleased]`; do not add entries for internal planning churn.

Keep every edit terse — this file is read at the start of the *next* session instead of
re-reading the whole codebase, so prioritize signal over prose.
