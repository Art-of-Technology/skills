# Shared reusable workflows in Art-of-Technology/.github

Four `workflow_call` workflows. Repos call them; they never copy them. Change CI once here, every repo picks it up. Runner routing: test, build, and docker jobs go to the datacenter `dc` group (labels `self-hosted, linux, x64, dc`); lint and typecheck stay on `ubuntu-latest`.

Every workflow carries `concurrency` keyed on workflow and ref, and the caller applies `paths-ignore`, PR event types, `merge_group`, and the draft guard from `aot-ci-workflows` stage 1.

## node-ci.yml

Turborepo monorepos: TypeScript, Node.js, Fastify or NestJS, Next.js, Prisma.

| Input | Default | Meaning |
|---|---|---|
| `node-version` | `22` | Node major or exact version |
| `turbo-filter` | `...[origin/main]` | Passed to `turbo run --filter`; only packages changed since `origin/main` |
| `runner-labels` | `["ubuntu-latest"]` | JSON array for test and build jobs |
| `pnpm-version` | from `packageManager` | Override only when the repo lacks the field |

Behaviour: `actions/checkout` with `fetch-depth: 0` so the filter has `origin/main` as a base. pnpm install with the store cached. `turbo run lint typecheck` on `ubuntu-latest`, `turbo run test build` on `runner-labels`. Build output uploaded as an artifact named after the sha. Reads `TURBO_API`, `TURBO_TEAM`, `TURBO_TOKEN` from org secrets when present so the LAN remote cache is used.

## dotnet-ci.yml

C# and ASP.NET Core services.

| Input | Default | Meaning |
|---|---|---|
| `dotnet-version` | `9.0.x` | SDK version |
| `project` | `.` | Solution or project path |
| `runner-labels` | `["ubuntu-latest"]` | For build, test, publish |

Behaviour: restore with the NuGet cache keyed on lock or project files, build, test with trx output uploaded, `dotnet publish -p:Version=<tag without v>` when the ref is a tag.

## docker-build.yml

| Input | Default | Meaning |
|---|---|---|
| `context` | `.` | Build context |
| `dockerfile` | `Dockerfile` | Path |
| `image` | `ghcr.io/<repo>` | Image name without tag |
| `runner-labels` | `["self-hosted","dc"]` | Buildx host |
| `push` | `true` | Set false for PR builds |

Behaviour: buildx with registry cache (`type=registry,mode=max`). Tags `sha-<sha>` always, and `<git tag>` when the ref is a tag. Logs in to ghcr with `GITHUB_TOKEN`. Uses the pull-through registry mirror when the runner host has one configured.

## release.yml

Implements `aot-release-lifecycle`. Read that skill's `references/github-actions.md` before touching this file.

| Trigger | Action |
|---|---|
| push to `main` | build `sha-<sha>` via docker-build, deploy staging, smoke test |
| tag `v*.*.*-rc.*` | retag `sha-<sha>` as the rc tag, deploy UAT, smoke test |
| tag `v*.*.*` (non-rc) | verify an rc tag points at the same commit, retag the rc image as the release, deploy production, create the GitHub Release |

No rebuild between UAT and production. `cancel-in-progress` is false on the tag triggers. Deploy step calls the repo's `deploy.sh <env> <image>`.

| Input | Meaning |
|---|---|
| `image` | Image name, same as docker-build |
| `staging-url`, `uat-url`, `production-url` | Health endpoints for smoke tests |
| `runner-labels` | Host that can reach the target environment |

## Caller template

```yaml
name: ci
on:
  push:
    branches: [main]
    paths-ignore: ['**.md', 'docs/**', '**.png', '**.jpg', '**.jpeg', '**.gif', '**.svg', '**.webp']
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]
    paths-ignore: ['**.md', 'docs/**', '**.png', '**.jpg', '**.jpeg', '**.gif', '**.svg', '**.webp']
  merge_group:

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  node:
    if: github.event_name != 'pull_request' || github.event.pull_request.draft == false
    uses: Art-of-Technology/.github/.github/workflows/node-ci.yml@main
    with:
      node-version: '22'
      turbo-filter: '...[origin/main]'
      runner-labels: '["self-hosted","linux","x64","dc"]'
    secrets: inherit

  e2e:   # repo-specific, stays local
    needs: node
    if: github.event_name != 'pull_request' || github.event.pull_request.draft == false
    runs-on: [self-hosted, dc]
    steps:
      - uses: actions/checkout@v4
      - run: pnpm test:e2e
```

## Merge queue

With the merge queue on `main`, required checks run against a temporary `gh-readonly-queue/main/...` ref on the `merge_group` event. The squash commit then lands on `main` as a normal push, so the staging deploy in `release.yml` fires unchanged. Required checks must be job names produced by these workflows plus Octopus.

## Where a repo needs something these lack

Comment on the repo's `ci-adoption` issue. Do not add a local workaround or fork the workflow.
