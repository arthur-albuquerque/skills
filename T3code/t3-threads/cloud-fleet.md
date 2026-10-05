# Cloud handoff threads

Read when the user explicitly requests a separate fleet or per-ticket T3 conversation for Claude or Codex cloud work. Otherwise dispatch from the current coordinator through [cloud-agents](../cloud-agents/SKILL.md). Apply [the shared cloud workflow](../cloud-agents/references/cloud-workflow.md) to either topology; this file supplies the T3 launch and health handoff.

## 1. Resolve the handoff

- **Monitor owner:** choose the one owner and fleet record through the shared workflow. A per-ticket thread is a dispatch/report shell. A separate fleet coordinator owns the watcher only on explicit transfer. For a not-yet-created owner thread, its brief identifies the owner as "this thread"; it obtains its actual ID with `t3_thread_configuration` and records it after launch. The parent then reads that same watcher rather than arming another for this fleet.
- **Local selection:** inherit the requesting thread's T3 selection unless the user overrides it. Resolve overrides through t3-threads §2. Either local provider can orchestrate either supported cloud provider.
- **Cloud selection:** resolve provider, model and effort through cloud-agents from the requesting session. Carry the explicit triple into the brief independently of the local selection. Keep existing tasks' recorded settings when adopting them.
- **Workspace:** name the absolute primary checkout, GitHub remote and pushed base. Launch with `workspaceStrategy: {type: "root"}` unless the user specified another workspace. It serves orchestration commands and metadata only; remote tasks own the implementation checkout. Keep the thread in the parent's T3 project for visibility, even when the named repository is elsewhere.
- **Preflight:** follow the selected provider reference and shared remote phase checks. Claude needs the GitHub App/reporting route; Codex needs authentication and a published current environment. Required remote review/integration routes belong in the handoff.
- **State:** reserve `~/.claude/t3-roster/<coordinatorThreadId>-<label>.json` for health metadata. Record the returned T3 ID as `kind: cloud-fleet` with tickets and this `fleet_state` path. Both providers use this historical state root.

Done when the local/cloud selections, existing task IDs if any, one monitor owner, checkout/base, phase routes or blockers, and health path are explicit.

## 2. Write and launch

Verify access to the shared skills at `~/.agents/skills`; name their absolute paths or embed reached procedures using writing-for-agents. Cloud-agents separately packages procedures for remote workers. Fill this template, then add t3-threads' report-back block:

```text
You are the cloud handoff thread for <owner/repo>, tickets <map>. Use <absolute checkout> for orchestration; the pushed base is <base>. Read <absolute cloud-agents/SKILL.md>, its shared cloud workflow, <absolute monitor-cloud/SKILL.md> and the selected provider reference.

Cloud settings: provider <provider>, model <model>, effort <effort>, environment <name>. Existing tasks to adopt: <IDs/settings or none>. These settings are independent of your local T3 selection.
Tickets → blockers: <table>
Remote integration ownership: <overlapping groups/owners>
Remote phase routes and unresolved prerequisites: <implementation, checks/browser, reviews, artifacts, GitHub writes>
<merge authority, required reviews and ticket notes exactly as authorized>

Execution is cloud under the shared workflow. This local thread dispatches/adopts work and records metadata. Run implementation, dependencies, tests, browser proofs, reviews and recovery through the recorded remote routes. A missing route is a phase blocker; retain existing work and continue independent remote work.

Monitor owner is T3 thread <monitorOwner>. Shared fleet record is <absolute fleetRecord>. Write your handoff health to <absolute fleet_state>, naming the owner and fleetRecord, repo/checkout, map, cloud settings, environment, provider ledgers, worker IDs, remote phase routes/blockers, status and actual host metadata supplied by the owner. Use null for metadata not yet returned. Write only your assigned metadata file; the owner maintains fleet-wide state and events.

After adopting/dispatching, report worker IDs/URLs/settings, health path and any unresolved prerequisite once to the monitor owner, then end your turn. This is the completion report for your handoff assignment. The owner polls the remote workers directly. Your completed handoff turn is expected while they run. A subsequent turn handles only new assigned work or a concrete decision; use the shared event contract.
```

If this thread is taking ownership of the whole fleet, fill the owner as "this thread" and its health path as the fleet record. Replace the final paragraph with an explicit transfer assignment: obtain its actual thread ID, establish/adopt the sole watcher and fleet record through monitor-cloud, report returned host metadata once to the parent, and end the turn. The parent relinquishes monitoring for those same tickets after the shared transfer criterion holds. Further parent reports cover only decisions needing it or fleet completion.

Continue with t3-threads §5, using the selected workspace. The monitor owner records all handoffs before arming one watcher over the complete map; handoff threads use that watcher rather than creating ticket schedules.

Done when the thread ID and roster row exist, workers are recorded/adopted without duplication, and the monitor owner has the health path, map and notifying host or manual limitation.

## 3. Read health and recover

Read `monitorOwner` and the recorded notifying host before evaluating liveness. A completed local handoff thread is not a failed or stalled cloud worker. The monitor owner performs provider/GitHub checks through monitor-cloud; the parent of a separate monitor owner checks its health file and actual host:

- **Scheduler:** verify its ID, bound owner thread, enabled state, `lastRunStatus` and next run. Compare `lastSweepAt` with the returned cadence.
- **Monitor:** check the host's supported expiry/re-arm behavior. The owner re-arms with the same `WATCH_STATE`.
- **Manual:** retain that limitation; an idle local thread is expected. Perform one explicit provider/GitHub check when requested.

A sweep more than two recorded cadences late, or host failure/expiry, needs one owner-targeted recovery action after inspecting messages/activity. Legacy records without `monitorOwner` need owner discovery and the shared workflow's schedule consolidation, preserving live workers and recorded provider/model/effort. Missing ticket metadata is recovered from ledgers or one targeted state request; it does not require another fleet.

Verify exact PR landings independently. Resolve the roster row when the cloud done-criterion holds, then settle the local handoff. Stop the sole owned watcher only when its complete map is resolved; retain health, event and provider records.
