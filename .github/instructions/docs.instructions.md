---
description: "Docs and ADR conventions — applies when editing docs/, CHANGELOG.md, or .github/copilot-instructions.md"
applyTo: "docs/**,CHANGELOG.md,.github/copilot-instructions.md"
---

# Docs conventions

- `docs/STATUS.md` reflects *current* state only — done / in progress / next steps /
  blockers. Don't let it accumulate history; that belongs in `CHANGELOG.md` (user-facing)
  or `docs/adr/` (decision rationale).
- Any decision that is non-trivial or hard to reverse (tech stack, storage engine, LLM
  provider, schema shape, algorithm trade-off) gets an ADR in `docs/adr/`, numbered
  sequentially. Never edit an old ADR's decision in place — supersede it with a new one.
- `docs/ARCHITECTURE.md` is the full pipeline reference; `.github/copilot-instructions.md`
  holds only the condensed version. If they'd drift out of sync, update both in the same
  change.
- When a section of `.github/copilot-instructions.md` becomes stale (e.g. stack decided,
  new convention adopted), update it in the same PR that makes it stale — don't defer.
