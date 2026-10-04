# T3 Code setup

This folder contains the two Claude skills for coordinating work inside T3 Code, their model guides, and the setup instructions for sharing them with another user.

## Contents

| File | Purpose |
| --- | --- |
| [t3-threads/SKILL.md](t3-threads/SKILL.md) | Launch and manage threads or delegated child tasks; record their roster. |
| [t3-monitor/SKILL.md](t3-monitor/SKILL.md) | Monitor the roster, handle reports, verify landings, and dispatch dependents. |
| [t3-threads/opus-guidance.md](t3-threads/opus-guidance.md) | Briefing guidance for Opus and the shared blocks used for other providers. |
| [t3-threads/fable-guidance.md](t3-threads/fable-guidance.md) | Briefing guidance for Fable. |
| [t3-threads/cloud-fleet.md](t3-threads/cloud-fleet.md) | Instructions for the optional cloud-fleet workflow. |

## Install for Claude Code

Copy this whole `T3code` folder to the other computer. From inside it, run:

```bash
mkdir -p ~/.claude/skills
cp -R t3-threads t3-monitor ~/.claude/skills/
```

This installs both skills globally for that user. Each skill folder must sit directly under `~/.claude/skills`; the `T3code` container is for distribution. The model guides are regular files, so copying the folders preserves them without symlinks to another installation.

Alternatively, once these changes are published to the repository, use its installer:

```bash
npx github:arthur-albuquerque/skills add --skill t3-threads --skill t3-monitor --client claude-code --global -y
```

To install from a local clone before publication, run these commands from the repository root:

```bash
npm install
node cli.mjs add --skill t3-threads --skill t3-monitor --client claude-code --global -y
```

Reload the agent if the skills do not appear.

## Dependencies

| Dependency | When it is needed |
| --- | --- |
| T3 Code with the `t3-code` MCP tools | All thread, delegation, messaging, and scheduling operations. Plain Claude Code outside T3 cannot supply these tools. |
| A connected, authenticated model provider | Running the dispatched work. The selected provider and model must be available in T3's live catalog. |
| Both `t3-threads` and `t3-monitor` | The dispatch and monitoring workflows work together. |
| `mattpocock-skills:writing-for-agents` | The briefing step in `t3-threads` expects this external skill; it is not bundled here. |
| Git | Creating separate worktrees for code-writing threads. |
| [`wt`](https://github.com/lorenzolfm/wt) | Sharing ignored files across worktrees and restoring their links with `wt sync`; install it separately for this workflow. |
| `jq` | The JSON commands shown for model discovery and cloud workspace trust. |
| Authenticated GitHub CLI (`gh`) | Verifying GitHub PR merges and ticket closures. |
| Node 18+ and npm | Using the repository installer; manual copying does not need Node. |

For cloud fleets, additionally install the external `cloud-agents` and `monitor-cloud` skills and configure Claude Code cloud access. Those skills are not bundled here. Read [cloud-fleet.md](t3-threads/cloud-fleet.md) before using that workflow.

## Why we use `wt`

Git worktrees provide separate code checkouts, but omit ignored files such as `.venv` and `.env`. We use [lorenzolfm/wt](https://github.com/lorenzolfm/wt) to keep configured files in a shared store and link them into each worktree. This lets workers reuse the prepared environment instead of installing it again for every checkout.

Follow `wt`'s [installation instructions](https://github.com/lorenzolfm/wt#installation), then initialize the target repository and share its existing ignored environment:

```bash
wt init
wt share .venv
```

Share only paths the project needs. `wt sync` restores missing links; it does not create a virtual environment or install dependencies. Projects using another setup should adapt the worker brief accordingly.

## Setup assumptions to review

The skills preserve the original workflow. Before using them on another computer, review these assumptions:

- The Fable guide includes a `high` effort ceiling and limits on parallel Fable workers. Adapt those cost preferences to the recipient's policy.
- The cloud-fleet reference names a default Claude model. Resolve it against the recipient's T3 catalog before launching a fleet.

The coordinator writes its runtime roster to `~/.claude/t3-roster/<coordinatorThreadId>.tsv` on the recipient's computer. The roster tracks active work; it is not part of the distributed setup.

## Use

Open a Claude coordinator thread inside T3 Code and invoke:

```text
/t3-threads <work to dispatch>
```

Then use `/t3-monitor` to coordinate the dispatched work. It uses a scheduled heartbeat and removes that heartbeat when the fleet finishes. For the complete behavior, read the two `SKILL.md` files linked above.
