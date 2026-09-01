---
name: aot-ship-loop
description: "Ship a code change through the complete Art of Technology quality loop: committed feature branch, no-mistakes validation, lint and tests, pull request, Octopus Review to 4+/5, green CI, and optional post-merge container release verification. Use when the user asks to ship, gate, validate, run the full PR loop, follow no-mistakes plus Octopus, get CI passing, or prepare a change for safe deployment."
---

# aot-ship-loop

Move one scoped change from a feature branch to a verified release candidate. Compose the installed `no-mistakes` and `aot-pr-loop` skills when available; this skill controls their order and the hand-offs between them.

## Exit conditions

Report success only when:

- the intended change is committed on a feature branch;
- no-mistakes completes its review, tests, docs, lint, push, PR, and CI gates;
- the latest Octopus Review score is at least 4/5 with no unresolved critical finding;
- every required PR check is green; and
- if deployment was explicitly requested, the merged revision's artifacts are published and the deployed revision is verified.

Stop at **ready to merge** unless the user explicitly authorized merging. Merge authority does not imply deployment authority.

## 1. Establish scope

1. Read repository instructions and inspect branch, status, diff, remotes, and recent commits.
2. Confirm the change is on a feature branch and contains only the requested scope.
3. Run the relevant targeted checks and commit the intended files. Never mix unrelated existing changes into the commit.
4. Write an intent that captures the user's outcome, constraints, compatibility promises, and accepted tradeoffs. Do not reduce it to a file list.

Show the proposed commit or review-fix changes and obtain confirmation before committing when repository instructions require it.

## 2. Run no-mistakes

Start the pipeline from the feature branch:

```bash
no-mistakes axi run --intent "<complete intent>"
```

Add `--yes` only when the user has clearly granted unattended auto-fix consent.

While a run is active:

- let the pipeline own the worktree;
- do not edit, commit, abort, restart, rebase, amend, or force-push;
- inspect progress with `no-mistakes axi status`;
- answer gates through the pipeline's printed `axi respond` command; and
- accept pipeline-authored fix commits, then let it rerun the affected gates.

Do not treat a local test pass as completion. Continue through review, tests, documentation, lint, push, PR creation, and CI.

## 3. Run the Octopus PR loop

Once the PR exists, follow `aot-pr-loop` against that exact PR.

1. Fetch the PR, latest Octopus review, inline comments, and general comments. Prefer `gh-axi` over `gh` when available.
2. Parse the overall score, category scores, and every finding.
3. Read the referenced code and classify each finding as fix, false positive, or skip.
4. Before changing files, show the PR URL, scores, and proposed action for each finding; obtain user confirmation.
5. Apply the smallest valid fixes in new commits, push normally, react and reply to the relevant threads, then tag `@octopus` once for re-review.
6. Repeat until the latest score is at least 4/5. Never silently dismiss a critical finding.

Inside this loop, never force-push, squash, rebase, or amend. If a pull conflicts, stop and surface the conflict.

## 4. Verify CI and hand off merge

Wait for every required PR check. If a check fails, inspect its logs, make the smallest scoped fix with confirmation, rerun local validation, push a new commit, and return to the Octopus gate when the diff changed.

When Octopus is 4+/5 and CI is green, report:

- PR number, title, and URL;
- no-mistakes outcome;
- Octopus score and findings fixed or dismissed;
- required CI checks; and
- the exact next action: ready for user merge, or merge now if already authorized.

## 5. Optional merge and release verification

Only after explicit authorization:

1. Merge using the repository's required strategy without rewriting history.
2. Wait for `main` CI to pass.
3. If containers are published, wait for **every** required container-image job. A green health endpoint alone does not prove the intended image is live.
4. Trigger a fresh deployment only when deployment was in scope.
5. Verify the deployed commit or image digest, plus one release-specific behavior.
6. Keep private services such as GPU, database, queue, and internal model endpoints private.

If artifact publication or deployment verification fails, report the precise failed gate. Do not claim the release is live.

## Hard rules

- No force-push, squash, rebase, or amend on a shared review branch.
- No worktree edits while no-mistakes owns an active run.
- No review-fix commit without the required confirmation.
- No automatic merge or deployment without explicit authority.
- No passing claim based only on health checks or stale CI.
- No unrelated refactors or opportunistic cleanup.
