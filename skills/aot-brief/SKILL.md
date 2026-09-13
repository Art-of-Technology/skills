---
name: aot-brief
description: >-
  Shape agent replies for ADHD-friendly scanning and fewer output tokens.
  Apply to all replies when enabled, including coding updates and decisions.
  Trigger on "brief", "terse", "short answer", "status", "what changed",
  or /aot-brief. Covers Claude Code and Codex conversational output.
metadata:
  version: "0.2.0"
---

# aot-brief

Reduce output tokens by 30% or more without losing material facts.
Treat this as a target to measure, never a guaranteed saving.
Preserve correctness, uncertainty, verification evidence, and required safety information.
When enabled, this shape supersedes actionable-output's conflicting formatting rules.

## Output shape

Every reply uses these blocks in order. Omit empty blocks.
Repeat inline labels for multiple lines; labels count toward line limits.

- DONE: One line per change or answer. Start with a verb.
  Include a file path when relevant. Never imply unfinished work succeeded.
- NEXT: Give one action, or the literal `NEXT: none`.
- BLOCKED: State the single thing needed to continue.
- DECIDE: Give numbered options, maximum three; mark one `(default)`.
  Put each option on its own `DECIDE:` line.
  End with one `DECIDE:` question, then stop for the answer.
  A default is a recommendation, never permission to act.

## Compression rules

Use caveman-lite compression without sacrificing readable sentences.

- No greeting, preamble, request recap, or closing offer.
- No play-by-play of tool calls. Report outcomes or meaningful next actions.
- No hedging words. State facts. Mark guesses with `unverified:`.
  Preserve uncertainty explicitly; never turn an estimate into a fact.
- Full sentences are allowed. No fragments. Maximum 12 words per line.
  Imperative sentences count. `NEXT: none` and option labels are exceptions.
- Diffs only: report changes, new findings, or answers to the question.
  Never echo files read. Never paste full files.
- Hard cap: eight physical lines, including labels and blank lines.
  Count whitespace-separated words, including labels, numbers, and paths.
- Put overflow in a task-specific file under `docs/agent-output/`.
  Return its path plus a three-line summary within eight lines.
  Use DONE for the path and summary; retain actionable blocks as needed.
  Exclude secrets. If writing is unavailable, state the blocker honestly.

## Exceptions

These override the cap when necessary.

- Destructive action: send one standalone `Warning:` line; wait for explicit yes.
  State the destructive effect and request yes before proceeding.
- Surprising side effect: allow one `Note:` line beyond eight regular lines.
  Keep twelve words per line for notes and warnings.
  Put notes before the final DECIDE question; never continue after it.
- Code, commits, and PR descriptions are written normally; caps do not apply.
  Keep surrounding chat compressed. Never paste full files.
- Higher-priority instructions and explicitly requested deliverables take precedence.

## Before and after

Before: 25 lines, with repeated framing but five material facts.

```text
I have finished working on the login bug you reported.
Here is a detailed update about what changed.
The main change is in src/auth.ts.
That file contains the login handling code.
I updated its expired-token handling.
Expired tokens now return HTTP 401.
That is the expected status for this case.
I also added a regression test.
The test is in tests/auth.test.ts.
It covers the expired-token case.
This protects the behavior against regressions.
After making the changes, I ran the tests.
All 18 tests passed.
There were no failing tests in that run.
The test run therefore completed successfully.
I checked the lint results as well.
Lint passed.
There were no lint failures.
That completes the implementation and local verification.
The changes are ready for review.
The remaining action is reviewing the diff.
Please review the diff next.
You can inspect the changes before proceeding.
That is everything for this update.
Let me know if you need anything else.
```

After: five lines preserving the change, test, results, and next action.

```text
DONE: Return HTTP 401 for expired tokens in src/auth.ts.
DONE: Add expired-token regression coverage in tests/auth.test.ts.
DONE: Pass all 18 tests.
DONE: Pass lint.
NEXT: Review the diff.
```

## Codex notes

Keep this shape in prompt text only: SKILL.md or referenced instructions.
Do not install hooks or use proxy rewrites to reshape replies.
Do not change reasoning effort settings; this skill controls output only.
Discovery alone does not enable this skill for every conversation.
For persistent use, reference this skill in the agent's standing instructions.
