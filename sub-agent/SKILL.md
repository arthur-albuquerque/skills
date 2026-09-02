---
name: sub-agent
description: Dispatch and manage in-session sub-agents via the Agent tool, including overnight ticket fleets run from a coordinator session. Use when the user wants work fanned out to sub-agents, tickets run through the Agent tool rather than claude --bg, or asks to check on, message, or continue a running sub-agent.
---

# Sub-agents (Agent tool)

A sub-agent runs *inside this session*: it lives only while the session lives, it never appears in `claude agents`/agent view, and its completion arrives on its own as a task notification — push, not poll. That is the trade against `claude --bg` (the bg-agent skill): bg sessions outlive the coordinator and are watchable from the terminal; sub-agents are cheaper to dispatch, auto-notify, and can be continued mid-run with SendMessage. For an overnight run the session stays open, so sub-agents are fine — the machine sleeping, not the session ending, is the real risk to flag to the user.

## Dispatch

- **Model policy: `model: "opus"`** unless the user explicitly named Fable for this dispatch — then pass `model: "fable"` and read [fable-guidance.md](fable-guidance.md) before writing the brief. Effort goes in the brief's framing, not a parameter (the Agent tool has none): state the level the user named, or judge it from the task (`high` default). Fable caps at `high` by the user's cost policy — never frame a Fable brief at xhigh or max.
- **`name` every agent** — `ticket-<n>-<slug>` for ticket work — so SendMessage can reach it and notifications are readable.
- Leave `run_in_background` at its default (background). Dispatch independent agents in **one message** so they run concurrently.
- **`isolation: "worktree"`** whenever two or more agents will edit files in the same repo. A lone agent editing serially doesn't need it.
- `subagent_type: "general-purpose"` unless a more specific type fits.

## The prompt is a brief

Same contract as a background session: self-contained spec, absolute paths, done-criterion checkable from outside, goal + constraints with the route left to the agent, scope bound explicitly, delegation capped for small tasks, final message shaped to lead with the outcome.

Before writing the prompt, load two things. Every dispatch, no exceptions:

1. **Invoke the `mattpocock-skills:writing-for-agents` skill** (via the Skill tool) and write the brief by its levers: completion criteria that are checkable and demanding, positive phrasing over prohibitions, leading words, single source of truth, no no-op sentences. The brief is a document an agent consumes, and that skill governs how it's written.
2. Read the guidance file for the model you're dispatching. [opus-guidance.md](opus-guidance.md) for Opus (the default), [fable-guidance.md](fable-guidance.md) when the user named Fable. Each stands alone, so read one: the blocks to paste in (scope, delegation cap, length), what to leave out, and how to pick effort. Both files are the single source of truth for those blocks and are kept identical to the copies in the bg-agent skill.

**In a git repo, prefer `isolation: "worktree"` over asking the agent to make its own.** When you do hand worktree creation to the agent instead, the brief names the paths, the way a background brief does:

```text
Work in a fresh git worktree, never the primary checkout:
`git -C <repo> worktree add <repo>/.claude/worktrees/<slug> -b <branch>`, and run everything from
that directory. Commit only the files your own task changed. Once the branch is merged, remove the
worktree.
```

## Ticket fleets

For running a fleet of tickets (dependency map, dispatch, verifying landings against GitHub, dispatching dependents), follow the monitor-tickets skill (`~/.claude/skills/monitor-tickets/`) — it covers both sub-agent and `claude --bg` fleets. Sub-agent completions push task notifications, so no Monitor is needed for this mechanism.

## Scope boundary

For a mechanical 3+-task decomposition with schema-shaped outputs and no judgment between stages, the delegate-workflow skill (Workflow tool) is the right tier instead. Ticket fleets stay on the Agent tool: between landings the coordinator verifies, re-reads the map, and decides — judgment a workflow script can't hold.
