# Fast secret scanning with current evidence

Keep a cheap check for newly introduced secrets on each changed head. Avoid
repeating an expensive all-history scan across multiple workflows for the same
revision. First inspect existing controls: a repository may already have a fast
tracked-file scanner that should remain required.

## Choose the scope deliberately

| Situation | Useful scope |
| --- | --- |
| PR update | The PR's introduced commits/changes relative to a verified base, plus any required current-snapshot check |
| Main push | Introduced changes relative to the verified previous protected revision, through the authoritative publication gate |
| Initial assessment, schedule, explicit investigation | Full history or selected historical refs, according to owner policy |
| Same-head retry | Reuse only trusted, successful evidence with identical scan inputs and policy; otherwise rerun the cheap scan |

Use the PR base/merge base for PR coverage, rather than only the immediately
previous push: a failed earlier PR commit must not escape review after a later
clean commit. Validate full object IDs and ancestry, fetch the needed history,
and handle initial pushes or missing bases explicitly. Do not fall back to an
empty range and report success. Commit-range scanning also catches secrets
introduced and then removed within the selected history.

The Gitleaks CLI supports commit ranges through `git --log-opts`. Resolve the
intended base/head from trusted event metadata, then validate before scanning:

```bash
set -euo pipefail
[[ "${BASE_SHA:-}" =~ ^[0-9a-f]{40}$ && "${HEAD_SHA:-}" =~ ^[0-9a-f]{40}$ ]] || exit 2
git cat-file -e "${BASE_SHA}^{commit}"
git cat-file -e "${HEAD_SHA}^{commit}"
git merge-base --is-ancestor "$BASE_SHA" "$HEAD_SHA"
commit_count=$(git rev-list --count "${BASE_SHA}..${HEAD_SHA}")
[[ "$commit_count" -gt 0 ]] || exit 2
gitleaks git --redact=100 --no-banner --log-opts="${BASE_SHA}..${HEAD_SHA}" .
```

Do not rely on the scanner exit code to validate history: some versions can
report success after Git rejects an invalid range. The explicit checks above
reject missing revisions, reversed/unrelated history and zero-commit coverage.
Handle an intentionally empty range through a documented snapshot check or
verified prior verdict, never an accidental empty scan. Pass metadata through
environment variables and quote arguments; never interpolate arbitrary
PR text into shell code. Pin and verify the scanner release or action commit.
Scanner errors, unavailable history, findings and unexpected empty coverage are
not successful scans. Use deliberately fake secrets in isolated validation
fixtures and keep reports fully redacted.

## Evidence is scoped to its inputs

A reusable success record needs the exact scanned head and base, scanner
version, configuration/rule hash, trusted producer/run, completed-success state,
and any freshness requirement. A new commit, changed rules, changed base or
failed/cancelled scan invalidates it. Cache the scanner binary and dependencies;
do not treat a cache hit as a passing security result.

Do not automatically baseline a newly found secret or allowlist a broad path to
make CI green. Existing findings need scoped triage and the repository's
remediation procedure. Keep real credentials and unredacted reports out of
commits, PR comments, ordinary artifacts and logs. Credential rotation and
history rewriting are separate actions subject to existing authorization.

## Prove the boundary

- A clean range passes, and a fake secret added in the range fails.
- A fake secret added then removed inside that range is still detected.
- Missing/invalid bases and scanner execution failures fail closed.
- A new head or changed scan configuration cannot reuse the previous verdict.
- Logs and retained reports reveal no secret values.

See [Gitleaks commands and configuration](https://github.com/gitleaks/gitleaks).
