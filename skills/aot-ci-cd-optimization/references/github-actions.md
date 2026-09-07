# GitHub Actions patterns

Adapt these patterns to the repository's commands, runner capacity and required
check names. They are focused examples, not a complete workflow to copy blindly.

## Triggers and cancellation

A common arrangement is PR checks in a reusable CI workflow, with main image
publication calling that workflow once. Avoid also triggering the same CI
directly on main pushes. Separate callers prevent a publication run from
cancelling a PR's required checks.

```yaml
concurrency:
  group: quality-${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}
```

Keep the key stable across commits to a PR. Do not use the head SHA or run ID as
the PR cancellation key. Include the caller's identity for reusable workflows.
Add a merge-queue trigger when the repository actually uses one.

Newest-wins staging publication is appropriate only when the project's policy
allows it. Production promotions and database migrations usually need
serialization without interrupting the active operation. Inspect pending-run
semantics as well: `cancel-in-progress: false` alone does not promise that every
pending run will eventually execute. Configure supported queue behavior when
every release request must be retained.

See [GitHub concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency).

## Parallel checks and one blocking result

Use independent jobs where runner capacity and setup cost justify them. Preserve
true dependencies: a browser job can depend on the production build artifact,
while lint, types, isolated database tests and secret checks run independently.
Keep PR code away from production credentials and persistent privileged runners
unless the repository's trust model actually permits it. A private repository
alone is not proof that every contributor, PR or dependency is trusted.

A skipped dependency can cause its dependants to be skipped. A terminal gate
must execute and explicitly reject non-success results. This example assumes
the workflow defines all six named dependencies and allows an always-running
terminal gate. Preserve the existing required status name when adapting it.

```yaml
ready:
  name: CI Ready
  if: always()
  needs: [lint, typecheck, tests, integration, secrets, build]
  runs-on: ubuntu-24.04
  permissions:
    contents: read
  timeout-minutes: 2
  steps:
    - name: Require every declared check
      env:
        RESULTS: ${{ toJSON(needs) }}
      run: |
        node <<'NODE'
        const expected = ['lint', 'typecheck', 'tests', 'integration', 'secrets', 'build'];
        const results = JSON.parse(process.env.RESULTS);
        if (!results || typeof results !== 'object' || Array.isArray(results)
            || Object.keys(results).length !== expected.length
            || expected.some(name => results[name]?.result !== 'success')) {
          process.exit(1);
        }
        NODE
```

`always()` here makes the verdict run after failures; it does not make any
validator optional. Do not apply it to a publication job so publication runs
after failed checks. If the repository forbids this pattern, retain a blocking
job and use its existing task runner to await parallel work, returning nonzero
on any failure or cancellation. Avoid hand-written detached background commands
whose child processes outlive the job.

For Turborepo, run multiple declared tasks with bounded `--concurrency`; normal
task scheduling preserves dependencies. Do not use `--parallel` to bypass the
task graph. `--continue=never` cancels remaining tasks after failure and returns
nonzero. Preserve root-level governance/secret/delivery tests that may sit
outside workspace tasks; `turbo run test` alone may omit them.

Test the actual runner with isolated fixtures: successful tasks overlap within
the bound; each failed task returns a failed verdict; cancellation terminates
owned work. For a job aggregator, inject success, failure, cancellation, skipped,
missing, malformed and extra-result inputs.

See [GitHub job dependencies](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-jobs)
and [Turborepo execution controls](https://turborepo.dev/docs/reference/run).

## Reuse tested outputs

- Build in the runtime/architecture used by the image. If browser tests consume
  a standalone build, package that same output; do not compile a second copy for
  publication and call it the tested artifact.
- Name intermediate artifacts with run ID and attempt; record the revision,
  platform and build-time configuration. Retrieve only from the intended trusted
  workflow/run. An artifact's filename or embedded revision claim is insufficient
  proof of its producer.
- Keep validation permissions read-only. Grant package-write permission only to
  publication. Do not introduce a privileged `workflow_run` consumer that trusts
  executable artifacts from untrusted PRs.
- Capture every service's image digest. Use digests for promotion or verify a
  commit-pinned image tag against its recorded digest. Mutable tags and a green
  health endpoint do not establish the deployed revision.
- Scope Docker caches per image/service. Keep runtime secrets out of build
  contexts, layers, caches and artifacts. Do not run a frozen install and then
  silently change the dependency graph during image packaging.

See [Docker cache scopes](https://docs.docker.com/build/cache/backends/gha/).

## Measure the result

Compare queue time, time to first failure, total runner time, and time to a
complete publishable artifact. Parallelism can improve latency while increasing
runner work; warm cache improvements need a cold-cache check too. Report local
test timings separately from actual GitHub workflow timings. Keep cancelled runs
out of successful-run timing comparisons.
