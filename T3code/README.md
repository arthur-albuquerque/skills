# T3 Code setup

This folder contains two T3 coordination skills and two Claude/Codex cloud skills, with their model guides and dispatch adapters.

## Contents

| File | Purpose |
| --- | --- |
| [t3-threads/SKILL.md](t3-threads/SKILL.md) | Dispatch child tasks or explicitly requested separate conversations; record their roster. |
| [t3-monitor/SKILL.md](t3-monitor/SKILL.md) | Monitor the roster, handle reports, verify requested results, and release dependents. |
| [t3-threads/opus-guidance.md](t3-threads/opus-guidance.md) | Claude briefing guidance. |
| [t3-threads/fable-guidance.md](t3-threads/fable-guidance.md) | Fable briefing guidance. |
| [t3-threads/cloud-fleet.md](t3-threads/cloud-fleet.md) | Thin handoff threads when separate fleet or per-ticket conversations are explicitly requested. |
| [cloud-agents/SKILL.md](cloud-agents/SKILL.md) | Dispatch, inspect and continue Claude or Codex cloud workers. |
| [cloud-agents/references/cloud-workflow.md](cloud-agents/references/cloud-workflow.md) | Shared remote execution, one monitor owner and actionable-event reporting contract. |
| [cloud-agents/codex-cloud.py](cloud-agents/codex-cloud.py) | Terminal adapter for current Codex Cloud. |
| [monitor-cloud/SKILL.md](monitor-cloud/SKILL.md) | Verify cloud results and ticket landings through one fleet watcher. |

## Install

For a shared global installation, run from the repository root:

```bash
mkdir -p ~/.agents/skills ~/.local/bin
cp -R T3code/t3-threads T3code/t3-monitor T3code/cloud-agents T3code/monitor-cloud ~/.agents/skills/
ln -sfn ~/.agents/skills/cloud-agents/codex-cloud.py ~/.local/bin/codex-cloud
```

Configure each client to discover these shared folders and put `~/.local/bin` on PATH. If a client uses its own skill directory, link the folders there or use the repository installer. Model guides are bundled as regular files.

The installer supports Claude Code, Codex, and OpenCode. For example:

```bash
npx github:arthur-albuquerque/skills add --skill t3-threads --skill t3-monitor --skill cloud-agents --skill monitor-cloud --client codex --global -y
```

To install from a local clone, run from the repository root:

```bash
npm install
node cli.mjs add --skill t3-threads --skill t3-monitor --skill cloud-agents --skill monitor-cloud --client codex --global -y
```

The installer uses each client's skill directory; it does not create the shared `~/.agents/skills` installation or the `codex-cloud` command alias. With a client-specific or project installation, substitute its actual skill directory in the cloud command examples and point the alias at its `cloud-agents/codex-cloud.py`. The watcher finds the sibling adapter automatically, or accepts `CODEX_CLOUD_CLI` for another location. Reload the agent if the skills do not appear. The two T3 skills require T3's tools; the cloud skills can be used without T3.

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

For cloud work, install both bundled cloud skills and complete the selected provider's preflight. Claude dispatch needs the authenticated Claude CLI, tmux and the Claude GitHub App installed for the repository. The current Codex adapter needs `uv`, a file-backed Codex ChatGPT login, and a registered published environment. Fleet polling needs `gh` and `jq`. Follow [Claude's reference](cloud-agents/references/claude.md) or [Codex's reference](cloud-agents/references/codex.md) for the relevant setup. Credentials, environment registries and provider ledgers remain on the user's machine; they are not bundled. Cloud workers receive pushed repository inputs and self-contained briefs.

## Worktree environments

Git worktrees omit ignored files such as `.venv` and `.env`. We use [lorenzolfm/wt](https://github.com/lorenzolfm/wt) to keep configured files in a shared store and link them into worktrees. Follow its [installation instructions](https://github.com/lorenzolfm/wt#installation), then initialize the target repository and share only the existing paths it needs:

```bash
wt init
wt share .venv
```

`wt sync` restores missing links; it does not create a virtual environment or install dependencies. Adapt briefs for projects using another setup.

## Selection and monitoring

Provider, model, and effort inherit from the requesting session unless the user explicitly overrides each field. A separate fleet coordinator receives the resolved cloud-worker settings in its brief, so changing its local model preserves worker settings. Unsupported combinations need clarification before dispatch. Session/user selections take precedence over defaults in the bundled model guides.

Direct cloud work runs through the shared cloud skills in the current coordinator. Create separate top-level conversations only when explicitly requested; delegated subagents remain child tasks. For per-ticket cloud conversations, each local thread dispatches or adopts its worker, reports once and ends its turn. Implementation, dependency setup, tests, browsers, review, integration and recovery run remotely. A missing remote route stays a named prerequisite until resolved.

The coordinator keeps its roster at `~/.claude/t3-roster/<coordinatorThreadId>.tsv` for compatibility across providers. Existing nine-column rosters remain valid. New rosters append provider, effort, and fleet-health record path. One named monitor owner checks the full cloud map through one notifying host; a parent checking a separate owner's health does not add another heartbeat for those tickets. Transfer the complete map, settings and host before relinquishing ownership. Health records name the actual cadence and last sweep; an idle local handoff can coexist with active remote work.

Persist event identities and inspect each changed result once. Keep unanswered questions and failed gates until resolved. Acknowledgements, duplicate reports and unchanged dependency waits generate no follow-up messages. T3's fallback is one twenty-minute schedule: it still starts an agent turn each interval, but quiet sweeps update health and end in one line. A background shell alone cannot wake an idle coordinator.

## Live check

The Claude Cloud → Codex Cloud review → Claude Cloud continuation was exercised in [viagem-trip-platform PR #238](https://github.com/arthur-albuquerque/viagem-trip-platform/pull/238) on 2026-10-05. Claude Sonnet 5.5/xhigh published a small regression test; Codex GPT-6.1-Sol/xhigh reviewed the exact pushed head remotely; both cloud environments passed the 72 targeted tests. One coordinator relay delivered the findings back to Claude, which [confirmed the review event and revision](https://github.com/arthur-albuquerque/viagem-trip-platform/pull/238#issuecomment-5986681358). This checked the handoff and remote testing, not larger-fleet performance or recurring-monitor behavior.

## Use

Open a coordinator inside T3 Code and invoke:

```text
/t3-threads <work to delegate, or explicitly requested separate conversations>
```

Then use `/t3-monitor` to coordinate the dispatched work. For cloud tickets directly, use `/cloud-agents` and `/monitor-cloud`. For a separate cloud coordinator, read [cloud-fleet.md](t3-threads/cloud-fleet.md).
