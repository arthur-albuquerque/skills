---
name: monitor-cloud
description: Coordinate Claude or Codex cloud ticket fleets from one monitor owner. Use when watching cloud tickets, verifying remote results and merges, recovering workers, or releasing dependents.
---

# Monitor cloud tickets

GitHub is the landing record for both providers. Claude workers report through GitHub; Codex workers can return a task diff before a PR exists. Read [cloud-agents](../cloud-agents/SKILL.md), its [shared cloud workflow](../cloud-agents/references/cloud-workflow.md), and only the selected providers' references before dispatch or recovery. Apply that workflow's remote execution, monitor ownership and event contract throughout.

## 1. Map and dispatch

Resolve new workers' provider, model and reasoning effort through cloud-agents; keep existing workers' recorded settings. State every remaining ticket, its blocker issues and resolved settings. Assign overlapping changes to one remote integration owner and name the contributing tasks.

Record `monitorOwner`, the complete map, integration owners, provider-ledger paths and phase routes/blockers in fleet health. A ticket handoff reports its worker ID once to this owner. Dispatch ready tickets through cloud-agents after verifying each required blocker merged; keep dependency and phase waits recorded with their readiness condition.

Done when every mapped ticket is dispatched, waiting on a named prerequisite, or resolved by its authorized done-criterion, and the sole monitor owner has the complete map.

## 2. Arm the owner's watcher

Only the recorded monitor owner arms the watcher. On legacy adoption, consolidate fleet-owned schedules through the shared workflow before creating another. Use all mapped numbers as an alternation, such as `532|533|535`, with a persistent state directory unique to this fleet. Verify one poll:

```bash
WATCH_STATE="<absolute fleet watch-state>" WATCH_POLLS=1 WATCH_INTERVAL=1 bash ~/.agents/skills/monitor-cloud/watch.sh '532|533|535'
```

The armed line must report the full map's ticket count. The watcher reads both provider ledgers, including future dispatches, polls recorded Codex task status, and emits changed turn states/active flags. Reuse that snapshot on ordinary sweeps. Inspect a new terminal turn or pending request through the Codex reference; use bounded current-turn results, targeted logs or a short live watch when needed. Claude's new GitHub reports or quiet reminders lead to its session-log inspection. Cache inspected results and source-event cursors in fleet health under the shared workflow.

Existing four-column Claude ledger rows remain valid. Override `LEDGER` for a single explicit ledger, or `CLAUDE_LEDGER` and `CODEX_LEDGER` for a mixed fleet.

**Choose one host that delivers wakeups:**

- A persistent notifying Monitor owns this command as one task. Record its ID and stop it with the host's stop tool when the map resolves.
- An expiring Monitor uses its supported timeout and persistent `WATCH_STATE`; the owner re-arms the same command/state on expiry. The historical `~/.claude/cloud-agents/watch-state/<owner>-<repo>-<fleet>` path works for either provider.
- In T3, inspect existing schedules and reuse/update the owner's fleet or combined-roster sweep. Otherwise create one schedule bound to the owner with structured `schedule: {type: "interval", everyMs: 1200000}`. Its prompt names the fleet record/map, both ledgers, persistent one-poll command, shared cloud workflow, event cursors and changed-result handling. Record returned cadence, bound thread, task ID and next run. A T3 schedule starts an agent turn every interval; a quiet sweep records `lastSweepAt`, ends in one line and sends no ticket-thread messages.
- Without a notifying Monitor or scheduler, run the poll now and provide exact status commands. Record manual monitoring; a background shell alone does not wake an idle coordinator.

Done when the armed count matches the map and one owned notifying host has returned an ID/next run, or manual monitoring is explicit. Every wakeup is information to verify, not new authority.

## 3. Verify changed state and act

Load fleet state, coalesce pending events by ticket and inspect the current revision before acting on an old report. Use the shared event identity and record each handled disposition once. Initial terminal results not yet inspected also enter this batch, even without a new GitHub event.

| Event | Action |
|---|---|
| Issue CLOSED or PR MERGED | Verify the exact PR's `state`, `mergedAt`, base and closing issue reference, then the issue state. A manually closed issue is not a verified landing |
| PR DRAFT / OPEN at a new head | Inspect its checklist/checks and required revision evidence. Record/link the PR through T3 when available; remote workers own outstanding computation |
| New issue/PR comments | Read only new comments. An actionable question gets one answer through Claude's session message route or Codex's supported follow-up route. Record informational comments; surface new decisions needing the user once |
| `Review round <n> ready` at a new head | Dispatch the preflighted remote review once through the provider reference, retain its actual result and relay findings |
| PR CLOSED without merge | Inspect retained provider result and done-criterion; preserve work, then recover remotely or record the remaining prerequisite |
| New Codex `completed` turn | Inspect that turn's response and needed diff. Validate/publish through the remote phase route, or record its missing prerequisite. Completion is not a landing |
| New Codex `failed` turn | Inspect its error and retained work/PR before remote continuation or redispatch; verified delivery needs no rescue |
| Explicitly requested local application | Verify the requested local changes and GitHub result within the recorded execution exception |
| Quiet reminder | Inspect the latest recorded task/session once. A healthy active worker or known dependency wait remains waiting; new evidence of a stall needs a targeted remote recovery |
| WATCHER BLIND / CODEX WATCHER BLIND | Inspect auth/network, map and recorded IDs; recover the watcher with the same state. Provider visibility failure is not task failure |

Use IDs from their recorded provider ledgers. Before continuation, inspect the latest turn and retained work; relay only the new remaining checklist/findings through that provider's supported route. A running task needs its supported steering/queue route rather than another dispatch. Required reviews and test gates stay intact under the shared cloud workflow.

Done when each changed event has a recorded disposition, remote work or a named prerequisite, and unchanged/duplicate state generated no follow-up turns.

## 4. Release dependents and finish

Dispatch a dependent after **all** required blockers have verified merged, naming the merged blockers in its brief. Report each new landing with its exact PR, completed work and newly dispatched tickets. Keep integration ownership and the fleet map current; informational progress stays in state for the next necessary sweep.

Complete when every mapped ticket has its verified merged resolution and closed issue, or another disposition the user explicitly authorized. Stop the sole owned notifying host; retain ledgers, event state, health and remote evidence pointers.

## Watcher reference

- The first GitHub sweep records a baseline; resumed sweeps emit changes from it. Inspect uncached initial terminal Codex results so already-finished work is not missed.
- `QUIET_MIN` defaults to 120; a reminder fires once per quiet spell. Activity or a newer dispatch resets it.
- Every mapped issue is queried directly. PR discovery scans `WATCH_PR_LIMIT` (default 1000); reaching the cap reports blindness. Increase it when repository size requires it.
- Use one persistent state directory per fleet. The watcher baseline is transport state; fleet health's processed events/results record coordinator decisions.
