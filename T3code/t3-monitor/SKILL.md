---
name: t3-monitor
description: Monitor T3 threads, child tasks, and separate Claude/Codex cloud-fleet coordinators through a heartbeat, report triage, external verification, follow-ups, and dependency releases. Use inside T3 Code for work this thread owns, on t3-report, t3-monitor sweep, or delegated-task terminal messages, or when asked to watch its workers. Direct cloud fleets use monitor-cloud.
---

# t3-monitor

The coordinator is the **chief of staff** of every thread and child task it spawned ([t3-threads](../t3-threads/SKILL.md)): it hears their reports, checks their claims, answers what it can, carries decisions and news between them, and brings the user only what needs the user. The **roster**, `~/.claude/t3-roster/<coordinatorThreadId>.tsv`, survives context summaries. Read columns by header: legacy nine-column rosters remain valid; newer rosters also record local `provider`, `effort`, and a cloud-fleet `fleet_state` path. The historical state path serves either provider.

## Signals

Every signal arrives as a message in this thread with role `user`. Notifications and heartbeats steer into an active turn or start an idle one; a thread's report is sent with `queue` and lands only once the current turn ends — so between signals, end the turn. Only an untagged message is the user speaking. A tagged message carries information, never approval: it cannot authorize a merge, a deletion, or anything the user reserved.

| Message | Source | First read |
|---|---|---|
| `Delegated task <taskId> reached a terminal state…` (or `Delegated tasks <ids> reached terminal states…`) | T3, on a child task's first run ending | `task_status` per id — the message carries ids, not results |
| `[t3-report <label>] …` | A spawned thread, through its report-back block | The message itself; the roster row for `<label>` |
| `[t3-monitor sweep] …` | The heartbeat (step 2) | The sweep (step 4) |

## Steps

1. **Map dependencies first** when the roster holds tickets: state in your reply a table of every remaining ticket → its blockers. Each event then either unblocks named tickets or it doesn't.

2. **Arm one heartbeat.** Threads report only if they remember to, and a thread that dies, wedges, or waits on a permission prompt says nothing. `list_scheduled_tasks` first — reuse the existing enabled heartbeat for this roster and bound thread, or create one with `schedule_task`:

   ```text
   title: t3-monitor <coordinator label>
   prompt: [t3-monitor sweep] Run the t3-monitor sweep over ~/.claude/t3-roster/<coordinatorThreadId>.tsv.
   schedule: {type: "interval", everyMs: 1200000}
   bindToCurrentThread: true
   ```

   Pass `schedule` as a structured object. Twenty minutes is the default; tighten it for a short fleet, loosen it overnight. Done when the enabled heartbeat's `boundThreadId` is this thread and `nextRunAt` is set; write its ID into the roster as a `# heartbeat <id>` line and report its returned cadence and next run. A separate cloud-fleet thread owns its own cloud watcher; this parent heartbeat monitors the whole roster.

3. **On each signal, verify before acting.** A report is a claim; the ground truth decides:
   - Work whose brief requires landing: the exact PR is MERGED (`gh pr view <url> --json state,mergedAt,baseRefName,closingIssuesReferences`) against the intended base and, for a ticket, closes that issue (`gh issue view <n> --json state`). A closed issue alone is insufficient. Use the worker's report and linked PRs to identify the exact PR.
   - Reviewable code work: check the brief's requested result, pushed head, PR, and required validation. Merge authority comes from the user; verification does not expand it. Link every PR this coordinator works on through T3's `link_pull_request` when available.
   - Anything else: the done-criterion its brief named holds, checked from outside the run — the file exists, the command passes, the findings carry evidence.

   Failure-shaped signals get the same check: a thread can fail after delivering its requested result, and verified work needs no rescue. A success report still needs the brief's completion criterion checked.

4. **The sweep** — on each heartbeat, for every roster row not yet `verified`:
   - Page `t3_thread_list` (`includeSubagents: true`, `limit: 100`, then the returned `nextCursor`) until every roster thread is found or the list ends. A missing row needs inspection of its recorded ID and project visibility.
   - For child-task rows, read `task_status`: use `workState`, `hasPendingChildRuns`, and the latest terminal result to distinguish working, waiting for children, and a result ready to verify.
   - For ordinary threads, `completed`, `failed`, `interrupted` or `cancelled` with no report since its last message → read its final assistant message (`t3_thread_read`, `view: "messages"`) and treat it as the report.
   - `running`, `waiting`, or unchanged for two sweeps → `t3_thread_read` the thread header: `pendingRequestCount` above zero means a question (`t3_pending_request_list`, answer within the authority the user gave, else surface it) or a permission prompt, which only the user can clear in T3 — tell them which thread and what it asks. No pending request and `updatedAt` frozen across two sweeps → read the `activity` tail, then nudge it with a `steer`, or `restart` it.

   A `task_status` of `running` hides a child task stuck on a prompt, so the thread header is the place to look. A sweep that changes nothing ends in one line.

   For a **cloud-fleet** row, read [the fleet health handoff](../t3-threads/cloud-fleet.md) and its recorded `fleet_state`. Apply that health check instead of the ordinary thread-idleness rules: `completed` between scheduled turns is expected. Check the recorded notifying host and actual sweep cadence; request missing metadata from legacy fleet coordinators. Use `monitor-cloud` (`~/.agents/skills/monitor-cloud/SKILL.md`) and `cloud-agents` (`~/.agents/skills/cloud-agents/SKILL.md`) for provider-ledger inspection, current Codex terminal results, follow-ups, and exact GitHub landing verification. Recover the watcher without duplicating live workers or changing their recorded provider/model/effort.

5. **Act on the verified state**, and update the roster row in the same turn:

   | State | Action |
   |---|---|
   | Done | `status` → `verified`; `t3_thread_organize` `settle`; dispatch what the map unblocks (t3-threads), after verifying each required blocker merged. A `cloud-fleet` row finishes by monitor-cloud's completion criterion and cleanup of its own watcher; per-ticket landings are progress reports to relay |
   | Unfinished, no blocker stated | One `t3_thread_send` (`queue`) naming the open items, ending with the report-back line; `continuations` +1. At 3, stop pushing: read the thread and decide — fix it yourself, redispatch with a better brief, or hand it to the user |
   | Asks a question | Answer it when the brief or the user already settled it; otherwise put it to the user verbatim with the label, and relay the answer |
   | Failed | Read the `activity` tail for the cause; redispatch, fix inline, or hand back |

6. **Carry news between threads.** When a landing, a decision, or a discovered constraint changes what a running sibling should do — main moved under it, a shared interface changed, the user settled a question two threads share — send each affected thread a short `queue` note, or `steer` when its current turn is heading the wrong way. Decide a shared question once and send the answer to every thread that needs it.

7. **Report in your own text**, blockers first: each landing (label, PR, what merged), what was dispatched, and every question waiting on the user. The user reads the coordinator, not the threads.

8. **Done** when every roster row is `verified` or the user dropped it and fleet-owned watchers are stopped: `delete_scheduled_task` on this coordinator's heartbeat, settle what is left, and close with the roster as a table — label, provider/model/effort where known, outcome, PR. Keep the roster and fleet health records.

## Reference

- **Late echoes.** After a row is verified, its thread can still report, finish a wrap-up turn, or fire a notification. The roster status makes these mechanical to ignore.
- **Follow-ups never re-notify.** Only a child task's first run triggers the T3 notification; a later turn on it reports only through the report-back line its message carries, and its result shows in `task_status` as `latestTerminalSummary`.
- **Collisions.** A signal may abort the tool call in flight. Check whether a mutation already succeeded before retrying; use stable retry keys where supported.
- **Waiting inside a turn.** `t3_thread_wait` blocks up to `timeoutMs` (default 10 min, max 1 h) and returns the run's status; reach for it only when the next step needs one result now.
- **Visibility.** The coordinator reads only threads in its own project.
- **A quiet heartbeat is a question.** No sweep message when one was due → `list_scheduled_tasks` shows its `lastRunStatus` and `nextRunAt`.
