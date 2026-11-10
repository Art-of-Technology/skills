---
name: aot-test-bottleneck
description: "Find why tests are slow in an agent pipeline or CI, then cut the wait without weakening any gate: time each stage, name the bottleneck, run only the tests a change can break, reuse results for lanes whose inputs did not change, and replace agent-improvised test steps with fixed commands. Use whenever tests or a pipeline's test step feel slow or have become the bottleneck, a small change or a review follow-up triggers a whole-suite or whole-pipeline rerun, an agent is about to rerun everything to be safe, or the user asks how to make tests faster or what the testing best practices are. Also use before waiting more than a few minutes on a test stage. Not for GitHub Actions wiring, caching or cancellation (use aot-ci-cd-optimization or aot-ci-workflows)."
---

# Tests as the bottleneck

Shorten the time from a change to evidence you can trust. Work in this order,
because each step changes what the next one is worth: measure, name the
bottleneck, select, reuse. Report numbers, not impressions.

## 1. Time each stage first

The test suite is often not the slow part. Before changing anything, collect
these for one or two representative runs of the current change:

- **Raw suite time.** Run the suite directly and read the runner's own total
  and test count. For example `node --test` prints `# duration_ms`, pytest has
  `--durations=10`, and `go test -json` reports elapsed time per package.
- **Stage time.** What the pipeline or CI reports per step and per job, for
  example `no-mistakes axi status` (its `steps` table has `duration_ms`),
  `gh pr checks <n>` or `gh run view <id> --json jobs`.
- **Setup inside the stage.** Dependency install, build, database bootstrap,
  service start. Read the stage log for what happened before the first test.
- **Rounds.** How many times each stage ran for this change, and why.

Put them in one table. A real case looked like this:

| Stage | Time | What it did |
|---|---|---|
| Full suite, run directly | 76 s | 1,523 tests |
| CI, three path-filtered workflows | 2 to 4 min | ran in parallel |
| Pipeline test step | 11 to 15 min | an agent planned and built its own checks |
| Rounds | 2 | a five-line review fix reran every stage |

The suite was never the problem. Without the table, the obvious fix (shard the
suite) would have saved about a minute of a forty-minute wait.

## 2. Name the bottleneck

Match what you measured to one cause. Fix that one before the next.

| What you see | Cause | Fix |
|---|---|---|
| Stage time is many times the raw suite time, and the log shows an agent deciding what to run | Improvised test step | Give the stage a fixed command and narrow instructions (below) |
| Minutes pass before the first test starts | Environment rebuilt every run | Prepare once and share it; do not build what the tests do not import |
| Every change runs everything | No selection | Section 3 |
| A small follow-up reruns all stages | No reuse | Section 4 |
| A few tests or one fixture dominate | Slow tests | Profile the ten slowest; fix setup and waits before adding workers |
| The same work ran twice | First result discarded | Find why it was discarded (unverified exit, timeout, fallback agent) and fix that |

**Improvised test step.** Some agent pipelines hand the test stage to a model
when no command is configured. The model then installs dependencies, tries
builds and writes its own drivers on every run. Configure the deterministic
part and leave the model only what needs judgement. In no-mistakes that is
`commands.prepare` and `commands.test` in `.no-mistakes.yaml`, which the
pipeline reads from the default branch. The agent still drives a few targeted
scenarios afterwards, so keep `test.instructions` explicit about what it must
not rebuild. Check the tool's own reference for the exact keys before editing.

**Parallelism comes last.** More workers on tests that share a database, a
port or a temp directory produce flakes, and a flaky suite is slower than a
slow one because every false failure costs a rerun.

## 3. Run what the change can break

Select by dependency, not by file extension or by habit.

1. Start from the diff against a verified base.
2. Take the changed modules, everything that imports them, and the tests that
   cover either. Use what the project already has: CI path filters,
   `nx affected -t test`, `turbo run test --filter='...[origin/main]'`,
   `jest --findRelatedTests <files>`, `vitest related <files>`, pytest by path
   or `--testmon`, `go test ./pkg/...`.
3. Add the always-run set: authentication, permission and other security
   tests, plus schema and migration tests when the data shape changes.
4. Run the whole suite when the diff touches a lockfile, a toolchain version,
   a shared test helper or shared configuration, or when you cannot tell what
   depends on the change. Unknown is a reason to run more, never less.

Decide where the full suite still runs (merge, nightly or release) and say so
in the report. Selection moves the full run later; it does not remove it.

**Read failures against a baseline.** A local environment can be stale, so a
raw failure count misleads in both directions. Run the same selection on the
base commit and compare the names of the failing tests. Failures present on
both sides belong to the environment. Failures only on your branch are yours,
even when the total looks unchanged.

## 4. Reuse results for a follow-up

A lane's earlier pass still stands when none of its inputs changed: the code
it covers, its tests and fixtures, the lockfile, configuration and toolchain.

- For a review fix, rerun the tests that cover the changed lines plus the
  always-run tests that apply. Keep earlier results for untouched lanes and
  record them as reused, with the commit they ran on. Do not present an old
  result as a run on the new head.
- Batch review fixes. Collect every finding from a round, fix them in one
  commit and validate once. Each extra push can cost a full round.
- If the pipeline cannot reuse anything and revalidates every push from the
  start, the first push is expensive to get wrong. Run the affected tests and
  the baseline comparison locally before pushing, and prefer one complete
  change over several small corrections.
- Skip a stage only where the project's own policy allows it, such as tests
  for a documentation-only change. Never skip review or tests for
  authentication, payments, infrastructure or other sensitive paths.

## 5. Wait without spending turns

A running test needs no model. Block on a completion signal instead of
checking in a loop: `gh pr checks <n> --watch`, the pipeline's own blocking
command, or a background task that notifies on exit. Use the wait for work
that does not depend on the result.

## What speed may not buy

- No deleted, skipped or loosened tests and assertions. A quarantined test
  needs an owner, a reason and an expiry.
- Skipped is not passed. Unknown is not passed. A cached pass belongs to the
  inputs it ran on.
- Do not abort or restart a running pipeline to apply any of this. Change its
  configuration between runs, through the project's normal review.
- Required checks, review policy and release gates stay as their owner set
  them. This skill does not authorize a merge, a deployment or a change to
  branch protection.

## Report

```
Bottleneck: <one line naming the cause>

| Stage | Time | What it did |
|---|---|---|

Change: <the one change made or proposed>
Saving: <measured before and after, or "not yet measured">
Still runs every time: <the always-run set>
Ran / reused / skipped: <what, and why for anything reused or skipped>
Full suite runs at: <merge | nightly | release>
```

For GitHub Actions wiring, caching, cancellation and artifact reuse, continue
with [aot-ci-cd-optimization](../aot-ci-cd-optimization/SKILL.md) and
[aot-ci-workflows](../aot-ci-workflows/SKILL.md). For the delivery loop
itself, see [aot-ship-loop](../aot-ship-loop/SKILL.md).
