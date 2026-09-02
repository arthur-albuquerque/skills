# skills

A collection of skills for AI agents.

## Skills

### `implement_plan`

Execute a plan or spec file by reading it and implementing its contents. Triggered when you provide a path to a plan, spec, or design document and want it implemented — even if you just drop a file path and say "do it."

It's great because the agent keeps a running HTML log of design decisions, deviations, tradeoffs, and open questions as it works — so you get a transparent record of *how* the spec was interpreted, not just the final diff.

**Usage:** `/implement_plan <path-to-spec-or-plan-file>`

> Heavily inspired by [Thariq's idea](https://x.com/trq212/status/2056418157305454805?s=20).

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

### `bg-agent`

Dispatch and manage Claude Code background agents (`claude --bg` / `agent view`). Run a task as a background session, then list, check on, stop, or attach to it — without blocking your current session.

Dispatches **Opus 5** by default, or **Fable 5.1** when you name it. The brief-writing guidance is per model: [bg-agent/opus-guidance.md](bg-agent/opus-guidance.md) follows Anthropic's [Prompting Claude Opus 5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5), and [bg-agent/fable-guidance.md](bg-agent/fable-guidance.md) follows [Prompting Claude Fable 5.1](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-1). Each covers that model's behaviour on scope, self-verification, subagent delegation, progress updates, and effort.

See [bg-agent/SKILL.md](bg-agent/SKILL.md) for full instructions.

### `sub-agent`

Dispatch and manage in-session sub-agents through the Agent tool, including overnight ticket fleets run from a coordinator session. Sub-agents live only as long as the session does, but they're cheap to dispatch, they report back on their own as task notifications, and you can message one mid-run.

Same brief-writing contract as `bg-agent`, and it ships the same per-model guidance: [sub-agent/opus-guidance.md](sub-agent/opus-guidance.md) and [sub-agent/fable-guidance.md](sub-agent/fable-guidance.md) are kept identical to the `bg-agent` copies, so either skill works installed on its own.

See [sub-agent/SKILL.md](sub-agent/SKILL.md) for full instructions.

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

