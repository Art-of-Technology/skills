# Art of Technology Skills

Shared agent skills for Claude Code, Codex, and other coding agents.

## Skills

| Skill | Purpose |
|-------|---------|
| cem-pr-loop | Drive a PR through Octopus Review feedback until 4+/5 |
| cem-security-audit | OWASP-aligned audit for TS/Node and C#/ASP.NET Core |
| cem-nextjs-server-first | Move Next.js data fetching server-side, BFF, RSC |
| cem-design-review | UI review: hierarchy, spacing, a11y, WCAG |
| blog-content-agent | Research, write, and publish codebase-aware blog posts |

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

## Use with Codex

Point AGENTS.md at the skill you need, or paste the SKILL.md content as the task prompt. Example AGENTS.md line:

```
For PR review loops, follow skills/cem-pr-loop/SKILL.md in Art-of-Technology/skills.
```

Or vendor the repo as a submodule and reference files directly:

```bash
git submodule add git@github.com:Art-of-Technology/skills.git .agent-skills
```

## Structure

Each skill is a folder with a SKILL.md entry point. Larger skills add references/, scripts/, and assets/ subfolders. SKILL.md frontmatter carries the name and trigger description.

## Contributing

One skill per PR. Keep SKILL.md under 200 lines. Push detail into references/.
