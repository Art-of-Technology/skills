# Design principles with concrete fixes

Contents: hierarchy, spacing, type scale, colour, depth, tables and density, forms, states, motion, microcopy, token proposal.

## Hierarchy

Rank the elements on the screen before touching any style. One primary action. One primary piece of information. Everything else supports.

Weight and colour outrank size. A 14px semibold label in full-strength foreground reads as more important than 18px regular in muted grey, and it costs less vertical space. Reach for size last.

```tsx
// before: three competing calls to action
<Button>Save</Button>
<Button>Duplicate</Button>
<Button>Archive</Button>

// after: one primary, the rest recede
<Button>Save changes</Button>
<Button variant="outline">Duplicate</Button>
<Button variant="ghost">Archive</Button>
```

Emphasis by de-emphasis works better than emphasis by addition. Instead of making the important thing louder, make its neighbours quieter.

## Spacing

One scale, 4px based: 4, 8, 12, 16, 24, 32, 48, 64. Anything off it is a finding.

Proximity encodes relationship. A label 4px from its value and 24px from the next pair needs no divider. Equal spacing everywhere forces borders to do work that space should do.

```tsx
// before: dividers compensating for uniform spacing
<div className="space-y-3 divide-y">
  <Row label="Email" value={email} />
  <Row label="Phone" value={phone} />
</div>

// after: grouping by space
<dl className="space-y-6">
  <div className="space-y-1">
    <dt className="text-xs text-muted-foreground">Email</dt>
    <dd className="text-sm">{email}</dd>
  </div>
</dl>
```

Give whitespace to the outside before the inside. Cramped padding inside a card with a huge gap between cards reads backwards.

## Type scale

Five or six sizes app-wide: 12, 14, 16, 20, 24, 32. Line height falls as size rises: 1.6 for body, 1.2 for headings. Prose line length 45 to 80 characters, so `max-w-prose` on paragraphs.

Numbers in columns need tabular figures or digits jitter as values change: `font-variant-numeric: tabular-nums`, or `tabular-nums` in Tailwind. Right-align numerics, left-align text, and never centre either in a table.

Two families maximum. Weight range does the differentiating.

## Colour

Build the interface in greys first and add accent last. If the layout only reads once colour arrives, the hierarchy is not working.

Semantic colours mean one thing each and never overlap. Colour alone never carries meaning: pair status colour with an icon or text label, since roughly 1 in 12 men has some colour vision deficiency.

Backgrounds carry state more calmly than borders. A selected row as `bg-accent` reads better than a 2px accent border shifting content by two pixels.

## Depth

Pick one system and hold it. Either shadows for elevation or surface lightness for elevation, not both. Shadows stay soft and large, never a 1px hard drop. Two elevation levels cover most interfaces: resting and floating.

Dark mode inverts nothing. Shadows disappear on dark surfaces, so elevation becomes lighter surface. Avoid pure black under white text; the contrast is harsh and halos. Start around `#0B0D10` with surfaces stepping lighter.

## Tables and density

Density is the feature in a CRM. Users scan hundreds of rows.

- Row height 36 to 44px. Comfortable and compact modes if users disagree.
- Sticky header. Sticky first column when horizontal scroll exists.
- Truncate with `truncate` plus a `title` attribute or tooltip holding the full value.
- Sortable columns show current sort direction and are keyboard reachable.
- Row actions visible on touch, not hover-only. A trailing actions column beats hidden reveal.
- Alternate zebra striping or a hover row highlight, never both.
- Column widths stable across pages so the eye keeps its position.
- Selection state on the row, count and bulk actions in a bar that appears without shifting the table.

## Forms

Label above the control. Placeholder-only labels vanish on focus and fail accessibility.

Field width signals expected input. A postcode field at 8ch, a name at 24ch, a note full width. A uniform 100% width on every field looks tidy and teaches nothing.

Validate on blur and on submit. Per-keystroke errors punish typing. Error text sits directly under the field, names the problem and the fix, and the field gets `aria-invalid` plus `aria-describedby`.

Mark required fields, not optional ones, unless most fields are required. Group related fields with a `fieldset` and a `legend`. Submit stays enabled and reports errors on click; a disabled submit with no explanation is a dead end.

## The states nobody builds

Every data view needs five renders.

- Loading: skeleton matching final dimensions. Same row count, same heights. A spinner is acceptable only for actions, not for content areas.
- Empty, first run: name the action. "No contacts yet. Import a CSV or add one." Not "No data".
- Empty, filtered: distinguish it. "No contacts match 'acme'. Clear filters."
- Error: what failed, what to do, a retry control. Never an empty list standing in for a failed request.
- Long content: the longest realistic string in every label. German labels and 60-character company names break layouts that placeholder text survives.

## Motion

Duration 150 to 250ms for UI transitions. Ease-out for entry, ease-in for exit. Longer reads as sluggish, shorter reads as a jump.

Animate transform and opacity. Animating height, width, or layout properties causes jank.

Respect the system preference:

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

Never stagger-animate a long list on load. It delays the content the user came for.

## Microcopy

Buttons name the outcome. "Save changes", "Send invoice", "Delete contact". Never "Submit" or "OK".

Keep one word per action across the whole flow. A button saying "Publish" produces a toast saying "Published", not "Successfully saved".

Sentence case throughout. Title Case On Every Label reads dated and slows scanning.

Errors state the fact and the next step, without apology and without blame. "Card declined. Try another card or contact your bank." Not "Sorry, something went wrong."

Name things as the user recognises them. A person manages notifications, not webhook subscriptions.

## Token proposal when none exists

When the project has no declared scale, propose one as finding number one. Everything else stays unfixable without it.

```css
:root {
  /* spacing: 4px base, use Tailwind defaults, no arbitrary values */
  --radius: 0.5rem;

  /* type: 12 / 14 / 16 / 20 / 24 / 32 */

  /* greys carry the UI */
  --background: 0 0% 100%;
  --foreground: 222 22% 11%;
  --muted: 220 14% 96%;
  --muted-foreground: 220 9% 42%;   /* 4.6:1 on background */
  --border: 220 13% 91%;

  /* one accent for action */
  --primary: 221 83% 45%;
  --primary-foreground: 0 0% 100%;

  /* semantic, one meaning each */
  --destructive: 0 72% 42%;
  --success: 142 60% 32%;
  --warning: 32 90% 40%;
}
```

Then the rule that keeps it honest: no hex value and no arbitrary bracket value in component code. Every exception gets justified in review.
