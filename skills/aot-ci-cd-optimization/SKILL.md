---
name: aot-ci-cd-optimization
description: Measure and improve GitHub Actions CI/CD speed through independent parallel checks, cancellation of superseded runs, efficient secret scanning, caching and reuse of tested artifacts. Use when setting up or speeding up a pipeline, investigating long checks or duplicate runs, or improving image publication. Preserve the repository's review and deployment policy.
---

# CI/CD speed without weaker gates

Improve time from a code change to a verified artifact. Measure the bottleneck,
change the smallest useful part, and prove that failures still block delivery.

## Establish the contract

Read the target repository's agent/contribution instructions, package scripts,
lockfile, workflows, Dockerfiles and deployment procedure. Identify:

- Required checks and their exact names; review evidence and merge rules.
- PR, merge-queue, main-push, tag and manual triggers; workflow callers and
  concurrency groups. A reusable workflow can already provide main validation.
- Package/runtime versions, frozen install commands, test services and shared
  mutable resources, runner capacity and trust boundaries.
- What actually builds, tests, publishes and promotes each service, and which
  actions require owner approval. Publication and deployment are separate facts.

Preserve existing authorization and policy. This skill does not authorize a
merge, workflow cancellation, production change, new paid runners or changes to
branch protection. Proceed with actions already covered by the user's request.
Do not impose a new release/tag convention on an existing project.

## Measure before changing

Use `gh-axi` when available, otherwise `gh`, to inspect representative successful
runs and the current task's runs. Record commit, run/attempt, queue time, job/step
duration, test counts and cache state. Separate wall time from total runner work.
Cancelled and failed runs are useful diagnostics, not comparable completion times.

Find the critical path: duplicated workflow calls, serial independent tasks,
one dominant test file, repeated compilation, slow installation, cache upload,
or runner queuing. Profile the slow task instead of assuming the review tool is
the cause. Compare identical cases in equivalent environments; distinguish a
filtered sample from a complete-suite result.

## Choose improvements supported by the evidence

1. **Remove duplicate validation.** Keep one authoritative gate per event and
   revision. For example, PR CI plus a main publication workflow calling CI once
   avoids a second direct main-push CI run. A PR head and its merge commit are
   different revisions; do not claim earlier evidence automatically covers both.
2. **Run independent work concurrently.** Lint, typechecks, unit tests, isolated
   database tests and secret/dependency checks can often overlap. Keep real
   dependencies, such as browser tests using a built artifact. Bound concurrency
   by CPU, memory and runner slots; extra jobs can increase queue/install cost.
3. **Cancel obsolete checks.** Group PR checks by workflow/caller and PR identity,
   not commit SHA or run ID. Keep publication, promotion, migration and release
   concurrency separate; preserve the project's cancellation/serialization policy.
4. **Reduce repeated work inside tests.** Profile expensive fixtures and queries.
   Preserve cases, assertions, realistic boundaries and timeout limits. Keep
   test-only shortcuts scoped to fixtures; prove changed inputs and negative
   cases still fail. Do not replace real coverage with a faster mock silently.
5. **Cache inputs and reuse artifacts.** Cache package stores by lockfile,
   runtime/OS and relevant tool configuration; use separate Docker cache scopes
   per service. Cache hits accelerate work; they do not prove a new head passed.
   Include build-time inputs and platform in artifact identity.
6. **Keep secret scanning cheap and current.** Scan new changes or the current
   tracked snapshot for each changed head. Reserve expensive full-history scans
   for initial assessment, scheduled or manual runs unless policy requires more.
   Do not remove an existing fast check merely because it runs on every push.

For workflow wiring, cancellation, aggregation and artifacts, read
[GitHub Actions patterns](references/github-actions.md). For scan boundaries,
redaction and evidence reuse, read [secret scans](references/secret-scans.md).

## Preserve a trustworthy merge and publication gate

Keep validation blocking. A terminal aggregator must require every expected
result to be exactly `success`; failures, cancellation, missing jobs and
unexpected skips cannot authorize a merge. If local policy prohibits an
always-running aggregate job, use an existing task runner inside a blocking job
and verify its exit/cancellation behavior. Never hide a failed validator.

Keep current required-check names until a reviewed protection change is ready.
Add `merge_group` only when the repository uses a merge queue. Avoid workflow
path filters that leave required checks pending; any conditional check needs an
explicit, tested applicability decision included in the gate.

Publish only the validated artifact from the intended trusted revision/run.
Retain service digests and revision metadata. Promote the same artifact using
the existing environment policy; do not rebuild on a deployment host. Verify
the running digest and feature behavior before reporting deployment complete.

## Validate and deliver

- Run the project's prescribed frozen install, checks, tests and builds.
- Prove both success and failure paths: each validator fails the gate; missing
  or skipped results fail; cancellation stops owned work; superseded PR runs do
  not cancel protected releases. Test changed secret-scan inputs and scan errors.
- Verify all original test identities/cases remain when optimizing a suite.
  Run relevant negative controls and the full suite after sampled measurements.
- Validate workflow syntax/action pins, cold and warm cache behavior where
  relevant, and the complete image set. Inspect actual post-merge runs before
  claiming the workflow change reduced delivery time.
- Keep operational documentation/changelogs aligned. Report measured before/
  after timings with scope, gate evidence, remaining bottlenecks and whether
  images are published or actually deployed.

Use the repository's existing review process. Where applicable,
[aot-ship-loop](../aot-ship-loop/SKILL.md) handles delivery checks and
[aot-release-lifecycle](../aot-release-lifecycle/SKILL.md) handles an explicitly
requested release. Neither link replaces the target repository's policy.
