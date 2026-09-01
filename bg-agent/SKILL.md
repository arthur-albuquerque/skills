---
name: bg-agent
description: Dispatch and manage Claude Code background agents (claude --bg / agent view). Use when the user wants a task run as a background agent or session, asks to list, check on, stop, or attach to background agents, or mentions agent view.
---

# Background agents (`claude --bg`)

Dispatch via Bash from the directory the agent should work in — the session inherits the cwd. The command returns immediately and prints a short session id.

Model & effort policy: **dispatch with `--model opus`** unless the user explicitly named Fable for this run — then use `--model fable`. For `--effort`, use the level the user named; if they didn't, judge it from the task's difficulty (low, medium, high, xhigh, max; `high` is the default). Fable caps at `high` by the user's cost policy — dispatch Fable on `low`, `medium`, or `high` only, even if the user asked higher. Include both flags on every dispatch.

```bash
claude --bg --model opus --effort <level> "<prompt>"                        # dispatch
claude --bg --model opus --effort <level> --name "<label>" "<prompt>"       # readable name in agent view
claude --bg --model opus --effort <level> --agent <subagent> "<prompt>"     # a specific subagent as main agent
claude --bg --model opus --effort <level> --permission-mode <mode> "<prompt>"
claude --bg --exec '<shell command>'          # plain shell command as a job (no model involved)
```

## The prompt is a brief

The background session sees none of this conversation and nobody is watching it — write a self-contained **brief**: the complete spec with absolute paths, and a done-criterion checkable from outside the run. State the goal and the constraints and leave the route to the agent.

Before writing the prompt, load two things — every dispatch, no exceptions:

1. **Invoke the `mattpocock-skills:writing-for-agents` skill** (via the Skill tool) and write the brief by its levers: completion criteria that are checkable and demanding, positive phrasing over prohibitions, leading words, single source of truth, no no-op sentences. The brief is a document an agent consumes; that skill governs how it's written.
2. Read the guidance file for the model you're dispatching — [opus-guidance.md](opus-guidance.md) for Opus (the default), [fable-guidance.md](fable-guidance.md) when the user named Fable. Each stands alone: the blocks to paste in (scope, delegation cap, length), what to leave out, and how to pick effort.

Multi-line prompts: `claude --bg "$(cat <<'EOF' … EOF)"`.

**In a git repo, the brief names the worktree.** Auto-isolation into `.claude/worktrees/` is documented but does not always fire, and a session that branches in the primary checkout sweeps another session's dirty files onto its branch. Paste in, with the paths filled:

```text
Work in a fresh git worktree, never the primary checkout:
`git -C <repo> worktree add <repo>/.claude/worktrees/<slug> -b <branch>`, and run everything from
that directory. Commit only the files your own task changed. Once the branch is merged, remove the
worktree.
```

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
