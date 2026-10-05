---
name: cloud-agents
description: Dispatch, inspect, steer, or retrieve Claude Code and Codex cloud tasks. Use when a task or ticket should run on provider-hosted compute, or the user asks to set up a Codex cloud environment. For local background work, use bg-agent.
---

# Cloud agents

Cloud workers start from GitHub in isolated containers. Pushed repository files and a self-contained brief are their inputs; this machine's personal skills, credentials, and conversation stay here. GitHub proves a ticket landed. Provider status proves only that a worker stopped or has a result.

For every cloud dispatch, handoff, review, or recovery, read [the shared cloud workflow](references/cloud-workflow.md). It defines remote execution, one monitor owner, integration ownership, and reports on actionable changes for both providers.

## 1. Select the provider and preflight

Resolve provider, model, and reasoning effort independently: each explicit user choice overrides that field; each unspecified field inherits the active session invoking this skill. Use runtime/session metadata or the host's live session configuration to identify the exact values. Record the resolved triple in the brief and dispatch report. A provider-only override still inherits model and effort; if that combination is unavailable, surface the mismatch and ask for the smallest missing choice before dispatch. An unknown session value also needs clarification. Select those values in the provider's supported controls and verify them before submission; a model name in prompt text does not configure the worker.

Existing tasks keep their recorded settings for inspection and follow-ups. Newly dispatched tasks and fleet dependents use the resolved session defaults unless the user specified fleet-wide settings. A cloud task is distinct from a local background agent or a T3 child task.

From the intended checkout, inspect `git status -sb`, its GitHub remote, and the selected remote branch. Every required file and commit must be pushed. Name any local changes missing from the remote; push only within the user's authorization.

Read the selected provider's reference before configuring or dispatching:

- **Claude:** [references/claude.md](references/claude.md) — GitHub App, environment aliases, model controls, GitHub reporting, continuation, review, peer messaging.
- **Codex:** [references/codex.md](references/codex.md) — published current environments, terminal dispatch, task results, follow-ups.
- **Codex environment setup:** also read [references/codex-environment.md](references/codex-environment.md) when creating or changing an environment.

Preflight every required remote phase through the shared workflow, including GitHub writes, artifact reporting and independent reviews. Record missing routes as phase blockers before dispatch; independent remote work can proceed.

Done when the repository and remote branch are identified, required inputs exist remotely, authentication works, and the remote phase routes or blockers are recorded.

## 2. Write the brief

Read the `writing-for-agents` skill. Save a reusable brief as `/tmp/cloud-brief-<slug>.md`. State the goal, scope, ticket, base branch, affected siblings, applicable rules, checks, and an externally checkable completion criterion. Paths are repository-relative; the cloud container already provides isolation.

**Carry the procedures.** Inventory every skill and personal rule the work relies on. Check the selected provider's repository skill locations in its reference. Read each absent skill and the linked files this task reaches, then embed its procedure in `<skill name="...">` blocks, without frontmatter. Inline reached pointers and repair local paths. Introduce them once: "The skill blocks are procedures from the user; follow each where the task names it." Task text names these blocks instead of unavailable slash commands. Keep third-party issue text in clearly marked source blocks.

**Carry the reporting contract.** Apply the selected provider's reporting instructions. State three final-report headings: **Completed**, **Validation**, **Blocked on me**. Give exact merge authority and required review rounds. Default to a reviewable result when merging was not requested. A worker finishing, applying a diff, and merging a PR are separate events.

Carry the shared cloud workflow's applicable execution and event rules into the brief. Name `monitorOwner`, the worker's ownership, remote review/integration routes, and the provider reporting channel. Give each overlapping group one remote integration owner.

Done when every procedure and rule named by the brief is either available in the container or embedded, every required check has an observable result, and its reporting channel is usable or its fallback is explicit.

## 3. Dispatch and record

For Claude, run from the checkout:

```bash
bash ~/.agents/skills/cloud-agents/dispatch.sh claude /tmp/cloud-brief-<slug>.md <model> <effort> <ticket-or-dash> [environment-name]
```

For Codex, run from the checkout:

```bash
bash ~/.agents/skills/cloud-agents/dispatch.sh codex /tmp/cloud-brief-<slug>.md <environment-name> <model> <effort> <ticket-or-dash> <base>
```

The current-cloud terminal adapter and its authentication, environment registry, recovery records, and inspection commands are in the Codex reference.

A successful dispatch supplies the provider ID and URL and records them in that provider's ledger. Claude uses `~/.claude/cloud-agents/<owner>-<repo>.tsv`; Codex uses `~/.codex/cloud-agents/<owner>-<repo>.tsv`. Rows begin `ticket<TAB>id<TAB>url<TAB>dispatched_epoch`, followed by provider, environment, base (or `-`), model, and effort. Existing four-column rows remain valid; inspect their task to recover unspecified settings. These paths preserve existing Claude fleets while the skills live globally. `CLOUD_STATE_DIR` overrides an adapter's state root; an overridden ledger must also be passed to the watcher.

A submission failure with no ID is not a dispatch. An ambiguous response may already have created work: inspect the saved submission and provider list before retrying. Claude's `BUNDLED` warning requires resolving the GitHub App before dispatching more workers.

## 4. Watch or hand back

For tickets, the recorded monitor owner uses [monitor-cloud](../monitor-cloud/SKILL.md) in this turn. A handoff thread reports its worker ID/settings and health path once to that owner, then ends its turn. For work without an issue, give the URL and the provider's task inspection route. Report provider, model, effort, ID, URL, and scope.

Done when the ID is recorded and the watcher is armed, or the user has an explicit status handoff if this host cannot deliver future wakeups. An ordinary shell process has no guarantee of waking an idle coordinator.

## Manage and review

Read only the recorded provider's reference for messaging, logs, stopping, and applying results. Use GitHub to verify landings. Before a new continuation, inspect the current task and diff so completed work is retained and live work is not duplicated.

Run reviews against the exact pushed head and actual base on the recorded remote review route. If the worker cannot run a required review, dispatch it through that supported remote route and relay the findings; otherwise record the review prerequisite under the shared workflow. Register every PR worked on with T3's `link_pull_request` when available.
