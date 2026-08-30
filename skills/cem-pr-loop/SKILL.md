---
name: cem-pr-loop
description: Address Octopus Review feedback on a GitHub pull request in a tight loop until the PR earns a 4+/5 quality score. Use this skill whenever the user asks to "run the pr loop", "run cem-pr-loop", "check my PR", "address Octopus feedback", "fix the review findings", "respond to review comments", "loop until 4/5", "get the PR to passing", or anytime there is an open PR that needs Octopus Review findings worked through iteratively. Also use when the user references review threads, finding severities (🔴🟠🟡🔵), or wants to react to and resolve Octopus comments. The skill drives gh CLI interactions, fix application, reactions, thread replies, and re-review notification.
---

# cem-pr-loop

Drive a GitHub PR through Octopus Review feedback to a 4+/5 score. Read the open PR for the current branch, parse every Octopus finding, apply the valid fixes, push, react to and reply to threads, then ping Octopus for re-review. Repeat until the quality gate passes.

## Quality gate

- Target: 4+/5 overall score from Octopus Review.
- Only proceed past this loop once the score lands at 4 or above.
- If stuck at 3/5 and the remaining findings are all false positives, surface the situation to the user and ask for a call.
- Never silently dismiss 🔴 findings. They get fixed, or the user explicitly approves dismissal.

## Rules of engagement

- Ignore findings that are genuinely false positives. Read the actual code first before deciding.
- React 👎 on each false-positive comment with a short reason.
- React 👍 on each valid, useful suggestion you fix.
- Reply in the relevant thread describing the fix after you apply it.
- Resolve the thread if the platform supports it. Otherwise leave a reply that clearly states the issue is addressed.
- After every push, post a single PR comment tagging @octopus so it re-runs review.
- Never force-push. Always plain `git push`.
- Never squash, rebase, or amend existing commits while inside the loop.

## Step 1: Find the PR

Get the current branch and look up its open PR.

```bash
git branch --show-current
gh pr view --json number,title,state,url,headRefName,reviewDecision
```

If `gh pr view` returns nothing, fall back to listing your open PRs and pick the right one:

```bash
gh pr list --author "@me" --state open --json number,title,headRefName,url
```

If no open PR exists, tell the user and stop.

If `state` is `MERGED` or `CLOSED`, stop immediately. This loop sometimes gets triggered by a stale wakeup scheduled by an earlier sub-agent before the parent merged. There is nothing to do on a closed PR. Do not fetch reviews, do not comment, do not reschedule.

## Step 2: Fetch all review feedback

Pull three things: reviews, inline comments, general PR comments.

```bash
gh api repos/{owner}/{repo}/pulls/{number}/reviews \
  --jq '.[] | {id, state, body, user: .user.login, submitted_at: .submittedAt}'

gh api repos/{owner}/{repo}/pulls/{number}/comments \
  --jq '.[] | {id, path, line, body, user: .user.login, created_at}'

gh api repos/{owner}/{repo}/issues/{number}/comments \
  --jq '.[] | {id, body, user: .user.login, created_at}'
```

Check the latest Octopus review body. If it says "0 findings", everything is resolved. Read the score. If it is 4+/5, the PR is ready to merge and you can jump to Step 9.

## Step 3: Parse Octopus findings

From the most recent Octopus review body, extract:

- Overall score (e.g. "2/5").
- Category scores: Security, Code Quality, Performance, Error Handling, Consistency.
- The findings table: severity icon (🔴🟠🟡🔵), file path, title, description.
- Any inline review comments tied to specific lines.

## Step 4: Assess each finding

Severity drives default action, but never apply blindly. Read the file first, because Octopus sometimes references stale context.

- 🔴 Critical: fix unless the user explicitly waives it.
- 🟠 Warning: fix unless it is a clear false positive.
- 🟡 Suggestion: fix when reasonable.
- 🔵 Info: acknowledge. Fix if trivial.
- False positive: prepare a one-line reason for the 👎 reaction.

The reason this matters: applying a wrong "fix" because the reviewer misread the code creates a bigger problem than the original finding. Confirm the finding maps to the real code state before changing anything.

## Step 5: Present the plan and confirm

Before touching any files, show the user:

- PR title, number, and URL.
- Current Octopus score and category breakdown.
- A table of findings with proposed action per row: fix / false positive / skip.

Ask the user to confirm before proceeding. The user may downgrade or upgrade individual actions.

## Step 6: Apply the fixes

```bash
git checkout <branch>
git pull origin <branch>
```

Read each file referenced by the findings. Apply changes:

- Code suggestions with an exact patch: apply as suggested.
- Style or refactor notes: minimal change addressing the feedback.
- Bugs: fix as described.
- Questions: if the answer implies a change, make it. Otherwise note it for the reply.

Stage and commit with a message that lists what changed:

```bash
git add <changed-files>
git commit -m "fix: address Octopus review feedback on #<PR-number>

- <change 1>
- <change 2>
- <change 3>
"
git push origin <branch>
```

## Step 7: Respond to the review comments

For each finding addressed:

- React 👍 on the inline comment or review body for valid findings you fixed.
- React 👎 on each false positive and reply with the reason.
- Reply to each inline thread with a short note describing the fix.
- Resolve the thread if the API supports it.

Then post a single PR-level comment to trigger re-review:

```
@octopus Fixes applied, ready for re-review.

## Changes made
| # | Finding | Action |
|---|---------|--------|
| 1 | <finding> | Fixed in <commit-sha> |
| 2 | <finding> | False positive: <reason> |
```

## Step 8: Wait for re-review

Check whether Octopus posted a new review:

```bash
gh api repos/{owner}/{repo}/pulls/{number}/reviews --jq '. | length'
```

If the review count has not increased, Octopus has not run yet. The user can trigger it manually with `octopus review <number>`. Report current status and the latest score.

If a new review landed, go back to Step 2 with it.

## Step 9: Merge and clean up

Only when the quality gate (4+/5) is met:

```bash
gh pr merge <number> --merge --delete-branch
git checkout master
git pull
git branch -d <branch-name>
```

Close any related issues that did not auto-close.

## Step 10: Report

Print a final status block:

- PR number, title, URL.
- Previous score to current score.
- Count of findings fixed vs dismissed.
- Whether the 4+/5 gate is met.
- Next step: merged / waiting on re-review / more fixes pending.

## Hard rules to never break

- No force-push.
- Show the planned fixes and get confirmation before committing.
- Make the smallest change that addresses each finding. Do not piggyback unrelated refactors.
- When in doubt, ask the user rather than guessing.
- Do not squash, rebase, or amend existing commits.
- If `git pull` reports merge conflicts, stop and surface them to the user.
