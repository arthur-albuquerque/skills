# Cloud fleet thread

A **cloud fleet thread** is a local T3 coordinator for provider-hosted workers. Read this file only when the user explicitly requests a separate coordinator conversation. Otherwise run `cloud-agents` (`~/.agents/skills/cloud-agents/SKILL.md`) and `monitor-cloud` (`~/.agents/skills/monitor-cloud/SKILL.md`) in the current thread. Those skills own provider preflight, dispatch, inspection, continuations, and verified landings; this file owns the T3 handoff.

## 1. Resolve launch inputs

- **Local coordinator:** inherit the requesting thread's T3 selection unless the user explicitly overrides the coordinator's settings. Resolve overrides through t3-threads §2. Claude and Codex coordinators can both use the shared cloud skills and T3 scheduler.
- **Cloud workers:** resolve provider, model, and effort through cloud-agents using the session requesting the fleet. Carry that resolved triple explicitly into the coordinator's brief as the fleet-wide settings. A different local coordinator selection then leaves worker settings intact. Inspect and continue existing workers with their recorded settings. An unsupported inherited combination needs the smallest missing user choice before dispatch.
- **Workspace:** use the repository's primary checkout and identify its GitHub remote and pushed base. The local coordinator performs orchestration and reviews; cloud workers make ticket changes. In the repo's T3 project, launch with `workspaceStrategy: {type: "root"}`. From another project, keep the coordinator thread in the parent's project for tool visibility and name the absolute repository checkout in its brief; run repository commands there.
- **Preflight:** read the selected provider's reference through cloud-agents. Check Claude folder trust only for Claude dispatches; check Codex authentication, published environment, and current-cloud terminal route for Codex dispatches. Complete unresolved prerequisites before starting workers.
- **State path:** reserve `~/.claude/t3-roster/<coordinatorThreadId>-<label>.json` for fleet health. After launch, record the returned thread ID as `kind: cloud-fleet`, with all mapped tickets and this `fleet_state` path. This historical state root works for either provider.

Done when the local selection and cloud-worker triple are explicit, the checkout/base and prerequisites are verified, and the health-record path is chosen.

## 2. Write the brief

Verify the local coordinator can read the global shared skills at `~/.agents/skills`. Name their absolute paths in its brief; if inaccessible, embed the reached procedures using writing-for-agents. The shared cloud skills package personal procedures separately for the remote workers.

Fill this template, then add t3-threads' report-back block:

```text
You are the cloud fleet coordinator for <owner/repo>. Run repository commands from <absolute checkout>; the pushed base is <base>. Read <absolute cloud-agents/SKILL.md> and <absolute monitor-cloud/SKILL.md>, then follow their selected-provider references. Run preflight, dependency mapping, briefs, dispatch, monitoring, verified landings, and dependents through those skills.

Tickets → blockers:
<table>

Cloud workers have explicit fleet-wide settings: provider <provider>, model <model>, effort <effort>, environment <name>. These worker settings are independent of your local T3 selection.
<merge authority, review policy, and ticket notes exactly as authorized>

Maintain the fleet health record at <absolute fleet_state path>. Record the repository, checkout, mapped tickets/blockers, resolved worker settings, environment and provider-ledger paths, watcher mode, returned host task/schedule ID, bound thread ID, cadence/next run where applicable, persistent WATCH_STATE directory, and lastSweepAt after each completed sweep. Record actual returned values; use null for fields unavailable in the chosen host. Provider ledgers remain the source of worker IDs and progress.

Choose a notifying host through monitor-cloud. In T3, prefer one recurring schedule bound to this fleet thread, using a structured interval and a prompt carrying the map, ledger paths, terminal inspection, and one-poll GitHub check. Inspect existing schedules before creating one. Save the returned ID, cadence, and next run; ending your turn lets scheduled wakeups run. If no notifying host is available, report the manual-monitoring limitation and exact status commands.

Report to the parent at each verified landing (ticket, exact PR, what merged, newly dispatched tickets), a decision needing the user (provider/task ID and question), an unresolved blocker, a watcher mode/ID change, and fleet completion (final ticket/PR table and watcher cleanup). Relay parent answers through the recorded worker provider's supported follow-up route. On monitoring failure, inspect the existing worker before continuation or redispatch.
```

Done when the brief carries the resolved settings, complete ticket map, authority, accessible procedures, report-back destination, and health-record contract. Continue with t3-threads §5 to launch using the workspace selected above, record the roster row, and arm the parent's monitor.

## 3. Read fleet health from the parent

The local thread can be `completed` between scheduled turns while cloud workers remain active. Use its health record and notifying host, rather than T3 status or a fixed re-arm timeout, to check liveness:

- **Scheduler:** inspect the recorded schedule ID for the fleet's `boundThreadId`, enabled state, `lastRunStatus`, and next run. Compare `lastSweepAt` with the actual cadence. A failed run or a missed sweep needs inspection; a running sweep may still be in progress.
- **Monitor:** inspect the recorded host task and its supported expiry/re-arm behavior through monitor-cloud. Preserve the same `WATCH_STATE` when re-arming.
- **Manual:** report monitoring as manual; an idle local thread is expected. Each parent sweep performs or requests an explicit cloud/GitHub check.

When a sweep is more than two recorded cadences late, or the host reports failure/expiry, read the coordinator's messages and activity, then queue a targeted recovery request. A missing health record needs a state report, not a second fleet. Independently verify exact PR landings through monitor-cloud; closed issues alone do not prove merges. Finish only when its completion criterion holds and the fleet-owned notifying task/schedule has been stopped. The parent's t3-monitor heartbeat is separate and stays active while other roster work remains.
