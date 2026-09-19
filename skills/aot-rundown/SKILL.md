---
name: aot-rundown
description: Give a concise whole-project status rundown from the current repository and GitHub state. Use for /aot-rundown, project backlog, pull requests, completed work, or release status. For a recap of the current session, use aot-rundown-current.
---

# aot-rundown

Inspect the current project's instructions, local Git state, and relevant planning or release documents. Use available repository and GitHub tools (connectors, APIs, or CLI) to check issues, project status, pull requests, recent activity, and releases. Do not rely only on conversation history. This workflow is read-only and requires no particular model provider or agent-specific tool.

Read and apply [aot-brief's output shape and compression rules](../aot-brief/SKILL.md) for this response only; preserve any previously enabled style afterwards. Do not create overflow files for this read-only workflow. Classify findings using these statuses; section headings are optional:

- **Backlog:** Issues/tasks waiting to be worked on.
- **In Progress:** Work with current evidence of active progress, such as an in-progress project status or active pull request; assignment alone is not proof.
- **Completed:** Recently finished work. Note uncertain release status; closing an issue or merging a pull request does not prove release readiness or deployment.
- **Waiting for Release:** Completed work confirmed ready but not yet released, based on the project's release process and available checks.
- **Recently Released:** Work included in recent verified releases; include the version or date when available and distinguish release publication from confirmed deployment.

For each item, include the title and issue/task number (or PR number when there is no issue), owner if known, current status, and a key blocker or next step only when relevant. Link the issue, PR, or release when available. Do not invent missing numbers or owners.

Prioritise important and recent items. Use the requested time window; otherwise use the past 14 days for recent activity and state that window briefly. Report each item once under its most specific status. Keep each item to one short line where practical.

Omit empty categories unless requested. Say "None found" only when checked. If access or evidence is missing, say "Unknown" and briefly identify the gap. Report conflicting or stale evidence rather than guessing.
