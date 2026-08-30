#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------------------------------------
# Art-of-Technology/skills bootstrap
# Run from inside the unpacked skills-repo folder, where gh is authenticated.
# Idempotent: safe to re-run.
# ---------------------------------------------------------------------------

ORG="Art-of-Technology"
REPO="skills"
VISIBILITY="private"

OWNER_REPO="$ORG/$REPO"

log() { printf '\n>> %s\n' "$1"; }

log "Checking gh auth"
gh auth status

log "Ensuring repo $OWNER_REPO"
if ! gh repo view "$OWNER_REPO" > /dev/null 2>&1; then
  gh repo create "$OWNER_REPO" --"$VISIBILITY" \
    --description "Shared agent skills for Claude Code, Codex, and other coding agents"
  log "Repo created"
else
  log "Repo already exists"
fi

log "Initializing git"
if [ ! -d .git ]; then
  git init -b main
fi

git add .
if git diff --cached --quiet; then
  log "Nothing new to commit"
else
  git commit -m "feat: initial skill library

- cem-pr-loop: Octopus Review PR loop to 4+/5
- cem-security-audit: OWASP audit for TS/Node and ASP.NET Core
- cem-nextjs-server-first: server-side data fetching refactor
- cem-design-review: UI and accessibility review
- blog-content-agent: codebase-aware blog content pipeline
"
fi

if ! git remote get-url origin > /dev/null 2>&1; then
  git remote add origin "git@github.com:$OWNER_REPO.git"
fi

log "Pushing to $OWNER_REPO"
git push -u origin main

log "Done: https://github.com/$OWNER_REPO"
