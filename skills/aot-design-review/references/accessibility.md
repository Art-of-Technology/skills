# Accessibility: measurable checks

Contents: automated pass, contrast, focus, targets, accessible names, keyboard traversal, semantics and landmarks, reduced motion, forms, live regions, contrast script.

These items have pass criteria. Measure them and report numbers. No taste debate available.

## Start with the automated pass

```bash
# against a running dev server
npx --yes @axe-core/cli http://localhost:3000/<route> 2>/dev/null || echo "axe unavailable"

# lighthouse accessibility category only
npx --yes lighthouse http://localhost:3000/<route> \
  --only-categories=accessibility --quiet --chrome-flags="--headless" \
  --output=json --output-path=/tmp/dr-a11y.json 2>/dev/null
```

Automated tools catch roughly a third of real issues. They find missing names and contrast failures. They miss wrong hierarchy, illogical tab order, and unusable keyboard flows. Run them first, then check the rest by hand.

## Contrast

Thresholds: 4.5:1 for text under 18.66px regular or under 24px bold. 3:1 for larger text. 3:1 for UI component boundaries and focus indicators. Decorative graphics are exempt.

Measure the resolved colours, not the token names. A `text-muted-foreground` passing on `--background` sometimes fails on `--muted` used as a card surface. Check every surface the text actually sits on.

Common failures worth checking directly: placeholder text, disabled labels, muted metadata on tinted cards, white text on brand accent, text over photographs, chart legends and axis labels, and pale borders defining inputs.

Text over images needs a scrim, not hope: a gradient overlay to roughly 60% opacity behind the text region.

## Focus

Every focusable element needs a visible indicator. `outline: none` without a replacement is a 🔴.

```css
/* keyboard users get the ring, mouse users do not */
:focus-visible {
  outline: 2px solid hsl(var(--ring));
  outline-offset: 2px;
}
```

The ring needs 3:1 against its background, including on accent-coloured buttons where a same-hue ring disappears. Offset it so it does not blend into the control edge. Check it inside modals, on dark surfaces, and on the selected row of a table.

Focus order follows visual order. Positive `tabIndex` values break that; only `0` and `-1` are acceptable.

Modals trap focus, return it to the trigger on close, and close on Escape. Radix primitives handle this, hand-rolled dialogs usually do not.

## Target size

44px minimum on touch. 24px minimum on pointer with adequate spacing. Measure the hit area, not the icon.

```tsx
// before: 16px icon, 16px target
<button onClick={remove}><X className="h-4 w-4" /></button>

// after: 40px target, same visual weight, plus a name
<button
  onClick={remove}
  aria-label="Remove contact"
  className="inline-flex h-10 w-10 items-center justify-center rounded-md hover:bg-muted"
>
  <X className="h-4 w-4" aria-hidden="true" />
</button>
```

Adjacent small targets are worse than one small target. Table row action clusters need spacing between them.

## Accessible names

Every control has a name in the accessibility tree. Icon-only buttons need `aria-label`. Decorative icons inside labelled buttons need `aria-hidden="true"` so the name does not duplicate.

Inputs need a real association: `<label htmlFor>` matching `id`, or `aria-label` where no visible label exists. `placeholder` is not a name.

Links need text describing the destination. "Read more" repeated eleven times is useless in a link list. Images need `alt`, and decorative images need `alt=""` rather than an omitted attribute.

## Keyboard traversal

Walk the screen with Tab, Shift+Tab, Enter, Space, Escape, and arrow keys. Note anything unreachable or trapped.

Checks that catch most failures: every action reachable without a mouse, no hover-only disclosure hiding functionality, dropdowns and comboboxes navigable with arrows, tables with sortable headers activatable by keyboard, Escape closing every overlay, and a skip-to-content link as the first focusable element on pages with long navigation.

`onClick` on a `div` is a 🔴. Use a `button`, which brings keyboard activation and role for free.

## Semantics and landmarks

Native elements before ARIA. A `button` is better than a `div role="button"` every time.

One `h1` per page. Headings descend without skipping levels; they are the document outline screen reader users navigate by, not a font-size picker.

Landmarks present: `header`, `nav`, `main`, `aside`, `footer`. Multiple navs get distinguishing `aria-label` values.

Lists marked up as lists. Definition data as `dl` / `dt` / `dd`. Tables as `table` with `th` and `scope`, since a grid of divs tells a screen reader nothing.

## Reduced motion

Honour `prefers-reduced-motion: reduce`. Parallax, autoplaying carousels, and large-scale entry animation cause nausea and vestibular symptoms for some users. Reduce to a near-instant opacity change rather than removing the state transition entirely.

## Forms

Errors need three things: adjacency to the field, specific wording, and programmatic association.

```tsx
<label htmlFor="email">Work email</label>
<input
  id="email"
  type="email"
  aria-invalid={!!error}
  aria-describedby={error ? 'email-error' : undefined}
/>
{error && (
  <p id="email-error" className="text-sm text-destructive">
    Enter a valid email, for example name@company.com
  </p>
)}
```

On submit failure, move focus to the first invalid field or to an error summary. Silent failure below the fold looks like a broken button.

Autocomplete attributes on personal fields reduce typing and help assistive tech: `autoComplete="email"`, `"tel"`, `"postal-code"`, `"name"`.

## Live regions

Content changing without a page navigation needs announcing. Toasts, save confirmations, async validation results, and search result counts go in `aria-live="polite"`. Errors interrupting the user use `assertive`, sparingly. A count of results updating silently leaves screen reader users unaware anything happened.

## Contrast script

Run this to check pairs quickly rather than estimating.

```bash
cat > /tmp/contrast.mjs <<'EOF'
const lin = c => { c /= 255; return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4 }
const lum = ([r, g, b]) => 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)
const hex = h => {
  const s = h.replace('#', '')
  const f = s.length === 3 ? [...s].map(c => c + c).join('') : s
  return [0, 2, 4].map(i => parseInt(f.slice(i, i + 2), 16))
}
const ratio = (a, b) => {
  const [x, y] = [lum(hex(a)), lum(hex(b))].sort((p, q) => q - p)
  return (x + 0.05) / (y + 0.05)
}
// edit these pairs: [foreground, background, label]
const pairs = [
  ['#9CA3AF', '#FFFFFF', 'muted text on white'],
  ['#FFFFFF', '#2563EB', 'button label on primary'],
]
for (const [fg, bg, label] of pairs) {
  const r = ratio(fg, bg)
  const body = r >= 4.5 ? 'PASS' : 'FAIL'
  const large = r >= 3 ? 'PASS' : 'FAIL'
  console.log(`${label}: ${r.toFixed(2)}:1  body ${body}  large/UI ${large}`)
}
EOF
node /tmp/contrast.mjs
```

Report the ratio and the required threshold in every contrast finding. A number ends the argument.
