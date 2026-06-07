---
name: cmux-browser
description: Drive the cmux browser from the command line to navigate, inspect, and interact with web pages (open URLs, click, type, fill forms, read text, take screenshots, manage cookies/state). Use this skill whenever the user says they want to use "cmux browser", "the cmux browser", "cmux browser automation", or asks you to open / navigate / click / scrape / screenshot a page using cmux — even if they only say "use cmux to open X" or "do this in cmux's browser." It explains the `cmux browser` CLI, surface targeting, and the open→wait→inspect→act→verify workflow so you don't have to guess command syntax.
---

# cmux Browser Automation

The `cmux browser` CLI lets you drive a real browser from the terminal: open pages, wait for them to load, inspect the DOM, click and type, read content, take screenshots, and persist session state. Every command runs through `Bash`.

Official docs: https://cmux.com/docs/browser-automation

## Mental model

- A **surface** is one browser window/webview instance. Most commands need a target surface (e.g. `surface:2`). Open commands don't need a target; almost everything else does.
- You don't get clickable element IDs back. You **inspect** the page (`snapshot`, `get`, `find`), then **act** on it using CSS selectors or accessibility queries (`role`, `testid`, `nth`). There is no "click element #5 from the snapshot" — you translate what you see into a selector.

## The core workflow

Follow this loop. It mirrors how a careful human drives a browser: open, wait until it's actually ready, look at what's there, act, then confirm the action landed.

```
cmux browser open https://example.com/login
cmux browser surface:2 wait --load-state complete --timeout-ms 15000
cmux browser surface:2 snapshot --interactive --compact
cmux browser surface:2 find role button --name "Continue"
cmux browser surface:2 click "button[type='submit']" --snapshot-after
```

1. **Open** the page.
2. **Wait** for readiness before touching anything — pages aren't interactive the instant they open. Wait on a load state, a selector, a text string, or a URL.
3. **Inspect** to learn the current structure (`snapshot` for an overview, `find`/`get`/`is` for specifics).
4. **Act** (`click`, `fill`, `type`, etc.).
5. **Verify** with `--snapshot-after` on mutating commands, or a follow-up `get`/`is`, so you know the action actually changed the page.

## Targeting a surface

If you don't know which surface to use, discover it first:

```
cmux browser identify              # lists active surfaces + metadata
cmux browser identify --surface surface:2
```

Two equivalent targeting forms — positional or flag:

```
cmux browser surface:2 url
cmux browser --surface surface:2 url
```

## Command reference

These are grouped by purpose. Reproduce flags verbatim — `--load-state`, `--timeout-ms`, `--snapshot-after`, `--out`, `--text`, `--attr`, etc.

**Navigation:** `identify`, `open`, `open-split`, `navigate`, `back`, `forward`, `reload`, `url`, `focus-webview`, `is-webview-focused`
```
cmux browser open https://example.com
cmux browser open-split https://news.ycombinator.com
cmux browser surface:2 navigate https://example.com/page2
cmux browser surface:2 url
```

**Waiting** — for selectors, text, URLs, load states, or JS conditions:
```
cmux browser surface:2 wait --load-state complete --timeout-ms 15000
cmux browser surface:2 wait --selector "#checkout" --timeout-ms 10000
cmux browser surface:2 wait --text "Order confirmed"
```

**DOM interaction:** `click`, `dblclick`, `hover`, `focus`, `check`, `uncheck`, `scroll-into-view`, `type`, `fill`, `press`, `keydown`, `keyup`, `select`, `scroll`
```
cmux browser surface:2 fill "#email" --text "ops@example.com"
cmux browser surface:2 type "#search" --text "hello"
cmux browser surface:2 press "#search" --key Enter
cmux browser surface:2 click "button[type='submit']" --snapshot-after
```
- `fill` sets an input's value in one shot; `type` simulates keystrokes (use it when the page reacts to each keypress).

**Inspection:** `snapshot`, `screenshot`, `get`, `is`, `find`, `highlight`
```
cmux browser surface:2 snapshot --interactive --compact
cmux browser surface:2 snapshot --selector "main" --max-depth 5
cmux browser surface:2 screenshot --out /tmp/cmux-page.png
cmux browser surface:2 get title
cmux browser surface:2 get text "h1"
cmux browser surface:2 get attr "a.primary" --attr href
cmux browser surface:2 get count ".row"
cmux browser surface:2 is visible "#checkout"
cmux browser surface:2 is enabled "button[type='submit']"
cmux browser surface:2 find role button --name "Continue"
cmux browser surface:2 find testid "save-btn"
cmux browser surface:2 find nth 2 ".row"
```

**JavaScript:** `eval`, `addinitscript`, `addscript`, `addstyle`
```
cmux browser surface:2 eval "document.title"
cmux browser surface:2 eval --script "window.location.href"
```
Reach for `eval` when no dedicated command fits — e.g. reading computed state or triggering page logic directly.

**Frames / Dialogs / Downloads:** `frame`, `dialog`, `download`

**State management:** `cookies`, `storage`, `state`
```
cmux browser surface:2 state save /tmp/cmux-browser-state.json
cmux browser surface:2 state load /tmp/cmux-browser-state.json
```
Save state after logging in so you can reload the session later instead of re-authenticating.

**Tabs / Logs:** `tab`, `console`, `errors`
```
cmux browser surface:2 console      # page console output
cmux browser surface:2 errors       # page errors — check here when something silently fails
```

## Practical tips

- **Always wait before acting.** Most flaky failures come from interacting before the page is ready. Prefer waiting on a concrete signal (`--selector`, `--text`) over a blind load state when you know what you're expecting.
- **Selectors over guesses.** Inspect with `snapshot`/`find` first; don't invent selectors. Accessibility queries (`find role button --name "..."`) are often more robust than brittle CSS.
- **Verify mutations.** Add `--snapshot-after` to clicks/fills, or follow up with `get text` / `is visible`, so you confirm the page changed rather than assuming it did.
- **When stuck, read the logs.** `console` and `errors` reveal why a page misbehaved.
- **Take a screenshot** (`screenshot --out /tmp/...png`) when you need to actually see the rendered page or show the user what state it's in.
