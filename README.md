# Art of Technology Skills

Shared agent skills for Claude Code, Codex, and other coding agents.

## Skills

| Skill | Purpose |
|-------|---------|
| aot-rundown | Concise whole-project status: backlog, in progress, completed, waiting for release, recently released |
| aot-rundown-current | Concise current-session recap: progress, unfinished work, blockers, next action |
| aot-ship-loop | Gate a change through no-mistakes, Octopus Review, CI, and release verification |
| aot-pr-loop | Drive a PR through Octopus Review feedback until 4+/5 |
| aot-skill-audit | Vet a third-party agent skill before installing it: prose injection, code exfiltration, persistence, verdict with evidence |
| aot-security-audit | OWASP-aligned audit for TS/Node and C#/ASP.NET Core |
| aot-nextjs-server-first | Move Next.js data fetching server-side, BFF, RSC |
| aot-design-review | UI review: hierarchy, spacing, a11y, WCAG |
| aot-ci-workflows | Stop wasted Actions runs (concurrency, paths-ignore, draft skip, merge_group), then adopt the org reusable workflows |
| aot-release-lifecycle | Trunk-based release flow: main→staging, rc tag→UAT, release tag→prod, promote-not-rebuild |
| aot-ci-cd-optimization | Measure and speed up CI/CD with parallel checks, cancellation, efficient secret scans and tested-artifact reuse |
| blog-content-agent | Research, write, and publish codebase-aware blog posts |
| aot-brief | Compact replies with DONE, NEXT, BLOCKED, DECIDE; invoke /aot-brief |
| actionable-output | Short, clear, actionable responses: next action first, numbered steps, no tangents |
| humanizer | Strip AI-writing tells from customer-facing copy only: email, web UI strings, marketing, notifications |
| skill-creator | Create, improve, and eval agent skills (Anthropic official, Apache-2.0) |
| frontend-design | Distinctive, non-generic UI design direction: typography, color, motion (Anthropic official, Apache-2.0) |

## Use with Claude Code

Clone and symlink into your user skills directory:

```bash
git clone git@github.com:Art-of-Technology/skills.git ~/art-of-technology-skills
ln -s ~/art-of-technology-skills/skills/* ~/.claude/skills/
```

Update all skills:

```bash
cd ~/art-of-technology-skills && git pull
```

Pulling updates existing linked skills. For newly added skills, also link
their folders into `~/.claude/skills/`; skip links that already exist.

## Use with Codex

For direct `$skill-name` invocation, link the desired skill folders into
`~/.agents/skills/`. For the rundown skills, after cloning as above:

```bash
mkdir -p ~/.agents/skills
ln -s ~/art-of-technology-skills/skills/aot-brief ~/.agents/skills/
ln -s ~/art-of-technology-skills/skills/aot-rundown ~/.agents/skills/
ln -s ~/art-of-technology-skills/skills/aot-rundown-current ~/.agents/skills/
```

Skip links that already exist. Pulling updates linked skills; newly added
skills need new links. If a skill does not appear, restart Codex.

Point AGENTS.md at the skill you need, or paste the SKILL.md content as the task prompt. Example AGENTS.md line:

```
For PR review loops, follow skills/aot-pr-loop/SKILL.md in Art-of-Technology/skills.
```

Or vendor the repo as a submodule and reference files directly:

```bash
git submodule add git@github.com:Art-of-Technology/skills.git .agent-skills
```

## Structure

Each skill is a folder with a SKILL.md entry point. Larger skills add references/, scripts/, and assets/ subfolders. SKILL.md frontmatter carries the name and trigger description.

## Contributing

One skill per PR. Keep SKILL.md under 200 lines. Push detail into references/.

## License

MIT. See [LICENSE](LICENSE). Vendored skills keep their upstream licenses: `humanizer` from [blader/humanizer](https://github.com/blader/humanizer) (MIT), `skill-creator` and `frontend-design` from [anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official) (Apache-2.0, see the `LICENSE.txt` in each folder).

## Compact replies

Enable `aot-brief` with `/aot-brief` in Claude Code, or reference
`skills/aot-brief/SKILL.md` in Codex prompt instructions. For all replies,
add that reference to your standing agent instructions. Its output shape
takes precedence over `actionable-output` when both are enabled.
No hooks, proxy rewriting, or reasoning-effort changes are required.

For a one-off recap, use `/aot-rundown-current` for the current session or
`/aot-rundown` for the whole project in Claude Code. In Codex, invoke
`$aot-rundown-current` or `$aot-rundown`. Both reuse `aot-brief` for that
response only, keeping the existing session style afterwards. Install
`aot-brief` alongside both rundown skills.
