# Cloud execution and fleet ownership

Read for every Claude or Codex cloud dispatch, handoff, review, and recovery. This is the shared execution and monitoring contract; provider references supply the transport. Carry the applicable contract into briefs whose recipients cannot read this file.

## 1. Keep computation remote

Cloud work runs implementation, dependency setup, builds, tests, browser proofs, independent reviews, integration, and recovery on provider-hosted compute or a configured remote runner. The local coordinator dispatches, checks status and GitHub metadata, reads bounded evidence, answers decisions, and records outcomes.

Record `execution: cloud` and the remote route for each required phase. A local T3 thread, child task, background agent, or worktree remains local even when its model uses a hosted API. Keep local handoff threads free of project environment setup, test/browser processes, and review subagents. An explicit user request to run a named phase locally overrides this contract for that phase; record the exception.

Preflight the worker's GitHub write route, test/browser dependencies, artifact reporting, and required independent or second-provider review route. A review on another provider needs its own supported cloud environment and resolved model/effort. When a required route is missing, name the blocked phase and continue independent remote work. Resolve the remote prerequisite or surface it to the user; preserve the gate and existing result. Missing cloud tools or model capacity do not authorize local execution or a substitute reviewer.

Remote reports name the exact head/base, commands and results, independent review results, artifact locations, and remaining gates. Keep complete logs and browser artifacts remote; retrieve the summary and evidence needed for the current decision. A merge gate still requires the requested checks against the delivered head, whether the evidence comes from the cloud worker or CI.

Done when each required phase has a usable remote route or a recorded blocker, and the brief carries the execution boundary.

## 2. Assign one monitor owner

Choose one `monitorOwner` for the complete fleet before dispatch: normally the current coordinator's thread ID. A separate fleet thread can own monitoring if responsibility is explicitly transferred to it. Record that owner, the full ticket map, provider ledgers, and the one notifying host/task ID in one fleet health record. In T3 use the owner's assigned `fleet_state` path; ticket health files point to it as `fleetRecord`. Otherwise use `WATCH_STATE/fleet.json`.

Per-ticket T3 threads, when the user requests them, dispatch or adopt their cloud worker, save its ID/settings and health metadata, report the handoff once, and end their turn. Prepare local handoff turns one at a time by default; remote worker concurrency is a separate budget. The monitor owner inspects the cloud workers directly. A completed local handoff turn is expected while remote work continues. Only the monitor owner arms, re-arms, and stops the fleet watcher; ticket threads use its returned host metadata.

Give overlapping production changes one remote integration owner, with explicit contribution handoffs and validation against the combined head. Release truly independent work in parallel. Waiting for integration, a dependency, CI, or a running cloud task is a recorded wait state, not a request for another agent turn.

When adopting a legacy fleet, inspect its existing tasks and schedules first. Keep the owner's watcher, verify its coverage, and retire redundant fleet-owned schedules only after coverage is established. Preserve unrelated schedules and live workers. An ownership transfer completes only when the successor has the map, state, provider settings and notifying host, and the previous owner has relinquished the watcher.

Done when the full map has one named monitor owner, one notifying host or explicit manual monitoring, and an integration owner for each overlapping group.

## 3. Report changes once

Use the existing provider channel: Claude's GitHub reports/session messages, Codex task responses/follow-ups, or T3 handoff reports. Route coordination through the monitor owner. Peer messaging is reserved for a specific assigned handoff; only a concrete question or requested action calls for a reply.

Persist `processedEvents` and provider/GitHub cursors in the fleet record. Identify an event by `(provider, taskId, turnId or source event ID, headSHA, eventType)`, using the available fields; a question uses its request/comment ID. Batch pending events by ticket and keep the newest state before acting. Preserve distinct unanswered questions and failed gates until answered or verified resolved; a newer status alone does not resolve them. Mark handled events after recording their outcome; a duplicate or superseded event ends without a send. Check an ambiguous mutation's acceptance before retrying, using a stable request ID where the host supports one. These state fields are coordination records, not provider API options.

Report completion, a newly failed required gate, a changed prerequisite, or a decision requiring the owner/user. Include the event ID, exact revision, evidence pointer and requested action. For ongoing work, persist progress for the next sweep. Informational reports and acknowledgements require no reply; avoid sending a confirmation merely to trigger another confirmation. Answer a concrete question once, and resume a worker only with new actionable work. The sender ends its turn after the report.

The monitor owner checks status first. Fetch new comments, current-turn results, changed diffs or targeted logs when state changes, a quiet reminder fires, or a prerequisite becomes ready. Cache terminal results and review evidence by task/turn/head; reuse them while their scope is unchanged. Retrieve full history only to investigate a specific gap. Late reports from completed work are recorded only if they reveal an unresolved defect or decision.

Done when the event batch has one recorded disposition per event, actionable handoffs are delivered once, and unchanged state produces no follow-up messages.

## 4. Use a notifying host

Apply [monitor-cloud](../../monitor-cloud/SKILL.md) from the monitor owner. A supported event-notifying host can wake it on changes. T3's recurring scheduler starts an agent turn on every interval: one fleet schedule, twenty minutes by default, is the available fallback. A quiet scheduled sweep records health, ends in one line, and sends nothing to ticket threads. A background shell by itself cannot reliably wake an idle T3 coordinator.

Inspect provider results and exact GitHub landings before resolving tickets; task completion is not a merge. At fleet completion, stop the owned notifying host and retain state and evidence.

Done when host ownership, cadence and next run are recorded or the manual limitation is explicit, and completion cleanup removes only the fleet's watcher.
