---
name: t3-threads
description: Dispatch and manage T3 child tasks or explicitly requested separate threads, including Claude/Codex cloud handoffs. Use inside T3 Code for delegation, separate conversations, or managing work this thread owns. For provider-hosted work, use cloud-agents and monitor-cloud with one fleet monitor owner.
---

# t3-threads

This thread is the **coordinator**: it dispatches work, resolves decisions and records verified outcomes. [t3-monitor](../t3-monitor/SKILL.md) handles reports and scheduled checks. Discover the `t3-code` tools through the host's tool catalog.

The coordinator sees only threads in its own project (`t3_thread_read`, `t3_thread_list` and `t3_thread_send` are all project-scoped), so spawn everything into the coordinator's project.

## GitHub ticket names

Before dispatching GitHub ticket work, rename the current coordinator thread to `Coordinator #<tickets>`, using the ticket set it oversees from the assignment or roster. Sort the numbers and compress consecutive runs into ranges: `Coordinator #407–410, #415`; a single ticket is `Coordinator #407`. List gaps separately so the title names only tickets under its oversight. Update the title when that scope changes. Call `t3_thread_update` with `action: "rename"` and `title`, omitting `threadId` to target the current coordinator. Include repository names when needed to distinguish ticket numbers across repositories.

When creating a thread or child task to tackle GitHub issues, include the assigned ticket numbers in its label and `title` at dispatch: `ticket-407-cc-gates`, or `tickets-407-408-cc-gates` for a fleet. Include `owner/repo` when needed to distinguish repositories, and carry the repository and issue numbers in the brief.

If the created thread's title needs correction, call `t3_thread_update` with `action: "rename"`, its returned `threadId` (or `childThreadId` for a child task), and the ticket-bearing `title`. Confirm each rename's returned title matches the requested name; report a failed rename. Work without a GitHub ticket keeps its ordinary naming convention.

## 1. Pick the vehicle

| | **Thread** — `t3_thread_launch` | **Child task** — `delegate_task` |
|---|---|---|
| Lives | Top-level in the sidebar; the user can open, read and steer it | Under the coordinator, owned by it |
| Workspace | Its own: `workspaceStrategy` picks a new worktree, an existing one, or the project root | The coordinator's own checkout, shared with it |
| Completion | No parent link, no notice — it reports through the **report-back** block (step 4) | Its first run's end wakes the coordinator on its own: `Delegated task <taskId> reached a terminal state…` |
| Fits | Separate conversations the user explicitly requested; select a workspace before launch | Delegated work, including implementation with explicit file ownership |

Use child tasks for subagents and parallel delegation. Give shared-checkout writers non-overlapping ownership and tell them to preserve others' changes; serialize overlapping edits. Use `t3_thread_launch` or `create_threads` only when the user explicitly asks for separate/new/top-level threads or conversations. `create_threads` shares the caller's checkout; `t3_thread_launch` selects its workspace explicitly.

**Cloud work** — use [cloud-agents](../cloud-agents/SKILL.md), including its [shared cloud workflow](../cloud-agents/references/cloud-workflow.md), and [monitor-cloud](../monitor-cloud/SKILL.md) from the recorded monitor owner. When the user explicitly requests separate fleet or per-ticket conversations, read [cloud-fleet.md](cloud-fleet.md) for thin handoff threads, then continue from step 5. Those T3 threads remain local; provider-hosted tasks own computation.

## 2. Pick the model

1. Read the coordinator's own selection: `t3_thread_configuration` with no `threadId`. It returns this thread's `threadId` (the coordinator id the briefs carry) and `modelSelection` — `instanceId`, `model`, `options`.
2. Resolve provider, model, and effort independently: explicit user choices override each field; unspecified fields inherit this thread's selection. With no overrides, reuse `modelSelection` verbatim, including options. For cloud workers, apply cloud-agents' resolution and supported-provider checks instead of the local T3 catalog.
3. Resolve overrides against `orchestrator_capabilities`, including configured custom provider instances and models. Use the actual returned catalog, whether inline or saved to a file. Match exact IDs; clarify an ambiguous alias. For child tasks, check `canRunChildTask` and the provider's constraints. That child-task flag does not decide whether a top-level thread can launch.
4. Use only option IDs and values supported by the resolved model. Translate inherited effort to its supported option without changing the level; retain other inherited options where supported. If a value is unknown or the resolved combination is unsupported, ask for the smallest missing choice before dispatch. Report the resolved provider, model, and effort.

Pass the selection explicitly on every dispatch: `modelSelection: {instanceId, model, options}` for a thread, `target: {providerInstanceId, model, options}` for a child task, `options` as an array of `{id, value}`. Inheritance is uneven — `delegate_task` drops the inherited options whenever the provider or model changes, and `t3_thread_launch` checks nothing against the catalog — so the resolution above is the only guard on what the child runs.

## 3. Write the brief

The child sees none of this conversation and nobody is watching it: write a self-contained **brief** — complete spec, absolute paths, a done-criterion checkable from outside the run, the goal and constraints with the route left to the agent.

Before writing it, load two things, every dispatch:

1. Read writing-for-agents (`~/.agents/skills/writing-for-agents/SKILL.md`) and write the brief by its levers.
2. For Claude models, read [opus-guidance.md](opus-guidance.md), or [fable-guidance.md](fable-guidance.md) for Fable, and carry the applicable scope and reporting instructions. The resolved session/user settings govern model and effort. For other providers, state scope, ownership, checks, and the final reporting contract directly in the brief.

Check which rules and skills the worker can actually read. Global shared skills live in `~/.agents/skills`; embed reached procedures when the worker lacks access. For remote containers, cloud-agents owns this packaging. Each brief carries applicable review policy and the user's merge authority.

**A local implementation thread starts in its prepared worktree.** Its brief names that checkout as the place to work and carries: "If `.venv` is absent in your worktree, run `wt sync` from it." Cloud handoff threads instead carry cloud-fleet.md's execution boundary and use their checkout for orchestration only. Outside git, a launch without `workspaceStrategy` runs in the project root — except in the Scratch project, where every thread gets a fresh folder; name local inputs by absolute path.

## 4. The report-back block (threads only)

A thread has no channel back except the one its brief gives it. Paste this at the end of every thread brief, filled:

```text
You were dispatched by coordinator T3 thread `<coordinatorThreadId>`; your label is `<label>`. Report once per completed assignment, changed prerequisite or decision needing the coordinator/user, with `t3_thread_send`, threadId `<coordinatorThreadId>`, mode `queue`, message starting `[t3-report <label>]`. Include a stable event ID, outcome, exact revision/PR/evidence and remaining work; for a question, give your recommendation and independent work continuing meanwhile. Informational reports need no reply. Route sibling coordination through the coordinator unless it assigns a specific peer handoff. After reporting, end your turn; process a later message only for its new action or concrete question.
```

`queue` waits for the coordinator's current turn to end; `auto` or `steer` would cut into it and abort whatever tool call is in flight.

Child tasks skip this block: the notification carries task IDs; read their results with `task_status`. Only a child task's first run notifies; an actionable follow-up uses the reporting contract in §6.

## 5. Dispatch

- **Label** every dispatch `<prefix>-<slug>`, applying the GitHub ticket naming rule above; it is the `title`, the report tag, and the roster key.
- **Thread:** `t3_thread_launch` with `title`, `message` (the brief), `modelSelection`, and an explicit workspace. Local implementation in git uses `workspaceStrategy: {type: "worktree", baseRef: "<parent branch>", branch: "<new branch>", startFromOrigin: <bool>}` — `false` for local commits, `true` for origin. Cloud handoffs use cloud-fleet.md's workspace choice. Uncommitted edits stay behind. Runtime and interaction modes inherit; leave them. After an error or lost response, look for the title in `t3_thread_list` before launching again; this tool has no retry key.
- **Child task:** `delegate_task` with `task` (the brief), `title`, `target`, `mode: "async"`, `role`, and a `clientRequestId` of the label, which makes a retry idempotent.
- Batch independent dispatches within the user's scope and any applicable concurrency limits.

**Record every dispatch in the roster** before anything else: `~/.claude/t3-roster/<coordinatorThreadId>.tsv`, one row per dispatch, tab-separated, header on first write:

```text
label	kind	id	model	workspace	ticket	blockers	status	continuations	provider	effort	fleet_state
```

`kind` is `thread`, `task`, or `cloud-fleet`; `id` is the `threadId`, or for a task the `taskId` and its `childThreadId` as `taskId|childThreadId`; `status` starts `running`. Ids carry `%` escapes, so write rows with the Write/Edit tools or a quoted heredoc rather than `printf`. The roster outlives this context window — t3-monitor reads and updates it.

The new header appends `provider`, `effort`, and `fleet_state` after the existing nine columns. The first two record the local worker selection; `fleet_state` is the cloud-fleet health record path described in cloud-fleet.md, or `-`. Existing nine-column rosters and heartbeat comments remain valid: preserve their layout, recover missing selections through T3 configuration, and ask an existing fleet coordinator to supply its health record before evaluating watcher health. The historical `~/.claude/t3-roster` state path stays compatible across providers.

Done when every dispatch returned an id, each has a roster row, and the monitor owner has the map and notifying host or explicit manual handoff. Ordinary local work uses t3-monitor; cloud handoffs share the fleet owner's watcher. Report each label, id and resolved provider/model/effort; then end the turn.

## 6. Manage

| To | Call |
|---|---|
| Assign new work or answer a question | `t3_thread_send` `mode: "queue"` starts a separate turn. Name the action and a stable event ID; use `clientRequestId` for retry safety. For work requiring a result, append: `Report the result once to thread <coordinatorThreadId>, mode queue, starting [t3-report <label>], event <eventId>.` For an informational update, record it in shared state and let the recipient's next necessary turn read it. `steer` corrects an active turn; `restart` abandons it. |
| See where it stands | `t3_thread_list` (`includeSubagents: true`, filter by `statuses` or `titleContains`) for status across the roster; `task_status` for a child task (`workState`: `working`, `waiting_for_children`, `result_available`) |
| Read what it said | `t3_thread_read`, `view: "messages"` for the conversation, `"activity"` for the tool trail; page with `afterPosition`, cap with `limit` and `maxCharsPerItem` |
| Answer its question | `t3_pending_request_list` then `t3_pending_request_respond`. Permission approvals are outside these tools: the user clicks them in T3 |
| Stop it | `t3_thread_interrupt` for a thread's turn; `task_cancel` for a child task |
| Wait on one result inside this turn | `t3_thread_wait` with a `timeoutMs` — only when the very next step needs that result |
| Retire it | `t3_thread_organize` `settle` (or `archive`) once t3-monitor has verified its work |
