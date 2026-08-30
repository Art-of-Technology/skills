# Writing Guide

All numeric limits and lists here have config defaults. If the config sets `writing.minWords`, `writing.maxWords`, `writing.titleMaxChars`, `writing.seoKeywords`, or `writing.bannedTerms`, use those values over the defaults below.

## Title

- Max 60 characters (default; SEO hard limit).
- Lead with a hook: a number, a bold claim, or a curiosity gap.
- Hint at the specific angle, not a broad topic label.
- Original every time. No pre-written or generic title.

Good: "Why Codebase Context Beats Diff-Only Review" / "Your CI Is Slow. Here Is the Fix."
Bad: "The Future of X" / "How AI Is Changing Y"

## Length

- 800 to 1200 words (default). Count them. Under the floor reads thin, over the ceiling reads bloated.

## Structure

1. **Hook** (1 to 2 sentences): open with the stat, pain point, or claim from research. No "in today's fast-paced world" openers.
2. **Problem** (200 to 400 words): what is broken right now, with concrete examples. "Review queues are 3 days deep so teams mass-approve" beats "review is slow."
3. **Product** (300 to 500 words): how the product solves it. Pick 1 or 2 features most relevant to this topic and go deep. Describe through a scenario, not a spec sheet. The product is the primary tool in the narrative.
4. **Code or architecture example**: at least one block, using only real commands or APIs from the repo brief.
5. **CTA** (2 to 3 sentences): one clear next step. Vary the phrasing across posts.

## Tone

- Technical but conversational. Write like a senior engineer on a dev blog, not a marketing team.
- Use "you" and "your team".
- Short paragraphs, 3 to 4 sentences max.
- Subheadings to break up sections.
- No em dashes. Use commas, colons, or periods.

## Competitors

Never name a competing tool. Refer to alternatives generically: "most tools", "traditional approaches", "diff-only tools". Use industry trends as the backdrop, then position the product as the answer.

## SEO

Weave the keywords from `writing.seoKeywords` naturally into the body. Do not stuff them. Always include the product name a few times in context.

## Code honesty

Code examples may only use commands, flags, endpoints, and config formats verified in the repo brief. Never invent a config file format or a CLI flag. If unsure it exists, leave it out.

## Topic rotation

Five categories. Never run two consecutive posts from the same one.

| Category | Focus | Example angles |
|----------|-------|----------------|
| pain-point | A specific user frustration the product fixes | false positives, review fatigue, context switching |
| trend-analysis | Industry trend plus product positioning | AI-generated code quality, shift-left, privacy |
| how-to | Practical guide using the product | self-hosting setup, CLI workflows, config |
| deep-dive | Technical internals or approach | how a subsystem works, design tradeoffs |
| opinion | Engineering-culture take with a product tie-in | review as mentorship, async culture, open source trust |

## Self-review scorecard

Score 1 to 5 on each. Show per-criterion scores and the average. Below 4.0 average, rewrite and re-score.

| Criterion | 1 (Fail) | 5 (Excellent) |
|-----------|----------|---------------|
| Product focus | Product barely mentioned | Product is the hero, woven in naturally |
| No competitor mentions | Names a competitor | Zero competitor names |
| Uniqueness | Same topic and angle as an existing post | Fresh topic and angle, clearly distinct |
| Hook quality | Generic opener | Specific stat or pain point, compelling |
| Technical depth | No code, reads like marketing | Real code, engineer-level insight |
| Accuracy | Invented features, flags, or config | Every command and feature verified |
| Freshness | Repeats the same feature as prior posts | Different feature, different scenario |
| SEO keywords | Missing or stuffed | Flow naturally in the text |
| Word count | Under 700 or over 1300 | Within range, well-paced |
