# skills

A collection of skills for AI agents.

## Skills

### `implement_plan`

Execute a plan or spec file by reading it and implementing its contents. Triggered when you provide a path to a plan, spec, or design document and want it implemented — even if you just drop a file path and say "do it."

It's great because the agent keeps a running HTML log of design decisions, deviations, tradeoffs, and open questions as it works — so you get a transparent record of *how* the spec was interpreted, not just the final diff.

**Usage:** `/implement_plan <path-to-spec-or-plan-file>`

> Heavily inspired by [Thariq's idea](https://x.com/trq212/status/2056418157305454805?s=20).

### `cmux-browser`

Help the agent rapidly navigate the [cmux](https://cmux.com/) in-app browser via CLI commands. See [documentation](https://cmux.com/docs/browser-automation) for further details.

### `coarse-review`

Review academic papers (PDF, DOCX, LaTeX, Markdown, HTML, EPUB) with rigorous peer-review feedback — locally, no API keys required.

See [coarse-review/README.md](coarse-review/README.md) for full instructions.

### `html_viewer`

Turn any local HTML file into a shareable live webpage via GitHub Gist + htmlpreview.github.io — no web server needed.

**Usage:** `/html_viewer <path-to-html-file>`

> Best for self-contained HTML (embedded CSS/JS). External assets referenced via relative paths won't load.

### `sciwrite_interactive`

Review a scientific manuscript for sentence-level writing quality (clutter, passive voice, buried predicates, terminology drift, numerical consistency) and accept/reject each suggestion in a browser editor — the experience is identical to Google Docs' "Suggesting" mode.

See [sciwrite_interactive/README.md](sciwrite_interactive/README.md) for the premises and full usage.

> Heavily inspired by [labarba/sciwrite](https://github.com/labarba/sciwrite), but delivers the review through an interactive accept/reject editor instead of a static report.

## Installation

Run the interactive installer — it lists every skill, lets you pick which ones and which agents to install for, and copies them into place:

```bash
npx github:arthur-albuquerque/skills
```

You'll choose:
- **Skills** — multiselect from the list above (space toggles, enter confirms)
- **Agents** — Claude Code, Codex, and/or OpenCode
- **Scope** — `user` (across all your projects) or `project` (current directory only)

Other commands:

```bash
npx github:arthur-albuquerque/skills list   # print available skills + descriptions
npx github:arthur-albuquerque/skills add --skill html_viewer --client claude-code
```

> Requires Node 18+. No npm account or global install needed — `npx` runs it straight from GitHub.

