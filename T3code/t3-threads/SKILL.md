---
name: t3-threads
description: Spawn and manage T3 Code threads from a coordinator thread — launch threads in their own worktrees, delegate child tasks, or launch a cloud fleet thread that runs tickets as claude --cloud sessions — on any connected provider and model (Claude, GPT/Codex, OpenCode). Use inside T3 Code when the user wants work run as T3 threads, subagents, or in the cloud, names a model to run it on, or asks to message, steer, interrupt, or check on a thread this one spawned.
---

# t3-threads

This thread is the **coordinator**: everything it spawns reports back to it, and it answers for all of them like a chief of staff. This skill dispatches and manages them; the t3-monitor skill runs the loop that reacts as they report. Every tool here is on the `t3-code` MCP server (load them with ToolSearch, `+t3-code`).

The coordinator sees only threads in its own project (`t3_thread_read`, `t3_thread_list` and `t3_thread_send` are all project-scoped), so spawn everything into the coordinator's project.

## 1. Pick the vehicle

| | **Thread** — `t3_thread_launch` | **Child task** — `delegate_task` |
|---|---|---|
| Lives | Top-level in the sidebar; the user can open, read and steer it | Under the coordinator, owned by it |
| Workspace | Its own: `workspaceStrategy` picks a new worktree, an existing one, or the project root | The coordinator's own checkout, shared with it |
| Completion | No parent link, no notice — it reports through the **report-back** block (step 4) | Its first run's end wakes the coordinator on its own: `Delegated task <taskId> reached a terminal state…` |
| Fits | Implementation, anything that commits or opens a PR, anything running alongside another writer | Research, review, scouting, one-off answers, read-only work |

Two writers in one checkout collide, so parallel code changes always go to threads, each in its own worktree. `create_threads` (a batch sharing the coordinator's checkout) fits only read-only batches the user asked to see as separate threads.

**Cloud fleet** — tickets the user wants worked in the cloud go to one local Claude thread that runs them as `claude --cloud` sessions through the cloud-agents and monitor-cloud skills. Its model rules, workspace and brief are in [cloud-fleet.md](cloud-fleet.md); read it before launching one, then carry on from step 5.

## 2. Pick the model

1. Read the coordinator's own selection: `t3_thread_configuration` with no `threadId`. It returns this thread's `threadId` (the coordinator id the briefs carry) and `modelSelection` — `instanceId`, `model`, `options`.
2. **The user named no model** → reuse that `modelSelection` verbatim, options included.
3. **The user named one** → resolve it against the live catalog. `orchestrator_capabilities` returns ~60 KB, so the harness saves it to a file; query it with jq:

   ```bash
   jq -r '.providers[] | select(.canRunChildTask) | .providerInstanceId as $p | .models[] | "\($p)\t\(.id)\t\([.options[]? | "\(.id)=\([.options[]?.id] | join("|"))"] | join(" "))"' <saved-file> | grep -i '<name>'
   ```

   - Provider by name: Claude family (opus, sonnet, haiku, fable) → `claudeAgent`; GPT / Codex names (sol, luna, astra, terra) → `codex`; OpenCode, or a model only OpenCode carries (gemini, deepseek, kimi, glm, qwen, minimax, …) → `opencode`, whose ids are `vendor/model` exactly as listed. A GPT name goes to `codex` unless the user said OpenCode.
   - A loose name ("gpt", "opus") → the newest matching model. `claudeAgent` and `codex` list their newest flagship first, so take the first match there; `opencode` lists alphabetically, so take the highest version of the named family. Name the resolved id in the dispatch report.
   - A provider with `canRunChildTask: false` is disabled or not installed; its `constraints` say why. Tell the user and stop that dispatch.
4. **Options** are per model — use only the ids and values the catalog lists for the resolved model. Effort is the level the user named; else, on an inherited selection, the coordinator's; else judged from the task, `medium` as the starting point. The option is `effort` on Claude, `reasoningEffort` on Codex (default `low`, so a Codex dispatch always sets it), and `variant` on OpenCode. A blank value list (`fastMode=`) marks a boolean. Fable caps at `high` by the user's cost policy. Keep `contextWindow` when the resolved model lists it.

Pass the selection explicitly on every dispatch: `modelSelection: {instanceId, model, options}` for a thread, `target: {providerInstanceId, model, options}` for a child task, `options` as an array of `{id, value}`. Inheritance is uneven — `delegate_task` drops the inherited options whenever the provider or model changes, and `t3_thread_launch` checks nothing against the catalog — so the resolution above is the only guard on what the child runs.

## 3. Write the brief

The child sees none of this conversation and nobody is watching it: write a self-contained **brief** — complete spec, absolute paths, a done-criterion checkable from outside the run, the goal and constraints with the route left to the agent.

Before writing it, load two things, every dispatch:

1. **Invoke `mattpocock-skills:writing-for-agents`** and write the brief by its levers.
2. **Read one guidance file**: [opus-guidance.md](opus-guidance.md) for Claude models, [fable-guidance.md](fable-guidance.md) for Fable. A GPT or OpenCode child gets the paste-in blocks from opus-guidance's "Bound the scope", "Unattended runs" (both blocks) and "The final report" sections, plus "Pasted text" when the brief carries text from elsewhere.

A non-Claude child reads none of `~/.claude` — no CLAUDE.md, no skills, no guides. Its brief carries every rule it needs in its own words, including any review-round policy.

**A thread in a git project starts in its prepared worktree.** The brief names that checkout as the place to work and carries one line: "If `.venv` is absent in your worktree, run `wt sync` from it." Outside git, a launch without `workspaceStrategy` runs in the project root — except in the Scratch project, where every thread gets a fresh folder of its own; either way the brief names every file by absolute path.

## 4. The report-back block (threads only)

A thread has no channel back except the one its brief gives it. Paste this at the end of every thread brief, filled:

```text
You were dispatched by a coordinator: T3 thread `<coordinatorThreadId>`; your label is `<label>`. Report to it with the t3-code MCP tool `t3_thread_send` — threadId `<coordinatorThreadId>`, mode `queue`, message starting `[t3-report <label>]` — at two moments: when you finish (outcome first; branch, PR URL, anything left undone), and when you reach a decision only the coordinator or the user can make (the question, your recommendation, and what you carry on with meanwhile). After a finish report, end your turn; replies arrive in this thread.
```

`queue` waits for the coordinator's current turn to end; `auto` or `steer` would cut into it and abort whatever tool call is in flight.

Child tasks skip this block: their final message is the report and the notification carries it. Only a child task's first run notifies, though, so every follow-up message to either kind ends with the one-line form (§6).

## 5. Dispatch

- **Label** every dispatch `<prefix>-<slug>` (`ticket-407-cc-gates`); it is the `title`, the report tag, and the roster key.
- **Thread:** `t3_thread_launch` with `title`, `message` (the brief), `modelSelection`, and in a git project `workspaceStrategy: {type: "worktree", baseRef: "<parent branch>", branch: "<new branch>", startFromOrigin: <bool>}` — `false` to build on local commits, `true` to fetch and start from origin. Uncommitted edits stay behind. Runtime and interaction modes inherit; leave them. `t3_thread_launch` has no retry key: after an error or a lost response, look for the title in `t3_thread_list` before launching again.
- **Child task:** `delegate_task` with `task` (the brief), `title`, `target`, `mode: "async"`, `role`, and a `clientRequestId` of the label, which makes a retry idempotent.
- Send independent dispatches in one message. T3 threads and child tasks sit outside CLAUDE.md's sub-agent cap; dispatch as many as the work needs.

**Record every dispatch in the roster** before anything else: `~/.claude/t3-roster/<coordinatorThreadId>.tsv`, one row per dispatch, tab-separated, header on first write:

```text
label	kind	id	model	workspace	ticket	blockers	status	continuations
```

`kind` is `thread`, `task`, or `cloud-fleet`; `id` is the `threadId`, or for a task the `taskId` and its `childThreadId` as `taskId|childThreadId`; `status` starts `running`. Ids carry `%` escapes, so write rows with the Write/Edit tools or a quoted heredoc rather than `printf`. The roster outlives this context window — t3-monitor reads and updates it.

Done when every dispatch returned an id, each has a roster row, and t3-monitor's loop is armed. Report each label, its id, and the resolved model; then end the turn — the reports and notifications are the wake-up.

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
