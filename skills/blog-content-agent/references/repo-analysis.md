# Repo Analysis

Goal: produce a short product brief that tells you what the product does and gives you only real, verifiable code examples. Everything you write about the product traces back to this brief.

## Sources, in priority order

1. **Config first.** Read `product.name`, `product.url`, `product.repo`, `product.repoPath`, and `product.audience` from the config.
2. **Local checkout** if `product.repoPath` is set. Fastest and most complete.
3. **GitHub API** if only `product.repo` is set. Use `https://api.github.com/repos/{owner}/{repo}` and the contents endpoint. No token needed for public repos at low volume; for private repos read the token from the env var named in the config.
4. **Product site** at `product.url`. Fetch the homepage and any docs pages for positioning and feature names.

## What to read

Read the cheap, high-signal files before anything else:

- `README.md` and `docs/`: positioning, feature names, quickstart, real commands.
- Package manifest: `package.json`, `pyproject.toml`, `*.csproj`, `Cargo.toml`, `go.mod`. Tells you language, framework, and declared CLI binaries or scripts.
- CLI entry points: `bin/`, `cmd/`, `scripts` in `package.json`, or an `[project.scripts]` block. These are your real commands.
- `CHANGELOG.md` or recent releases: what shipped lately. Good source for fresh angles.
- Top-level `src/` structure: the domain model. Folder names map to features.
- Example or config files the project ships: only treat a config format as real if it exists in the repo.

## Local checkout commands

```bash
# Map the structure without noise
find . -maxdepth 2 -type d -not -path '*/node_modules/*' -not -path '*/.git/*'

# Read positioning and quickstart
cat README.md

# Find real CLI commands
cat package.json | grep -A30 '"scripts"'
ls bin/ cmd/ 2>/dev/null

# Recent changes for fresh angles
git -C . log --oneline -20 2>/dev/null
cat CHANGELOG.md 2>/dev/null | head -60
```

## GitHub API (no local checkout)

```bash
# Repo metadata: description, language, topics
curl -s https://api.github.com/repos/{owner}/{repo}

# README, decoded
curl -s https://api.github.com/repos/{owner}/{repo}/readme \
  -H "Accept: application/vnd.github.raw"

# Top-level tree
curl -s https://api.github.com/repos/{owner}/{repo}/contents/
```

For private repos, add `-H "Authorization: Bearer $TOKEN"` where `$TOKEN` is the env var named in `secrets`.

## Output: the product brief

Write 6 to 10 lines covering:

- One-sentence description of what the product does.
- The 3 to 5 primary features, in plain language.
- Real commands or API calls, copied from the repo, not invented.
- Language and stack, if relevant to the audience.
- Who uses it and the problem it removes.

## Accuracy rule

Code examples in the post may only use commands, flags, endpoints, and config formats that you saw in the repo or docs. If you are unsure something exists, leave it out. Inventing a flag or a config file is the most common way these posts lose trust.
