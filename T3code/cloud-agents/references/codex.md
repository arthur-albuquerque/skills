# Current Codex Cloud from the terminal

Use `~/.local/bin/codex-cloud`, backed by this skill's [codex-cloud.py](../codex-cloud.py). It connects to `wss://codex-cloud-backend.chatgpt.com/` using the existing file-backed `codex login` credentials and the cloud app-server protocol. The worker runs on OpenAI's compute and survives the command disconnecting. Requires `uv` and network access; its script declares the WebSocket dependency. Browser cookies and an API key are unnecessary.

For dispatch, review and recovery, apply [the shared cloud workflow](cloud-workflow.md); the commands here supply Codex's transport.

This is an experimental adapter to the current service, verified on 2026-10-04, rather than an upstream `codex cloud` subcommand. Stable 0.160.0 and alpha 0.162.0-alpha.13 still queried the legacy catalog and could not resolve the published `viagem-default`. Preserve the current route when those commands fail. Recheck upstream compatibility after upgrades.

## Preflight and dispatch

1. Identify the checkout, pushed inputs, provider/model/effort through the main skill. `codex-cloud models` returns this account's live model and effort choices. The adapter rejects unavailable selections before creating work. The backend's internal `modelProvider: local` identifier is distinct from the skill's Codex provider and its hosted execution.
2. Select a published current environment. Read [codex-environment.md](codex-environment.md) for setup. `codex-cloud environments list` lists the **local registry**, not every server environment. Register a known published config with `codex-cloud environments add <name> '<full-UUID~asenvcfg_ID>' --repo <owner/repo> --branch <published-ref>`. Registration records the existing config; it creates no environment. Dispatch verifies the returned environment ID, model, and effort before sending the brief.
3. Run from the checkout with the resolved values:

```bash
bash ~/.agents/skills/cloud-agents/dispatch.sh codex /tmp/cloud-brief-<slug>.md <environment-name> <model> <effort> <ticket-or-dash> <base>
```

The adapter uses the environment's published repository refs. The helper rejects a base or repository differing from its registry; update and publish the environment before changing that ref. It checks the base exists remotely. Required local edits still need the main skill's pushed-input check.

Done when the command reports an admitted turn, the server has returned the matching environment/model/effort, and the actual thread ID and URL are recorded. Credentials stay in memory. A private submission record under `~/.codex/cloud-agents/submissions/` is written before each mutation, including the returned thread ID before its first turn. A lost response is **ambiguous**: inspect that record and `codex-cloud list --env <name>` before retrying. Never automatically retry a mutating call.

## Brief and reporting

Codex reads repository `AGENTS.md` and repository `.agents/skills`. Check their presence and embed required personal procedures using the main skill. This Mac's global skills, MCP setup, and conversation do not travel automatically.

Include this reporting contract:

```text
Work on issue #<N> against <base>. Keep a checklist and report Completed, Validation,
and Blocked on me in your final task response. Include exact check commands and results.
If this environment has verified GitHub write tools, open a draft PR with Closes #<N>,
update its checklist, and post questions/final reports there. Otherwise retain your changes
and return an inspectable diff, naming remaining GitHub actions for the coordinator.
Use the assigned isolated workspace and commit only your task's files. Merge only within
explicitly stated authority. Keep unrelated sibling work intact.
```

A request to post on GitHub does not create credentials. Inspect the task response and changes even when no PR exists. A terminal task state, an applied diff, and a merged PR are distinct results.

Embed the shared cloud workflow's execution and event contract. A diff-only result needs a remote publisher/validator route or a recorded phase blocker; the local coordinator can inspect evidence without taking over computation.

## Inspect and continue

```bash
codex-cloud status <thread-id>
codex-cloud turns <thread-id> --order desc
codex-cloud items <thread-id> --turn <turn-id> --order desc
codex-cloud watch <thread-id> --seconds 30
codex-cloud followup <thread-id> --brief /tmp/cloud-followup.md
codex-cloud stop <thread-id>
```

`status` returns thread state, the latest turn, and the actual URL. `items` paginates persisted history, including agent messages and tool results; live items can lag persistence. `watch` resumes/attaches to the existing task and streams live notifications and pending server requests. Detaching preserves the running task. Inspect active flags, errors, and pending requests before classifying a silent task as stalled. A follow-up starts an idle turn and inherits its recorded model/effort; explicit `--model` and `--effort` override independently. `stop` interrupts the active turn. Archive only after recording the final result, when requested, using `codex-cloud archive <id>`.

Use the watcher status snapshot for routine sweeps. On a new terminal turn, pending request or specific quiet reminder, fetch that turn's items with `--order desc` for the result tail; the default page is bounded. Add `--all` with `--turn` when the needed evidence spans that turn's pages. Full thread history is for investigating a named gap. Cache the inspected turn/head under the shared cloud workflow before another sweep.

For additional protocol operations, `codex-cloud rpc <method> --params <JSON-file>` sends one request. Read the operation's actual schema and inspect pending requests before replying or steering; this adapter does not automatically answer approvals. Unsupported operations fail explicitly. Current thread URLs can contain `/local/` and `hostId=local`; confirm the returned `codex-cloud-agent` source and current environment config instead of inferring execution location from the URL.

The dispatch helper writes `~/.codex/cloud-agents/<owner>-<repo>.tsv` with `ticket<TAB>thread_id<TAB>url<TAB>dispatched_epoch<TAB>codex<TAB>environment_id<TAB>base<TAB>model<TAB>effort`. For an already-created task, `record-codex.sh` takes those fields and records idempotently. A setup conversation is not a fresh task.

## Retrieve and review

```bash
codex-cloud diff <thread-id> --cwd /workspace/<repo-directory> --base origin/<base> > /tmp/cloud-result.patch
```

This executes `git diff --binary <base> --` in the task's actual cloud environment and retrieves the patch over the authenticated connection. Verify the cloud base commit and `git status` first; have the worker commit or stage new files so they are included. Inspect the final report and needed diff evidence locally. Apply, review and validate the result in the recorded remote publisher/integration workspace, then create/update the PR within the user's authority. A missing remote route is a phase blocker under the shared cloud workflow. Link each worked-on PR to T3 when available. Verify merge and issue closure through GitHub; task completion is not a landing.

References: [current cloud environments](https://learn.chatgpt.com/docs/environments/cloud-environments), [app-server protocol](https://learn.chatgpt.com/docs/app-server), [skills](https://learn.chatgpt.com/docs/build-skills).
