# Agent instructions

This repo holds shared agent skills. Each folder under skills/ is one skill with a SKILL.md entry point.

When asked to run a named skill, read skills/<name>/SKILL.md and follow it exactly. Load files under references/ only when the SKILL.md points to them.

Hard rules across all skills:
- No force-push, no squash, no rebase, no amend on shared branches.
- Show planned changes and get confirmation before committing.
- Smallest change that addresses the issue. No piggyback refactors.
