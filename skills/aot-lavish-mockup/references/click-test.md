# Click through the mockup before anyone sees it

A mockup that breaks on the second click costs the person's trust in everything else on the page. So press every control yourself first, with a script, then look at screenshots.

## 1. Open the file in a headless browser

Any driver works (a DevTools-based CLI, Playwright, Puppeteer). Open the file directly with a `file://` address; Lavish is not needed for this step. Read the console right after loading: it must be empty.

## 2. Run one script that presses everything

Keep the script in its own file and pass it to the driver's evaluate command. Many evaluate commands take an expression, not statements, so wrap the script in an async function that is called at once and returns a JSON string.

```js
(async () => {
  const out = [], errs = [];
  window.addEventListener('error', e => errs.push(String(e.message)));
  const cur = () => document.querySelector('.screen:not([hidden])');
  const click = (sel, txt) => {
    const el = [...cur().querySelectorAll(sel)].find(e => !txt || e.textContent.includes(txt));
    if (!el) throw new Error('no element ' + sel + ' ' + (txt || ''));
    el.click(); return el;
  };
  const go = i => document.querySelectorAll('#nav button')[i].click();
  const ok = (name, cond) => out.push((cond ? 'PASS ' : 'FAIL ') + name);
  const text = () => cur().textContent;
  const lay = v => click('.optbar button[data-v="' + v + '"]');
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  try {
    go(1);
    click('.lrow', 'First item');           ok('item opens its detail', text().includes('Detail of'));
    lay('B');                               ok('layout B shows cards', cur().querySelectorAll('.fcard').length > 0);
    // ... one line per control ...
    for (let i = 0; i < document.querySelectorAll('#nav button').length; i++) {
      go(i);
      if (document.documentElement.scrollWidth > window.innerWidth + 1) out.push('FAIL sideways scroll on screen ' + (i + 1));
    }
  } catch (e) { out.push('ERROR ' + e.message); }
  return JSON.stringify({ pass: out.filter(x => x.startsWith('PASS')).length, notPass: out.filter(x => !x.startsWith('PASS')), errs });
})()
```

What the script should cover:

| Cover | Why |
| --- | --- |
| Every button and tab at least once | A dead control is the first thing a person finds. |
| Every layout option of every screen | Options share state; one renderer often lags behind the others. |
| The empty path of every form (submit with nothing typed) | It should show an inline hint, not fail silently. |
| Each flow to its end (create, send, approve) | The last step is the one most often left unwired. |
| Anything timed (a simulated wait) | Wait for it in the script and check the state afterwards. |
| Sideways scroll on every screen | Wide chips and tables overflow without anyone noticing. |
| The pick forms and the open-points form | Without Lavish they should say the answer is selected, not throw. |
| Fill in a form, go to another screen, come back | A screen that is rebuilt on every click forgets what was typed and chosen. |

Set a select's value and dispatch a `change` event to drive it; a script-set value alone does not fire one.

Run the script again after every edit. It takes seconds.

## 3. Look at it

The script proves the controls work, not that the page reads well. Take a screenshot of each screen and look for: text that is too dim to read, a figure whose labels overlap, controls stretched to full width by accident, and a caption that says something the picture does not show. A narrow window (phone width) is worth one screenshot when the person may open it on a phone.

## 4. Report what you checked

Say the number of checks, that the console was empty, which screens you looked at, and what you did not check. Do not write "tested" without those.
