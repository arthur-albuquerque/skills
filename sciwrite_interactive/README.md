# sciwrite_interactive

A writing-review skill for scientific and engineering manuscripts. The agent reads your draft, runs five audit passes for sentence-level quality, and hands you a **browser editor that behaves exactly like Google Docs' "Suggesting" mode** — each finding becomes a margin card you accept (✓) or reject (✕) with one click. When you click **Save & Finish**, the revised manuscript is written next to the original as `<stem>_revised.md`.

> Heavily inspired by [labarba/sciwrite](https://github.com/labarba/sciwrite). That project produces a static review report; this one keeps the same editorial principles but ships them through an interactive accept/reject editor so you stay in control of every change.

## Premises

The skill applies Dr. Kristin Sainani's *Writing in the Sciences* methodology. Every word must earn its place; every sentence is stripped to its cleanest components. Concretely, the agent runs five passes:

1. **Clutter extraction** — dead-weight phrases ("due to the fact that" → "because"), redundant adjectives ("successful solutions" → "solutions"), throat-clearing intros ("it is worth noting that…").
2. **Active voice & verb vitality** — passive constructions that hide the actor, and "smothered verbs" ("provides a review of" → "reviews").
3. **Sentence architecture** — buried predicates, monotone sentence length, punctuation that could be tightened with a colon, dash, or semicolon.
4. **Keyword consistency & terminology** — the *Banana Rule*: if Methods says "obese group", Results must not switch to "heavier group". Also flags ad-hoc acronyms.
5. **Numerical consistency & citation integrity** — sample sizes that disagree across Abstract/Tables, percentages that don't match raw numbers, statistics cited only through secondary sources.

**What it will not do.** It does not touch scientific content, data, statistical analysis, methods, or citation formatting. It improves *how* the claims are delivered, not the claims themselves.

## How to use it

Point any capable agent (Claude, Cursor, Copilot, …) at your manuscript:

```
/sciwrite_interactive path/to/manuscript.md
```

The skill is agent-agnostic. The only requirements are a shell and Python 3.

### What happens

1. The agent reads your manuscript and runs the five audit passes.
2. It writes a compact `suggestions.json` (only the findings — never re-typing your prose) and a build script splices those findings into a copy of the source.
3. A local server launches and opens the editor in your browser at a free port.
4. You review each suggestion from the right-margin cards:
   - **✓** accepts the change.
   - **✕** rejects it.
   - You can also edit the text directly anywhere on the page.
5. Progress autosaves continuously (the top bar shows "Draft saved").
6. Click **Continue Later** to pause — you can close the tab and resume later. Re-running the skill on the same manuscript will ask whether to continue or start fresh.
7. Click **Save & Finish** to write the revised manuscript next to the original as `<stem>_revised.md`.

### Suggestion cards

Each card shows:

- The **original** text and the **proposed replacement**.
- A short **rationale** (3–6 words, like a margin comment — "Dead-weight phrase", "Passive — name the actor", "Term inconsistent with Methods").
- A **severity** color (critical / major / minor) and a **kind** tag (clutter / voice / architecture / terminology / numbers).

Tables, fenced code blocks, and `$$…$$` math are locked automatically — suggestions never land inside them.

### Supported inputs

- Markdown (`.md`) — read directly.
- Other formats (`.qmd`, `.tex`, `.docx`) — the agent will extract the prose to markdown first, or ask you how to proceed.

## Installation

The skill lives in this repo as `sciwrite_interactive/`. The default install path for Claude is `~/.claude/skills/sciwrite_interactive`. For other agents, place the folder anywhere and set:

```bash
export SCIWRITE_HOME=/path/to/sciwrite_interactive
```

The skill falls back to `~/.claude/skills/sciwrite_interactive` if `SCIWRITE_HOME` is unset.

## Sessions and resuming

Each manuscript gets a stable session directory keyed by its absolute path, stored under `<manuscript-dir>/.sciwrite/<hash>/`. That directory holds the suggestions, the draft document, and the running server's PID/URL — so a review survives browser closes, terminal timeouts, and new agent sessions. The server self-terminates after 30 minutes idle; the draft persists on disk and nothing is lost.

## When *not* to use it

- Technical / content review of methods or results.
- Statistical analysis review.
- Citation formatting (BibTeX, CSL, journal style for references).

For those, reach for a different skill.
