---
name: aot-ci-workflows
description: "Cut wasted GitHub Actions runs in a repo and migrate it onto Art of Technology's shared reusable workflows (node-ci, dotnet-ci, docker-build, release), in two gated stages. Use when the user asks to speed up CI, stop wasted or duplicate runs, add concurrency or paths-ignore, skip CI on drafts, adopt the org's reusable workflows, act as the repo agent for CI adoption, hands over a repo-agent brief, or asks what the shared workflows are, what inputs they take, or how the merge queue interacts with CI. Not for defining how releases move between environments (use aot-release-lifecycle) or for working PR review feedback (use aot-pr-loop)."
---

# aot-ci-workflows

You are the code agent for one repo. The org agent owns org-level CI in `Art-of-Technology/.github`. You own this repo's `.github/workflows` only. Open PRs, never merge them. Drive each PR through `aot-pr-loop` until Octopus scores 4/5 or higher, stopping before its merge step. Report in plain text: done, PR link, blockers.

## Never do

- Create or edit runner groups, GitHub Apps, or org secrets.
- Change branch rulesets or merge queue settings.
- Edit `Art-of-Technology/skills` or `Art-of-Technology/.github`. Gaps go in a comment on the ci-adoption issue.
- Open more than one PR per stage.
- Change job logic, runners, or secrets in stage 1.

## Stage 1: stop wasted runs. Do now.

Goal: no run for docs-only changes, no run for drafts, no stale run surviving a new push.

For every file under `.github/workflows`:

1. **Concurrency** keyed on workflow and ref, cancelling superseded runs:
   ```yaml
   concurrency:
     group: ${{ github.workflow }}-${{ github.ref }}
     cancel-in-progress: true
   ```
   Tag refs are unique, so release workflows never cancel each other. For a push-to-main deploy whose deploy script is not safe to interrupt, set `cancel-in-progress: false` and say so in the PR.

2. **paths-ignore** on `push` branch triggers and on `pull_request`:
   ```yaml
   paths-ignore:
     - '**.md'
     - 'docs/**'
     - '**.png'
     - '**.jpg'
     - '**.jpeg'
     - '**.gif'
     - '**.svg'
     - '**.webp'
   ```
   Never under `tags:`. Path filters do not apply to tag pushes.

3. **PR trigger types**, the merge queue event, and a draft guard on every job:
   ```yaml
   on:
     pull_request:
       types: [opened, synchronize, reopened, ready_for_review]
     merge_group:
   jobs:
     test:
       if: github.event_name != 'pull_request' || github.event.pull_request.draft == false
   ```
   `merge_group` is what lets required checks run once the merge queue is on. Path filters do not apply to it, and it has no draft state, so the guard above already passes it through.

Required-check trap: if a job is a required status check in the branch ruleset, `paths-ignore` leaves docs-only PRs stuck on "Expected". Check first:

```bash
gh api "repos/{owner}/{repo}/rules/branches/main" --jq '.[] | select(.type=="required_status_checks") | .parameters.required_status_checks[].context'
```

For any workflow that owns a required check, either keep it free of `paths-ignore` or add a twin workflow with the same job names that runs only on the ignored paths and exits 0. Say which you did in the PR body.

Verify before opening the PR:

```bash
for f in .github/workflows/*.y*ml; do
  grep -q '^concurrency:' "$f"        || echo "missing concurrency: $f"
  grep -q 'paths-ignore'   "$f"       || echo "missing paths-ignore: $f (fine if tag-only)"
  grep -q 'ready_for_review' "$f"     || echo "missing PR types: $f (fine if no pull_request trigger)"
  grep -q 'pull_request.draft' "$f"   || echo "missing draft guard: $f (fine if no pull_request trigger)"
done
```

One PR titled **`ci: stop wasted runs`**. Body lists every workflow touched and each exception taken. Then run `aot-pr-loop` to 4/5, without merging. Report the PR link and the workflows touched.

## Stage 2: adopt org reusable workflows. Wait for the handoff.

Start only when an issue labelled `ci-adoption` exists in this repo. Check:

```bash
gh issue list --label ci-adoption --state open --json number,title,url
```

None: stop after stage 1 and report that stage 2 is waiting on the org agent. The issue names the reusable workflows in `Art-of-Technology/.github` (`node-ci`, `dotnet-ci`, `docker-build`, `release`) and their inputs. What each one does and accepts is in `references/reusable-workflows.md`; the issue wins where they differ.

1. Replace local CI workflows with `workflow_call` jobs into the shared ones this repo needs:
   ```yaml
   jobs:
     ci:
       uses: Art-of-Technology/.github/.github/workflows/node-ci.yml@main
       with:
         node-version: '22'
         turbo-filter: 'web...'
         runner-labels: '["self-hosted","dc-1"]'
       secrets: inherit
   ```
2. Set inputs from the issue: node version, dotnet version, turbo filter, runner labels. Route test, build, and docker jobs to the `dc` runner labels named in the issue. Keep lint and typecheck on `ubuntu-latest`.
3. Keep repo-specific steps (migrations, e2e, seed data) as extra jobs alongside the call. Never fork or copy a shared workflow into the repo.
4. Verify release triggers follow `aot-release-lifecycle`: push to `main` deploys staging, `vX.Y.Z-rc.N` tags deploy UAT, `vX.Y.Z` tags promote the RC image to production with no rebuild.
5. Where a shared workflow lacks something this repo needs, comment on the ci-adoption issue. Do not patch around the gap locally.

One PR titled **`ci: adopt org reusable workflows`**. Then `aot-pr-loop` to 4/5, without merging. Report lines removed, inputs chosen, gaps raised on the issue.

## Report format

Plain text, three lines minimum:

```
done: <stage> <what changed>
pr: <url>  octopus: <score>/5
blockers: <none | what and who owns it>
```
