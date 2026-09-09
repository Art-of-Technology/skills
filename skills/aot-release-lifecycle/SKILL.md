---
name: aot-release-lifecycle
description: Enforce the trunk-based release lifecycle across environments. main merges deploy to staging, vX.Y.Z-rc.N tags promote to UAT, vX.Y.Z tags release to production. Use this skill whenever the user asks to "cut a release", "promote to UAT", "tag an RC", "release to production", "prepare a release", "hotfix production", "roll back a release", "run aot-release-lifecycle", or mentions release candidates, semver tags, staging/UAT/production promotion, release branches, changelogs, or the release process. Also trigger when setting up CI/CD pipelines, GitHub Actions release workflows, environment promotion gates, or reviewing whether a branch or tag follows the release convention. Even if the user does not name the skill, use it for any question about how code moves from a branch to an environment.
---

# Release Lifecycle: main → staging → UAT → production

This skill defines how code moves through environments. Follow it exactly. Never deploy to an environment through any other path.

## The model in one table

| Environment | Trigger | Artifact | Purpose |
|---|---|---|---|
| staging | Merge to `main` | Build from `main` HEAD | Continuous integration testing, latest work |
| UAT | Tag `vX.Y.Z-rc.N` | Build from the tagged commit | Business acceptance, stakeholder sign-off |
| production | Tag `vX.Y.Z` | Same artifact as the approved RC | Live traffic |

Core rule: the production tag must point to the same commit as the last approved RC tag. Promote artifacts, not branches. Never rebuild between UAT and production.

## Branch rules

- `main` is the only long-lived branch. Protect it. Require PR review and green CI.
- Feature branches: `feature/<short-name>` or `fix/<short-name>`, branched from `main`, merged back via PR. Squash merge. Delete after merge.
- No `develop` branch. No long-lived `release/*` branches unless a release needs stabilization while `main` moves on (see Stabilization below).
- Every merge to `main` auto-deploys to staging. If a change is not ready to be visible on staging, gate it behind a feature flag, not a branch.

## Tag rules

Use semver. Tags are immutable. Never delete or move a published tag.

- RC tags: `v1.4.0-rc.1`, `v1.4.0-rc.2`, ... Each RC increments the `-rc.N` suffix.
- Release tags: `v1.4.0`. Created only after an RC with the same base version passes UAT.
- Tag annotated, not lightweight:

```bash
git tag -a v1.4.0-rc.1 -m "RC1 for 1.4.0: <one-line summary>"
git push origin v1.4.0-rc.1
```

- Version bump rules: MAJOR for breaking API or schema changes, MINOR for features, PATCH for fixes only.

## Standard release flow

Work backwards from the production goal. Confirm each gate before the next step.

1. Confirm `main` is green on staging. Check CI status and smoke tests.
2. Update version metadata (package.json, .csproj, CHANGELOG) on `main` via PR.
3. Tag the RC from `main`:
   ```bash
   git checkout main && git pull
   git tag -a v1.4.0-rc.1 -m "RC1 for 1.4.0"
   git push origin v1.4.0-rc.1
   ```
4. CI builds once from the tag, publishes the artifact (Docker image tagged with the git tag), deploys to UAT.
5. UAT sign-off. Record who approved and when, in the release PR or ticket.
6. If UAT finds defects: fix on `main` via PR, tag `v1.4.0-rc.2`, repeat. Never patch UAT directly.
7. On sign-off, tag the release on the exact RC commit:
   ```bash
   git tag -a v1.4.0 v1.4.0-rc.2^{} -m "Release 1.4.0"
   git push origin v1.4.0
   ```
8. CI retags the existing RC artifact as `v1.4.0` and deploys to production. No rebuild.
9. Verify production health checks. Create a GitHub Release with the changelog.

## Hotfix flow

For a production defect when `main` has moved ahead with unreleased work:

1. Branch from the production tag: `git checkout -b hotfix/1.4.1 v1.4.0`
2. Fix, PR into the hotfix branch, tag `v1.4.1-rc.1` from it.
3. Deploy RC to UAT (or staging if UAT is occupied), verify the fix.
4. Tag `v1.4.1` on the same commit, deploy to production.
5. Cherry-pick or merge the fix back to `main` immediately. This step is mandatory. A hotfix not merged back regresses in the next release.

## Stabilization branch (exception case)

Only when a release needs hardening while `main` must keep taking new features:

1. Cut `release/1.4` from `main` at feature freeze.
2. RC and release tags come from `release/1.4`.
3. Only fixes land on it, each cherry-picked from `main` (fix on `main` first).
4. Delete the branch after the release ships and merges are confirmed.

## Rollback

- Preferred: redeploy the previous release tag's artifact. Fast, no git changes.
- Then decide: roll forward with a hotfix, or hold on the old version.
- Never revert by force-pushing or deleting tags. If a release is bad, the fix is a new tag.
- Database migrations: only roll back a version if its migrations are backward compatible. Enforce expand/contract migrations so N-1 app versions run against N schema.

## Gates checklist per promotion

Staging → UAT (before tagging RC):
- CI green on `main`, staging smoke tests pass
- CHANGELOG updated, version bumped
- No pending migrations that break N-1 compatibility

UAT → production (before tagging release):
- Written UAT sign-off recorded
- RC has run in UAT for the agreed soak period
- Rollback plan confirmed (previous tag identified, migration compatibility checked)
- Production tag targets the exact approved RC commit. Verify: `git rev-parse v1.4.0-rc.2^{} v1.4.0^{}` must print the same hash twice.

## CI/CD wiring

Read `references/github-actions.md` for complete GitHub Actions workflow examples covering the three triggers (push to main, `v*-rc.*` tags, `v*` release tags), artifact promotion without rebuild, and environment protection rules. Use it whenever setting up or reviewing pipelines for this lifecycle. For cutting wasted runs on the repo's CI workflows and migrating onto the org's reusable workflows, use `aot-ci-workflows`.

## Anti-patterns to reject

When you see these, stop and correct course:

- Deploying a branch to UAT or production. Only tags deploy there.
- Rebuilding the artifact for production. Promote the RC image.
- Tagging a release on a commit with no matching approved RC.
- Fixing bugs directly on a UAT or production environment.
- Reusing or moving a tag.
- Merging to `main` without a PR.
- A hotfix that never lands back on `main`.
