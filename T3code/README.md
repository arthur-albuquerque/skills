# T3 Code setup

This folder contains two skills for coordinating work inside T3 Code across connected providers, their model guides, and installation instructions.

## Contents

| File | Purpose |
| --- | --- |
| [t3-threads/SKILL.md](t3-threads/SKILL.md) | Dispatch child tasks or explicitly requested separate conversations; record their roster. |
| [t3-monitor/SKILL.md](t3-monitor/SKILL.md) | Monitor the roster, handle reports, verify requested results, and release dependents. |
| [t3-threads/opus-guidance.md](t3-threads/opus-guidance.md) | Claude briefing guidance. |
| [t3-threads/fable-guidance.md](t3-threads/fable-guidance.md) | Fable briefing guidance. |
| [t3-threads/cloud-fleet.md](t3-threads/cloud-fleet.md) | Handoff to an explicitly requested separate Claude/Codex cloud-fleet coordinator. |

## Install

For a shared global installation, copy the two skill folders from this directory:

```bash
mkdir -p ~/.agents/skills
cp -R t3-threads t3-monitor ~/.agents/skills/
```

Configure each client to discover these shared folders. If it uses its own skill directory, link the two folders there or use the repository installer for that client. The bundled model guides are regular files, so either skill folder can be copied without dependencies on another installation's symlinks.

The installer supports Claude Code, Codex, and OpenCode. For example:

```bash
npx github:arthur-albuquerque/skills add --skill t3-threads --skill t3-monitor --client codex --global -y
```

To install from a local clone, run from the repository root:

```bash
npm install
node cli.mjs add --skill t3-threads --skill t3-monitor --client codex --global -y
```

The installer uses each client's skill directory; it does not create a shared global installation. Reload the agent if the skills do not appear. Both skills require T3's tools at runtime.

## Dependencies

| Dependency | When it is needed |
| --- | --- |
| T3 Code with the `t3-code` orchestration tools | Thread, child-task, messaging, and scheduling operations. |
| A connected, authenticated model provider | Running local dispatched work. Resolve IDs and options through T3's live catalog, including custom instances. |
| Both `t3-threads` and `t3-monitor` | Dispatch and monitoring work together. |
| `writing-for-agents` at `~/.agents/skills/writing-for-agents/SKILL.md` | Writing briefs. This external skill is not bundled here. |
| Git | Separate worktrees for explicitly requested implementation conversations. |
| [`wt`](https://github.com/lorenzolfm/wt) | Restoring configured ignored-file links in worktrees with `wt sync`. |
| Authenticated GitHub CLI (`gh`) | Checking exact PR merges, bases, closing references, and issue state. |
| Node 18+ and npm | Using the installer; manual copying does not require Node. |

For cloud work, install the external `cloud-agents` and `monitor-cloud` skills under `~/.agents/skills` and complete the selected provider's preflight. They are not bundled here. They supply Claude dispatch and the current Codex cloud terminal adapter, authentication/environment checks, provider ledgers, continuations, and worker-result inspection. Follow their selected-provider references for prerequisites and adapter installation. Cloud workers need pushed repository inputs and self-contained briefs; this computer's personal skills do not automatically travel to the container.

## Worktree environments

Git worktrees omit ignored files such as `.venv` and `.env`. We use [lorenzolfm/wt](https://github.com/lorenzolfm/wt) to keep configured files in a shared store and link them into worktrees. Follow its [installation instructions](https://github.com/lorenzolfm/wt#installation), then initialize the target repository and share only the existing paths it needs:

```bash
wt init
wt share .venv
```

`wt sync` restores missing links; it does not create a virtual environment or install dependencies. Adapt briefs for projects using another setup.

## Selection and monitoring

Provider, model, and effort inherit from the requesting session unless the user explicitly overrides each field. A separate fleet coordinator receives the resolved cloud-worker settings in its brief, so changing its local model preserves worker settings. Unsupported combinations need clarification before dispatch. Session/user selections take precedence over defaults in the bundled model guides.

Direct cloud work runs through the shared cloud skills in the current coordinator. Create a separate top-level coordinator only when the user explicitly requests a separate conversation; delegated subagents remain child tasks.

The coordinator keeps its roster at `~/.claude/t3-roster/<coordinatorThreadId>.tsv` for compatibility across providers. Existing nine-column rosters remain valid. New rosters append provider, effort, and fleet-health record path. Cloud-fleet health uses its actual notifying host, schedule cadence, and last completed sweep; an idle local thread can coexist with active remote workers. Parent heartbeats and fleet-owned cloud watchers have separate IDs and are cleaned up by their owners.

## Use

Open a coordinator inside T3 Code and invoke:

```text
/t3-threads <work to delegate, or explicitly requested separate conversations>
```

Then use `/t3-monitor` to coordinate the dispatched work. For cloud tickets directly, use `/cloud-agents` and `/monitor-cloud`. For a separate cloud coordinator, read [cloud-fleet.md](t3-threads/cloud-fleet.md).
