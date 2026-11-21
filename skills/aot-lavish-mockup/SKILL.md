---
name: aot-lavish-mockup
description: Build a clickable, multi-screen UI mockup in Lavish that a person clicks through, compares working layout options on, and approves with one press. Each screen leads with the picture, offers two or three layouts with one marked recommendation, and has a pick form that sends the answer back to you. Use this whenever the user asks to "show me how it will look", wants a mockup or prototype of planned screens before they are built, asks for options with your recommendation, wants to approve a refactor's UI before issues are filed, or asks for an ADHD-friendly visual of how a system will work, even if they never say "Lavish" or "mockup". Not for a static report or a single diagram (use the lavish skill), and not for building the real feature.
---

# Lavish mockup

A clickable page that lets someone approve planned screens in about ten minutes, instead of reading a description of them.

```
+--------------------------------------------------------------+
| Title · "Sample data. Nothing is saved."                     |
| [1 How it works] [2 Screen] [3 Screen] ... [N Open points]   |   one screen at a time
+--------------------------------------------------------------+
| PART · SCREEN 2 OF N                                         |
| Screen title                                                 |
| One sentence.            [Term = meaning] [Term = meaning]   |   key terms before detail
|                                                              |
| Layout: [A ... my pick] [B ...] [C ...]                      |   working options
| Why A: one line.                                             |
| +----------------------------------------------------------+ |
| |  the app, mocked in its own look, every control works    | |   picture first
| +----------------------------------------------------------+ |
| Your pick: ( ) A  ( ) B  ( ) C   [Queue this answer]         |   one answer per screen
|                                         [Next: Screen 3 ->]  |
+--------------------------------------------------------------+
```

## When it fits

Use it when there are several screens, some layout choices are still open, and the person wants to see and choose before work is filed or built. For one diagram, a comparison table or a report, the plain `lavish` skill is enough. If nothing is undecided, show one version per screen and skip the option bars.

## Steps

1. **List what is decided and what you assumed.** Decisions go into the screens as fact. Each thing you assumed without the person ruling on it becomes a row on the last screen, "Open points". This keeps your guesses from slipping through as if they were agreed.
2. **Read the look of the app being mocked.** Take its colour tokens, type sizes and layout from its own stylesheet or design notes, and mock in that look. A mockup in a foreign style makes people judge the style instead of the layout. If a second product appears and you cannot find its tokens, approximate and say so on that screen.
3. **Load the `lavish` skill and open its playbooks** for `diagram`, `comparison`, `input` and `plan` before writing HTML (`npx -y lavish-axi playbook <id>` prints one when that skill is not installed). They carry the rules for figures (inline SVG, not boxes made of divs) and for sending answers back.
4. **Start from `assets/template.html`.** It has the shell: numbered tabs, the option bar, the app frame, the pick form, the open-points form and the queueing code. Add one entry to `SCREENS` and one `R.<id>` render function per screen.
5. **Make every control do something.** Keep real state in a small object per screen and re-render on each click. Use sample data that looks like the person's actual work. Options are different renderers over the same state, so switching layout keeps what was clicked.
6. **Click through it yourself before anyone sees it.** Follow `references/click-test.md`: a script that presses every control and checks the result, then screenshots of each screen. Do not say it works until the script passes with no console errors.
7. **Open it with `npx -y lavish-axi <file>` and poll with `npx -y lavish-axi poll <file>` in a tracked background job.** Tell the person, in numbered steps with a time estimate, what to click and that pressing "Send to Agent" is the signal.
8. **When the picks arrive, use them.** Write each pick into the issue, plan or note it belongs to, in words (not "layout A" alone). Account for every open point by its id. Keep a lasting copy of the page, for example in the project's ignored `.lavish/` folder, because a temporary folder does not survive a restart.
9. **When the picks become issues, the pictures go with them.** Take a screenshot of each approved screen showing the picked option and attach it to the issue that builds that screen, in whatever tracker the work is filed in (Collab, Jira, Linear, GitHub issues), so the person or agent who builds it sees what was approved without opening the page. Use the tracker's own attachment; where it has none, commit the pictures beside the design note and link them from the issue. Do this every time, without being asked.

## What makes it work

- **One screen at a time.** Tabs, not one long page. The reader holds one thing in mind and always sees "screen 3 of 8".
- **Picture first, words after.** The mock comes before any explanation. Key terms sit above it as short chips, so no term is used before it is defined.
- **First screen shows the system.** An inline SVG figure with a "today / after" switch and a stepper that lights up one step at a time with a one-line caption. It answers "how will this work?" before any single screen.
- **Exactly one pick per choice.** Mark your recommendation on the option tab and in the pick form, with one line of why. Say what the other options cost, so they are real choices and not decoys.
- **Two or three options, only where the layout is open.** A choice on every screen wears the reader out.
- **Native controls.** Build clickable things as `<button>`, inputs, selects, or elements with an ARIA role such as `tab` or `radio`. Lavish treats those as controls; a clickable `div` gets annotated instead of clicked.
- **One queued answer per screen.** Choosing a radio only changes the page. The "Queue this answer" button calls `window.lavish.queuePrompt` once, with a `queueKey` so a changed mind replaces the earlier answer. The open-points form sends all its rows as one tracked batch.
- **No browser dialogs.** `alert`, `confirm` and `prompt` block the page. Use an inline row with an input and an "Add" button.
- **Say what is fake.** "Sample" on anything that looks like a real result, such as a created record or a connected account.
- **Nothing is filed until they send.** Say so in the top bar and on the last screen. People click more freely when they know it is safe.

## The message that goes with the link

Lead with the link and what to do, then what you checked:

```
**Your mockup is open: <link>**

1. Click through the N tabs, left to right (about 10 minutes). Everything is clickable; nothing is saved.
2. Under screens ..., choose a layout and press "Queue this answer". My pick is marked.
3. On the last screen, answer the open points and press "Queue these answers".
4. Press "Send to Agent". That is my signal to <what happens next>.

Checked before sending: every control clicked (<n> checks pass, no console errors), screenshots of <which> screens.
Not checked: <for example phone width>.
```

## Files

- `assets/template.html`: the working shell with three sample screens. Copy it and replace the samples.
- `references/click-test.md`: how to click through the page without a person, with a script to adapt.
