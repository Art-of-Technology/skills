# Automation

Run the agent daily without a human using Claude Code headless mode on a cron schedule. The skill is the brain; this is the body that fires it.

Copy `assets/github-action.yml` to `.github/workflows/daily-blog.yml` in a content repo and edit the matrix and schedule.

## Repo layout

```
content-repo/
  .claude/skills/blog-content-agent/   the skill, committed here
  configs/product-a.json               one config per product
  configs/product-b.json
  state/product-a.json                 written and committed by the job
  posts/                               only for markdown-file platforms
  .github/workflows/daily-blog.yml
```

Committing the skill into `.claude/skills/` makes Claude Code load it as a project skill, so `claude -p` finds it by name.

## Secrets

Add these under Settings, Secrets and variables, Actions. Names must match the env var names in each config's `secrets` block.

- `ANTHROPIC_API_KEY`: powers Claude Code. Required.
- `BLOG_API_KEY`: blog platform auth. Required for remote platforms.
- `BANNER_API_KEY`: image provider. Only if `banner.enabled`.
- `NOTIFY_WEBHOOK_URL`: notification target. Only if `notify.enabled`.
- `REPO_TOKEN`: read access for private product repos. Optional.

Rotate these like any production credential. Use environment protection rules for the workflow if your plan supports it.

## How a run flows

1. Checkout, install Node, install Claude Code.
2. Preflight runs first and fails the job on a bad config, a missing secret, or a leaked key. No tokens are spent if it fails.
3. `claude -p` runs the skill end-to-end for one product config. `--allowedTools` scopes what it can touch. `--max-turns` and the job `timeout-minutes` cap runaway cost and hung jobs.
4. On success the job commits `state/` (and `posts/` for static-site blogs) back with `[skip ci]`, so rotation and dedup persist to the next run.

## Why these guardrails

- `--dangerously-skip-permissions`: permission prompts cannot fire in headless mode, so the run would otherwise stall. The runner is ephemeral and isolated, and the tool list is scoped, which is the recommended pattern for CI. Do not widen the tool list without reading the prompt.
- `max-parallel: 1`: serializes products so two jobs never push the state file at once.
- `dry_run` input: a manual run that does everything except publish and notify. Use it to validate a config change safely.
- `--output-format json`: the run log is captured as an artifact-friendly JSON file for debugging.

## Alternatives

- Plain cron on a server: same `claude -p` command in a crontab. Set `ANTHROPIC_API_KEY` and the other env vars explicitly, since cron does not load your shell profile.
- `anthropics/claude-code-action@v1`: the official action, better suited to PR and `@claude` triggers than scheduled content jobs. The headless CLI above gives more direct control for this use case.

## Scaling to many products

Add one config per product to the matrix. Keep `max-parallel: 1` if all products share one state branch. If you split state per repo or per branch, you can raise parallelism. Watch token spend: each product run does web research, a repo read, optional image generation, and one or more rewrites.
