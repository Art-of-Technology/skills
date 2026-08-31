---
name: aot-design-review
description: Review a web UI against visual design, interaction, and accessibility principles, then produce a prioritized findings report with concrete code fixes. Use this skill whenever the user asks to "review the UI", "review the design", "run a design review", "run aot-design-review", "does this look good", "make this look better", "the UI feels off", "improve the layout", "critique this screen", or mentions visual hierarchy, spacing, type scale, design tokens, contrast ratios, WCAG, focus states, touch targets, empty states, loading skeletons, layout shift, dark mode, or responsive breakpoints. Also trigger when reviewing a new component, dashboard, form, or data table before shipping, or when the user shares a screenshot or a Figma frame and wants feedback. Covers React, Next.js, Tailwind, and shadcn/ui. Even if the user does not say "review", use this skill when they want UI quality checked.
---

# aot-design-review

Review a UI and return a prioritized, fixable report. Inspect the tokens, read the component code, capture screenshots at real breakpoints, check the states nobody builds, then score and report. Apply fixes only after the user confirms.

Design feedback fails in two directions. Vague taste notes nobody can act on, and pedantic nitpicks that miss a broken hierarchy. Avoid both: every finding names a location, an effect on the user, and a specific change.

## What you produce

- Summary: stack detected, screens reviewed, breakpoints checked, counts by severity, a score out of 5.
- Findings table: ID, severity, category, location, one-line issue, one-line fix.
- Per-finding detail with the fix as code in the project's own token vocabulary.
- A token audit: the scales in use versus the scales declared.
- Screenshots at each breakpoint where available, before and after if fixes get applied.
- A remediation plan ordered by severity.

## Scope before reviewing

Infer these. Confirm only what you cannot.

1. Target. A component, a screen, a flow, or a whole app. Default to what the user last mentioned or the diff in the working tree.
2. Inputs available. Source code, a running dev server, screenshots, a Figma file. Say which you used. A review from source alone misses rendered spacing and contrast, so state that limit rather than pretending to see the pixels.
3. Mode. Report-only, or report then fix. Default to report-only.
4. Product register. An internal CRM optimises for density, scanning, and keyboard speed. A marketing page optimises for a first impression. The same spacing is right in one and wrong in the other. Get this right before scoring anything.

## Step 1: Detect the design system

```bash
cat package.json 2>/dev/null | grep -E '"(tailwindcss|@radix-ui|lucide-react|next|clsx|tailwind-merge|framer-motion)"'
ls tailwind.config.* components.json app/globals.css src/styles 2>/dev/null
grep -rn "--(background|foreground|primary|muted|border|radius)" --include='*.css' . 2>/dev/null | head -30
ls -R components/ui 2>/dev/null | head -40
```

Record what exists: a token set, shadcn primitives, an ad-hoc mix. A project with declared tokens gets judged against them. A project without them gets a token proposal as finding one, because inconsistency has no fix until a scale exists.

Read `references/principles.md` before writing any critique, and `references/accessibility.md` before scoring contrast, focus, or keyboard findings.

## Step 2: Look at the rendered UI

Static code review misses the things users see. Capture screenshots when a dev server runs.

```bash
npx --yes playwright screenshot --viewport-size=1440,900 --full-page \
  "http://localhost:3000/<route>" /tmp/dr-desktop.png 2>/dev/null || echo "no dev server"
npx --yes playwright screenshot --viewport-size=390,844 --full-page \
  "http://localhost:3000/<route>" /tmp/dr-mobile.png 2>/dev/null
```

Then view the images. Judge the screenshot, not the intent of the code.

Breakpoints worth checking: 390 (phone), 768 (tablet), 1280 (laptop), 1920 (wide). A CRM breaks most often at 1280 with a sidebar open, and at 768 where tables collapse.

Also check the states that rarely get built. Each is a separate screenshot: loading, empty, single item, long content overflow, error, and the longest realistic string in every label. A layout only holding together with placeholder text is broken.

## Step 3: Review against the checklist

Order reflects how much each item affects a user getting work done.

1. Hierarchy. The primary action and primary information read first. One primary button per view. Weight, size, and colour reinforce the same order instead of competing. If everything is bold, nothing is.
2. Contrast and legibility. Body text meets 4.5:1, large text and UI components 3:1. Muted text stays readable, placeholder text is not a substitute for a label, text over images has a scrim.
3. Spacing consistency. Every gap comes from one scale, typically 4px based. Related items sit closer than unrelated items. Space groups content instead of borders and dividers doing that job.
4. Type scale. Five or six sizes across the app, not eleven. Line height rises as size falls. Line length stays between 45 and 80 characters for prose. Numeric columns use tabular figures.
5. Colour discipline. Greys carry the interface, one accent carries action, semantic colours mean one thing each. Colour never carries meaning alone, since status by colour excludes colour-blind users.
6. Alignment and rhythm. Shared left edge, consistent optical alignment of icons to text, form labels and controls on the same grid.
7. Interactive states. Every control has hover, active, focus-visible, disabled, and loading. Focus rings visible against every background. Disabled controls explain why, adjacent to the control.
8. Touch and pointer targets. Minimum 44px on touch, 24px with spacing on pointer. Icon-only buttons carry an accessible name and a tooltip.
9. Empty, loading, error states. Empty screens name the next action. Skeletons match final dimensions to avoid shift. Errors say what failed and what to do. Never a bare spinner where a skeleton fits.
10. Forms. Labels above or beside, never placeholder-only. Errors adjacent and specific. Validation on blur and submit, not per keystroke. Required marked. Inputs sized to expected content, so a postcode field is not 400px wide.
11. Data tables and density. Sticky header, aligned numerics, sensible truncation with the full value on hover, sortable columns marked, row actions discoverable without hover on touch. Density is a feature in a CRM.
12. Feedback and motion. Every action gets a response inside 100ms, even if only a pressed state. Transitions 150 to 250ms with an ease-out curve. Motion respects `prefers-reduced-motion`. No animation on entry of long lists.
13. Responsive behaviour. Nothing overflows horizontally. Tables become cards or scroll containers with intent. Sidebars collapse to a defined pattern. Modals fit small viewports.
14. Copy in the interface. Buttons name the outcome, so "Save changes" not "Submit". The same action keeps the same word across the flow. Sentence case. Errors avoid apology and vagueness.
15. Consistency against the token set. Arbitrary values such as `p-[13px]` or `#3B7FE0` where a token exists. Duplicate components diverging in radius, shadow, or padding.
16. Dark mode, when present. Not an inverted palette. Elevation by surface lightness, not shadow. Borders remain visible. No pure black background under white text.
17. Icon use. Consistent set, consistent size and stroke weight, aligned to text baseline, never decorative filler.
18. Signature and restraint. One memorable element per product view, everything else quiet. Cut decoration that carries no information. Then look again and remove one more thing.

Record location, effect, and fix for each hit.

## Step 4: Triage and score

- 🔴 Critical. Blocks use or excludes users: contrast failure on body text, no visible focus state, target under 24px, content clipped at a supported breakpoint, unlabelled control.
- 🟠 High. Costs the user time or attention: broken hierarchy, competing primary actions, inconsistent spacing inside one view, missing empty or error state, skeleton causing shift.
- 🟡 Medium. Polish gap: arbitrary values off the scale, minor alignment drift, weak microcopy, motion not respecting reduced motion.
- 🔵 Low. Preference and refinement, flagged as opinion.

Then score out of 5, matching the quality gate used elsewhere in the workflow.

- 5: Coherent, accessible, tokens respected, every state built, distinctive.
- 4: Coherent and accessible. Minor polish gaps only. This is the pass bar.
- 3: Works, reads as templated or inconsistent. Some states missing.
- 2: Hierarchy or accessibility problems affecting daily use.
- 1: Unusable at a supported breakpoint, or fails basic accessibility.

Separate fact from taste. Contrast ratios and target sizes are measurements. Palette and type pairing are judgement, so label them as opinion and give the reasoning. Never present taste as a standard.

## Step 5: Report

Use this exact structure.

```markdown
# Design Review: <target>

**Stack:** <detected> | **Reviewed:** <routes or components> | **Breakpoints:** 390 / 768 / 1280
**Inputs:** <source, screenshots, Figma> | **Date:** <date>
**Score:** N/5 | **Findings:** 🔴 N  🟠 N  🟡 N  🔵 N

## What works
- <two or three specifics worth keeping, with locations>

## Findings
| ID | Sev | Category | Location | Issue | Fix |
|----|-----|----------|----------|-------|-----|
| 1 | 🔴 | Contrast | ContactCard.tsx:34 | Muted label at 2.9:1 on card surface | Use text-muted-foreground token, 4.6:1 |

## Detail
### 1. 🔴 Body label fails contrast
**Location:** components/ContactCard.tsx:34
**Effect:** Secondary labels unreadable in daylight and for low-vision users. Ratio 2.9:1 against 4.5:1 required.
**Fix:**
\`\`\`tsx
// before
<span className="text-gray-400">Last contacted</span>
// after
<span className="text-muted-foreground">Last contacted</span>
\`\`\`

## Token audit
| Property | Declared scale | Values found in code | Off-scale hits |
|---|---|---|---|
| Spacing | 4px steps | 4, 6, 8, 13, 15, 16, 24 | 13px, 15px |

## State coverage
| Screen | Loading | Empty | Error | Long content | Mobile |
|---|---|---|---|---|---|
| /contacts | skeleton mismatch | missing | missing | truncates | table overflows |

## Remediation plan
1. <highest severity first>
```

Stop here in report-only mode.

## Step 6: Fix loop (only after confirmation)

1. Show the findings table with the proposed change per row. Wait for confirmation.
2. Fix accessibility findings first. They have objective pass criteria and no taste debate.
3. Use existing tokens and components. Introducing a new colour or a new spacing step is a token change requiring the user's agreement.
4. Screenshot after each group of fixes at the same breakpoints and compare against the before shot.
5. Re-run the checklist items touched to catch regressions.
6. If an open PR exists, hand the commit and review cycle to `aot-pr-loop`.

## Hard rules

- Never commit or push without explicit confirmation.
- Name a location for every finding. No unlocatable critique.
- State the effect on the user. A rule quoted without a consequence is noise.
- Measure, do not estimate, contrast ratios and target sizes.
- Label opinion as opinion.
- Never propose a redesign when the finding is a spacing bug.
- Match the product register. Do not push marketing-page airiness onto a dense internal tool.
- Say which inputs the review used, and what a missing input prevented you seeing.
- Lead with what works, briefly and specifically. Not padding, calibration.

## Reference files

- `references/principles.md` — Hierarchy, spacing, type scale, colour, depth, tables and density, motion, microcopy. Before-and-after snippets per checklist item.
- `references/accessibility.md` — Contrast maths and how to measure, focus-visible patterns, target sizing, accessible names, keyboard traversal, reduced motion, screen-reader-relevant markup, and a check script.
