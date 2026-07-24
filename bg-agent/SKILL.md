---
name: bg-agent
description: Dispatch and manage Claude Code background agents (claude --bg / agent view). Use when the user wants a task run as a background agent or session, asks to list, check on, stop, or attach to background agents, or mentions agent view.
---

# Background agents (`claude --bg`)

Dispatch via Bash from the directory the agent should work in — the session inherits the cwd. The command returns immediately and prints a short session id.

Model & effort policy: **always dispatch with `--model opus`** — never another model. Pick `--effort` yourself from the task's difficulty (low, medium, high, xhigh, max): low/medium for mechanical or well-specified work, high for typical implementation or debugging, xhigh/max for hard multi-file reasoning. Include both flags on every dispatch.

```bash
claude --bg --model opus --effort <level> "<prompt>"                        # dispatch
claude --bg --model opus --effort <level> --name "<label>" "<prompt>"       # readable name in agent view
claude --bg --model opus --effort <level> --agent <subagent> "<prompt>"     # a specific subagent as main agent
claude --bg --model opus --effort <level> --permission-mode <mode> "<prompt>"
claude --bg --exec '<shell command>'          # plain shell command as a job (no model involved)
```

Prompt rules:
- The background session sees none of this conversation — write a self-contained prompt: goal, file paths, verification command, done-criterion.
- Multi-line prompts: `claude --bg "$(cat <<'EOF' … EOF)"`.

Background sessions auto-isolate into a `.claude/worktrees/` worktree before editing files (skipped when the directory isn't a git repo).

## Monitor / manage

```bash
claude agents --json          # list sessions; --all includes completed
claude logs <id>              # recent output
claude stop <id>              # stop (alias: claude kill)
claude respawn <id>           # restart with conversation intact
claude rm <id>                # remove from list (transcript kept)
```

`state` in the JSON: `working`, `blocked` (check `waitingFor`), `done`, `failed`, `stopped`.

`claude agents` and `claude attach <id>` are interactive TUIs — suggest them to the user, never run them.

Done when: the dispatch printed a session id and you've reported the id, the name, and that the user can watch it in `claude agents` or take over with `claude attach <id>`. Poll `claude logs` only if the user asks you to babysit the run.

Full reference (keybindings, peek panel, daemon, filters): https://code.claude.com/docs/en/agent-view
