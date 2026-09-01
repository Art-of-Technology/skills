# GitHub Actions wiring for main → staging, rc tag → UAT, release tag → production

Three workflows, three triggers. Docker image is built once per commit and promoted by retagging.

## 1. Staging: push to main

```yaml
# .github/workflows/staging.yml
name: staging
on:
  push:
    branches: [main]

concurrency:
  group: staging
  cancel-in-progress: true

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4

      - name: Build and push image
        run: |
          IMAGE=ghcr.io/${{ github.repository }}:sha-${{ github.sha }}
          docker build -t "$IMAGE" .
          echo "${{ secrets.GITHUB_TOKEN }}" | docker login ghcr.io -u ${{ github.actor }} --password-stdin
          docker push "$IMAGE"

      - name: Deploy to staging
        run: ./deploy.sh staging "ghcr.io/${{ github.repository }}:sha-${{ github.sha }}"

      - name: Smoke test
        run: curl -fsS --retry 10 --retry-delay 6 https://staging.example.com/health
```

## 2. UAT: rc tag

```yaml
# .github/workflows/uat.yml
name: uat
on:
  push:
    tags: ['v*.*.*-rc.*']

jobs:
  promote-to-uat:
    runs-on: ubuntu-latest
    environment: uat
    steps:
      - uses: actions/checkout@v4

      - name: Retag commit image with rc tag
        run: |
          SRC=ghcr.io/${{ github.repository }}:sha-${{ github.sha }}
          DST=ghcr.io/${{ github.repository }}:${{ github.ref_name }}
          echo "${{ secrets.GITHUB_TOKEN }}" | docker login ghcr.io -u ${{ github.actor }} --password-stdin
          docker buildx imagetools create -t "$DST" "$SRC"

      - name: Deploy to UAT
        run: ./deploy.sh uat "ghcr.io/${{ github.repository }}:${{ github.ref_name }}"

      - name: Smoke test
        run: curl -fsS --retry 10 --retry-delay 6 https://uat.example.com/health
```

The retag step assumes the staging workflow already built `sha-<commit>` when the commit merged to main. If the rc tag points to a commit never built (stabilization branch), add a fallback build step guarded by an image-exists check.

## 3. Production: release tag

```yaml
# .github/workflows/production.yml
name: production
on:
  push:
    tags: ['v*.*.*']

jobs:
  guard:
    # Skip rc tags: v1.4.0-rc.1 matches v*.*.* on some patterns, so filter explicitly
    if: ${{ !contains(github.ref_name, '-rc.') }}
    runs-on: ubuntu-latest
    outputs:
      rc_tag: ${{ steps.verify.outputs.rc_tag }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Verify release commit has an approved rc tag
        id: verify
        run: |
          RC_TAG=$(git tag --points-at HEAD | grep -E "^${{ github.ref_name }}-rc\.[0-9]+$" | sort -V | tail -1)
          if [ -z "$RC_TAG" ]; then
            echo "::error::No rc tag found on this commit. Production tags must point at an approved RC commit."
            exit 1
          fi
          echo "rc_tag=$RC_TAG" >> "$GITHUB_OUTPUT"

  promote-to-production:
    needs: guard
    runs-on: ubuntu-latest
    environment: production   # configure required reviewers on this environment
    steps:
      - name: Retag rc image as release
        run: |
          SRC=ghcr.io/${{ github.repository }}:${{ needs.guard.outputs.rc_tag }}
          DST=ghcr.io/${{ github.repository }}:${{ github.ref_name }}
          echo "${{ secrets.GITHUB_TOKEN }}" | docker login ghcr.io -u ${{ github.actor }} --password-stdin
          docker buildx imagetools create -t "$DST" "$SRC"

      - name: Deploy to production
        run: ./deploy.sh production "ghcr.io/${{ github.repository }}:${{ github.ref_name }}"

      - name: Health check
        run: curl -fsS --retry 10 --retry-delay 6 https://example.com/health

      - name: Create GitHub Release
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: gh release create ${{ github.ref_name }} --generate-notes
```

## Environment protection settings

Configure in repo Settings → Environments:

- `staging`: no reviewers, main branch only.
- `uat`: deployment branches/tags restricted to `v*-rc.*` tags.
- `production`: required reviewers (at least one), tags restricted to `v*` non-rc, optional wait timer.

## Branch protection on main

- Require pull request before merging, one approval minimum.
- Require status checks: build, tests, lint.
- Require linear history (squash merges).
- Block force pushes and deletions.

## Tag protection

Add a tag protection rule (or ruleset) for `v*` so only release managers push version tags.

## deploy.sh contract

Each repo supplies its own `deploy.sh <env> <image>`. For Docker Compose on a self-hosted runner, the script sets the image tag in the env file and runs `docker compose up -d`, then waits on the health endpoint. Keep the interface identical across repos so the workflows stay copy-paste portable.

## .NET and Node version stamping

Stamp the version into the artifact at build time so /health or /version reports it:

- Node: `npm version ${TAG#v} --no-git-tag-version` before build, expose via env.
- .NET: `dotnet publish -p:Version=${TAG#v}`.
