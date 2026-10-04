# Cloud fleet thread

A **cloud fleet thread** is a local Claude thread in T3 that runs a ticket fleet in the cloud: it dispatches each ticket as a `claude --cloud` session (the cloud-agents skill), watches them over GitHub (the monitor-cloud skill), and answers to the coordinator like any other thread. The cloud sessions do the work; the fleet thread is their local coordinator, the one place where Codex reviews run and where `claude -p … --cloud` reaches them.

## Launch it

- **Model:** the fleet thread runs Claude — it uses Claude Code skills and the Monitor tool. Use the coordinator's selection when it is Claude, else `claudeAgent` / `claude-opus-5-5` at `medium`.
- **Cloud workers' model:** only Claude runs in the cloud. A Claude model the user named goes to the workers; unnamed, the workers take the coordinator's model when it is Claude, else cloud-agents' own policy. Fable caps at `high`. A non-Claude model named for cloud work goes back to the user.
- **Workspace:** the fleet thread edits nothing; it only runs from the repo's primary checkout, where `claude` already trusts the folder and the base branch is the one the user pushed. In the repo's own project that is `workspaceStrategy: {type: "root"}`. When the coordinator sits in another project, launch in the coordinator's project anyway (it can see nothing else) and name the checkout path in the brief.
- **Folder trust:** `dispatch.sh` drives the interactive CLI, which stops at the workspace-trust prompt in a folder never opened interactively — and T3 runs `claude` headless, so a repo used only through T3 is untrusted. Before launching, `jq '.projects["<checkout path>"].hasTrustDialogAccepted' ~/.claude.json` must print `true`; otherwise ask the user to run `claude` once in that folder and accept.
- **Roster:** `kind` is `cloud-fleet`, `ticket` lists every ticket it owns.

## The brief

A local Claude thread reads `~/.claude`, so the brief names the skills rather than pasting them. Fill and send:

```text
You are the cloud fleet coordinator for <owner/repo>, working from <root checkout path>. Invoke the cloud-agents and monitor-cloud skills and run the tickets below by them: preflight, dependency map, briefs, dispatch, watcher, verified landings, dependents.

Tickets → blockers:
<table>

Cloud workers: model <model>, effort <effort>, environment <name, or "default">.
<merge authorization, review policy, and ticket notes, as the user stated them>

You run inside a T3 Code thread. Its Monitor has no `persistent` option, so arm the watcher by monitor-cloud's re-arm variant and re-arm it on every expiry notice. Between watcher events, ending your turn is correct: the next event wakes you.

You were dispatched by a coordinator: T3 thread `<coordinatorThreadId>`; your label is `<label>`. Report to it with the t3-code MCP tool `t3_thread_send` — threadId `<coordinatorThreadId>`, mode `queue`, message starting `[t3-report <label>]` — at each of these moments: a ticket verified landed (ticket, PR, what merged, what you dispatched next); a cloud session's question only the user can answer (verbatim, with its issue or PR link); a blocker you cannot clear (`BUNDLED`, an environment gap, a trust prompt, a session gone silent past its continuations); and the fleet done (the final table). Answers the coordinator sends you go to the cloud session with `claude -p "<answer>" --cloud <session_id>`.
```

Add opus-guidance's "Bound the scope" and "The final report" blocks; its unattended-run block stays out, since this thread ends turns by design.

## How it reads from the coordinator

The fleet thread's T3 status is `completed` between turns while its watcher runs, and its `updatedAt` moves at least every 30 minutes, at each re-arm. t3-monitor handles the kind accordingly.
