---
name: blog-content-agent
description: Research trends, analyze a product repository to learn what it does, propose blog topics, write a publication-ready post, optionally generate a banner image, self-review against a scorecard, and publish to a configured blog platform with an optional team notification. Use this whenever the user wants to create, draft, generate, or publish a blog post or content-marketing piece for a product, run a recurring or automated blogging workflow, turn a repo or product into blog content, or fill a blog with codebase-aware posts. Works for any product through a per-product config file with no secrets baked in. Trigger even when the user only says "write a blog post", "daily post", "content for our blog", or names a product and a blog platform.
---

# Blog Content Agent

Turn a product and its repository into a unique, publication-ready blog post, then publish it to the team's blog platform.

This skill is product-agnostic. Every product detail comes from a config file. No API keys, URLs, or product names live in the skill itself.

## Domain model

- **Product profile**: name, URL, repo, audience, voice, community links. Source of truth for what you write about.
- **Repo brief**: what the product does, derived by reading the repo. Drives topic relevance and accurate code examples.
- **Trend signals**: stats, pain points, and emerging themes pulled from web research.
- **Existing posts**: already-published content, used to avoid duplication.
- **Topic category**: one of five rotation buckets. Never two posts in a row from the same bucket.
- **Draft**: title, slug, markdown body, optional banner, SEO metadata.
- **Platform adapter**: how this product publishes (WordPress, Ghost, Dev.to, generic REST, or a local markdown file).
- **Notification**: optional post-publish message to a team channel.

## Setup (first run for a product)

1. Locate the config. Look for `product-config.json` in the working directory or a path the user gives. If none exists, copy `assets/product-config.example.json`, fill it with the user, and save it.
2. Confirm secrets are in environment variables, never in the config file. The config names the env vars; the values stay in the environment. See the `secrets` block in the example config.
3. Read `references/platforms.md` for the platform the config selects.

Never paste API keys, tokens, or webhook URLs into the config file, the post, chat, or any committed file. If a key appears in conversation, treat it as exposed and tell the user to rotate it.

## Workflow

Work backwards from the goal: a unique, accurate, on-brand post live on the product's blog, optionally with a banner and a notification.

### Step 0: Preflight (fail fast)

Run `python scripts/preflight.py <config-path>` before anything expensive. It validates the config, confirms required environment variables are set, scans the config for literal secrets, and prints the state summary. If it exits non-zero, stop and report the errors. Do not research or write until preflight passes. This avoids burning a full run only to die at publish on a missing key.

Note the `lastCategory` and recent slugs it prints. You use both below.

### Step 1: Build the repo brief

Read `references/repo-analysis.md`, then produce a short product brief: what it does, primary features, real CLI commands or APIs, and the audience. This brief is the only source for code examples. Do not invent commands, flags, or config formats. If you cannot verify a feature exists, leave it out.

### Step 2: Check existing posts

Read state first: `python scripts/state.py show --config <config-path>`. It gives you the last category and recent slugs, which are ground truth for rotation and dedup.

Then pull existing titles from the platform (search endpoint, sitemap, or the local posts folder). Run at least 3 varied keyword searches around your planned area. For each hit, note the title, angle, featured feature, and audience. Combine platform results with the state history so rotation and dedup do not rely on guesswork.

### Step 3: Research trends

Run multiple targeted web searches, not one generic query. Cover:

- Recent developments in the product's domain
- Real pain points from developer or user discussions
- Industry data or stats you can cite
- Emerging themes most blogs have not covered

Extract one concrete stat, one real sourced pain point, and one fresh angle. Ignore off-topic results. If research yields only generic "X is changing everything" content, dig deeper for specific numbers and incidents.

### Step 4: Suggest topics, then confirm

Pick a topic category different from `lastCategory` in the state and from the recent posts. Propose 2 or 3 candidate topics, each with a one-line angle and the category it fits. Wait for the user to pick one.

Skip the wait only if the user explicitly asked for a fully unattended end-to-end run. In that case, pick the strongest candidate and continue.

Categories: pain-point, trend-analysis, how-to, deep-dive, opinion. Rotate through them.

### Step 5: Write the post

Follow `references/writing-guide.md` for title rules, structure, length, tone, SEO, and the honesty rule on code examples. Output title, slug (kebab-case), and markdown body. The product is always the primary tool in the narrative. Never name competitors; refer to alternatives generically.

### Step 6: Banner image (optional)

If `banner.enabled` is true in the config, generate a cover image through the configured provider, then poll for the result. Poll on the interval and attempt cap in the config (default every 5s, max 12 attempts). If it does not complete in time, publish without a cover image.

If `banner.enabled` is false, skip this step.

### Step 7: Self-review

Score the draft 1 to 5 on each criterion in `references/writing-guide.md` (Product focus, No competitor mentions, Uniqueness, Hook quality, Technical depth, Accuracy, Freshness, SEO keywords, Word count). Show the scorecard with per-criterion scores and the average. If the average is below 4.0, rewrite and re-score. Only publish at 4.0 or above.

### Step 8: Publish (idempotent)

First guard against duplicates from a re-run. Save the draft body to a file, then run `python scripts/state.py check --config <config-path> --slug <slug> --content-file <draft>`:

- Exit 0 (NEW): publish.
- Exit 3 (DUPLICATE_CONTENT): identical content already shipped. Skip publishing and report it. Do not republish.
- Exit 4 (SLUG_EXISTS): the slug is taken by different content. Use the suggested slug it prints, then publish.

If running in dry-run mode, stop here and hand over the draft without publishing.

Otherwise use the platform adapter in `references/platforms.md` matching `platform.type`. Submit title, content, slug, and cover image if present. Capture the returned slug or URL.

### Step 8b: Record state

After a successful publish, run `python scripts/state.py record --config <config-path> --slug <slug> --title "<title>" --category <category> --content-file <draft> --url <url>`. This updates `lastCategory` and the publish history so the next run rotates correctly and cannot duplicate this post. In CI, commit the state file back to the repo.

### Step 9: Notify (optional)

If `notify.enabled` is true, send the published URL to the configured channel. If the primary method fails, use the fallback in the config. Do not fall back to any unconfigured channel.

### Step 10: Report

Return: title, slug, full URL, banner URL if any, the scorecard with average, and which topic category was used.

## Running modes

- **Suggest mode** (default): stop at Step 4 for topic approval, then continue.
- **End-to-end mode**: user asks for a full unattended run, or a scheduler invokes it. Auto-pick the topic and run all steps.
- **Draft-only mode**: user wants the post but not publishing. Stop after Step 7 and hand over the markdown.
- **Dry-run mode**: run every step including the duplicate check, but stop before publishing and notifying. Use it to preview a scheduled run safely.

## Automation

To run this daily without a human, see `references/automation.md` and the ready-to-edit workflow in `assets/github-action.yml`. The runner uses Claude Code headless mode on a cron schedule, one job per product, and commits the state file back so rotation and dedup persist across runs.

## Reference files

- `references/repo-analysis.md`: how to read a repo and produce the product brief.
- `references/platforms.md`: publish and dedup adapters per platform.
- `references/writing-guide.md`: title, structure, tone, SEO, code honesty, scorecard.
- `references/automation.md`: scheduled unattended runs via GitHub Actions.
- `assets/product-config.example.json`: config template to copy per product.
- `assets/github-action.yml`: copy-paste GitHub Actions workflow.
- `scripts/preflight.py`: config, env, and secret validation. Run first.
- `scripts/state.py`: rotation and idempotent-publish state. Stdlib only.
