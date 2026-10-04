---
name: t3-threads
description: Dispatch and manage T3 child tasks or explicitly requested separate threads, including a separate coordinator for Claude/Codex cloud fleets. Use inside T3 Code for delegation, separate conversations, or messaging, steering, stopping, and inspecting work this thread owns. For direct provider-hosted work, use cloud-agents and monitor-cloud.
---

# t3-threads

This thread is the **coordinator**: everything it spawns reports back to it, and it answers for all of them like a chief of staff. This skill dispatches and manages them; [t3-monitor](../t3-monitor/SKILL.md) runs the loop that reacts as they report. Discover the `t3-code` tools through the host's tool catalog.

The coordinator sees only threads in its own project (`t3_thread_read`, `t3_thread_list` and `t3_thread_send` are all project-scoped), so spawn everything into the coordinator's project.

## 1. Pick the vehicle

| | **Thread** — `t3_thread_launch` | **Child task** — `delegate_task` |
|---|---|---|
| Lives | Top-level in the sidebar; the user can open, read and steer it | Under the coordinator, owned by it |
| Workspace | Its own: `workspaceStrategy` picks a new worktree, an existing one, or the project root | The coordinator's own checkout, shared with it |
| Completion | No parent link, no notice — it reports through the **report-back** block (step 4) | Its first run's end wakes the coordinator on its own: `Delegated task <taskId> reached a terminal state…` |
| Fits | Separate conversations the user explicitly requested; select a workspace before launch | Delegated work, including implementation with explicit file ownership |

Use child tasks for subagents and parallel delegation. Give shared-checkout writers non-overlapping ownership and tell them to preserve others' changes; serialize overlapping edits. Use `t3_thread_launch` or `create_threads` only when the user explicitly asks for separate/new/top-level threads or conversations. `create_threads` shares the caller's checkout; `t3_thread_launch` selects its workspace explicitly.

**Cloud work** — use `cloud-agents` (`~/.agents/skills/cloud-agents/SKILL.md`) and `monitor-cloud` (`~/.agents/skills/monitor-cloud/SKILL.md`) from the current coordinator. When the user explicitly requests a separate fleet coordinator thread, read [cloud-fleet.md](cloud-fleet.md) for its selection, brief, and health handoff, then continue from step 5. Cloud workers run on the selected provider; a local T3 thread is their coordinator.

## 2. Pick the model

1. Read the coordinator's own selection: `t3_thread_configuration` with no `threadId`. It returns this thread's `threadId` (the coordinator id the briefs carry) and `modelSelection` — `instanceId`, `model`, `options`.
2. Resolve provider, model, and effort independently: explicit user choices override each field; unspecified fields inherit this thread's selection. With no overrides, reuse `modelSelection` verbatim, including options. For cloud workers, apply cloud-agents' resolution and supported-provider checks instead of the local T3 catalog.
3. Resolve overrides against `orchestrator_capabilities`, including configured custom provider instances and models. Use the actual returned catalog, whether inline or saved to a file. Match exact IDs; clarify an ambiguous alias. For child tasks, check `canRunChildTask` and the provider's constraints. That child-task flag does not decide whether a top-level thread can launch.
4. Use only option IDs and values supported by the resolved model. Translate inherited effort to its supported option without changing the level; retain other inherited options where supported. If a value is unknown or the resolved combination is unsupported, ask for the smallest missing choice before dispatch. Report the resolved provider, model, and effort.

Pass the selection explicitly on every dispatch: `modelSelection: {instanceId, model, options}` for a thread, `target: {providerInstanceId, model, options}` for a child task, `options` as an array of `{id, value}`. Inheritance is uneven — `delegate_task` drops the inherited options whenever the provider or model changes, and `t3_thread_launch` checks nothing against the catalog — so the resolution above is the only guard on what the child runs.

## 3. Write the brief

The child sees none of this conversation and nobody is watching it: write a self-contained **brief** — complete spec, absolute paths, a done-criterion checkable from outside the run, the goal and constraints with the route left to the agent.

Before writing it, load two things, every dispatch:

1. Read `writing-for-agents` (`~/.agents/skills/writing-for-agents/SKILL.md`) and write the brief by its levers.
2. For Claude models, read [opus-guidance.md](opus-guidance.md), or [fable-guidance.md](fable-guidance.md) for Fable, and carry the applicable scope and reporting instructions. The resolved session/user settings govern model and effort. For other providers, state scope, ownership, checks, and the final reporting contract directly in the brief.

Check which rules and skills the worker can actually read. Global shared skills live in `~/.agents/skills`; embed reached procedures when the worker lacks access. For remote containers, cloud-agents owns this packaging. Each brief carries applicable review policy and the user's merge authority.

**A thread in a git project starts in its prepared worktree.** The brief names that checkout as the place to work and carries one line: "If `.venv` is absent in your worktree, run `wt sync` from it." Outside git, a launch without `workspaceStrategy` runs in the project root — except in the Scratch project, where every thread gets a fresh folder of its own; either way the brief names every file by absolute path.

## 4. The report-back block (threads only)

A thread has no channel back except the one its brief gives it. Paste this at the end of every thread brief, filled:

```text
You were dispatched by a coordinator: T3 thread `<coordinatorThreadId>`; your label is `<label>`. Report to it with the t3-code MCP tool `t3_thread_send` — threadId `<coordinatorThreadId>`, mode `queue`, message starting `[t3-report <label>]` — at two moments: when you finish (outcome first; branch, PR URL, anything left undone), and when you reach a decision only the coordinator or the user can make (the question, your recommendation, and what you carry on with meanwhile). After a finish report, end your turn; replies arrive in this thread.
```

`queue` waits for the coordinator's current turn to end; `auto` or `steer` would cut into it and abort whatever tool call is in flight.

Child tasks skip this block: the notification carries task IDs; read their results with `task_status`. Only a child task's first run notifies, so every follow-up message to either kind ends with the one-line form (§6).

## 5. Dispatch

- **Label** every dispatch `<prefix>-<slug>` (`ticket-407-cc-gates`); it is the `title`, the report tag, and the roster key.
- **Thread:** `t3_thread_launch` with `title`, `message` (the brief), `modelSelection`, and in a git project `workspaceStrategy: {type: "worktree", baseRef: "<parent branch>", branch: "<new branch>", startFromOrigin: <bool>}` — `false` to build on local commits, `true` to fetch and start from origin. Uncommitted edits stay behind. Runtime and interaction modes inherit; leave them. `t3_thread_launch` has no retry key: after an error or a lost response, look for the title in `t3_thread_list` before launching again.
- **Child task:** `delegate_task` with `task` (the brief), `title`, `target`, `mode: "async"`, `role`, and a `clientRequestId` of the label, which makes a retry idempotent.
- Batch independent dispatches within the user's scope and any applicable concurrency limits.

**Record every dispatch in the roster** before anything else: `~/.claude/t3-roster/<coordinatorThreadId>.tsv`, one row per dispatch, tab-separated, header on first write:

```text
label	kind	id	model	workspace	ticket	blockers	status	continuations	provider	effort	fleet_state
```

`kind` is `thread`, `task`, or `cloud-fleet`; `id` is the `threadId`, or for a task the `taskId` and its `childThreadId` as `taskId|childThreadId`; `status` starts `running`. Ids carry `%` escapes, so write rows with the Write/Edit tools or a quoted heredoc rather than `printf`. The roster outlives this context window — t3-monitor reads and updates it.

The new header appends `provider`, `effort`, and `fleet_state` after the existing nine columns. The first two record the local worker selection; `fleet_state` is the cloud-fleet health record path described in cloud-fleet.md, or `-`. Existing nine-column rosters and heartbeat comments remain valid: preserve their layout, recover missing selections through T3 configuration, and ask an existing fleet coordinator to supply its health record before evaluating watcher health. The historical `~/.claude/t3-roster` state path stays compatible across providers.

Done when every dispatch returned an id, each has a roster row, and t3-monitor's loop is armed. Report each label, its id, and resolved provider/model/effort; then end the turn — the reports and notifications are the wake-up.

## 6. Manage

| To | Call |
|---|---|
| Message a thread or child | `t3_thread_send` `mode: "queue"` — a separate turn after its current one. `steer` corrects an active turn mid-flight; `restart` abandons it. A `clientRequestId` makes the send idempotent. End the message with: `When done, report with t3_thread_send to thread <coordinatorThreadId>, mode queue, message starting [t3-report <label>].` |
| See where it stands | `t3_thread_list` (`includeSubagents: true`, filter by `statuses` or `titleContains`) for status across the roster; `task_status` for a child task (`workState`: `working`, `waiting_for_children`, `result_available`) |
| Read what it said | `t3_thread_read`, `view: "messages"` for the conversation, `"activity"` for the tool trail; page with `afterPosition`, cap with `limit` and `maxCharsPerItem` |
| Answer its question | `t3_pending_request_list` then `t3_pending_request_respond`. Permission approvals are outside these tools: the user clicks them in T3 |
| Stop it | `t3_thread_interrupt` for a thread's turn; `task_cancel` for a child task |
| Wait on one result inside this turn | `t3_thread_wait` with a `timeoutMs` — only when the very next step needs that result |
| Retire it | `t3_thread_organize` `settle` (or `archive`) once t3-monitor has verified its work |
