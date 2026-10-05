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

### `monitor-tickets`

Run a fleet of ticket agents from one coordinator session. You write the dependency map, it dispatches the frontier, watches for landings, and dispatches each dependent the moment its blockers merge.

GitHub is the ground truth, which is the point: an agent's own status lags a real merge and keeps crying wolf after one, so every event is checked against `gh` before anything is dispatched. Works over `claude --bg` sessions (watched by a persistent Monitor) or in-session sub-agents (woken by task notifications).

See [monitor-tickets/SKILL.md](monitor-tickets/SKILL.md) for full instructions.

### `t3-threads`

Dispatch child tasks or explicitly requested separate conversations in T3 Code. Claude/Codex cloud conversations are thin handoff threads: computation stays remote, and one monitor owner checks the complete fleet. Inherit provider, model and effort unless the user overrides them; write self-contained briefs and keep a roster.

Includes the cloud-fleet reference and standalone copies of the Opus and Fable briefing guides.

**Usage:** `/t3-threads <work to dispatch>`

See [T3code/t3-threads/SKILL.md](T3code/t3-threads/SKILL.md) for full instructions.

### `t3-monitor`

Coordinate work launched with `t3-threads`: verify results, answer actionable questions, release dependents and clean up the owned heartbeat. Cloud work shares one monitor owner and watcher; duplicate reports, acknowledgements and unchanged waits do not wake ticket threads.

**Usage:** `/t3-monitor` after dispatching work with `t3-threads`.

See [T3code/t3-monitor/SKILL.md](T3code/t3-monitor/SKILL.md) for full instructions.

### `cloud-agents`

Dispatch, inspect and continue Claude Code or Codex cloud tasks. The shared workflow keeps implementation, tests, reviews, integration and recovery remote, while the local coordinator handles dispatch, status and decisions. Claude's Codex review route uses a separate Codex cloud task and relays its findings back to the original Claude session.

See [T3code/cloud-agents/SKILL.md](T3code/cloud-agents/SKILL.md) for provider preflight and the bundled dispatch adapters.

### `monitor-cloud`

Watch Claude/Codex ticket fleets through one monitor owner and notifying host. Record processed events, inspect changed results once, verify exact GitHub landings and release dependents. Missing remote capabilities remain named phase blockers.

See [T3code/monitor-cloud/SKILL.md](T3code/monitor-cloud/SKILL.md) for the watcher and completion criteria.

These four skills, their adapters, model guides and installation notes are grouped in [T3code/README.md](T3code/README.md). Use the T3 pair inside T3 Code; the cloud pair also works outside it.

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
npx github:arthur-albuquerque/skills add --skill t3-threads --skill t3-monitor --client claude-code --global -y
npx github:arthur-albuquerque/skills add --skill t3-threads --skill t3-monitor --skill cloud-agents --skill monitor-cloud --client codex --global -y
```

> Requires Node 18+. No npm account or global install needed — `npx` runs it straight from GitHub.
