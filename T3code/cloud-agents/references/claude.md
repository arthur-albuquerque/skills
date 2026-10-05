# Claude cloud sessions

Read this reference only for Claude dispatches. These provider-specific probes and conventions do not apply to Codex.

For dispatch, review and recovery, apply [the shared cloud workflow](cloud-workflow.md); the commands here supply Claude's transport.

## Preflight, once per repo

- The repo is on github.com, and the branch you dispatch from is pushed: `git status -sb` shows no `ahead`, and every file the agent needs (`AGENTS.md`, docs, specs) is committed.
- **The Claude GitHub App is installed on the repo** — `/web-setup` alone isn't enough. It must be installed on the GitHub account that owns the repo, with this repo among its selected repositories, and connected to the same claude.ai account. Without the app, the CLI uploads a bundle of the local repo instead: the VM has no git remote and no GitHub MCP tools, so the agent can't push, open a PR, or comment, and the whole GitHub channel is dead. `dispatch.sh` prints `BUNDLED — Bundling (reason: …)` when this happens, from the CLI's own preflight (`GitHub app is not installed on <repo>`). On that line, stop new Claude dispatches, retain any returned session ID and hand the install prerequisite to the user. Preserve already-running workers.
- The selected cloud environment gives the test suite what it needs beyond the [pre-installed tools](https://code.claude.com/docs/en/cloud-environments#installed-tools) — env vars, a setup script, network hosts. Configure it at claude.ai/code using available browser access; involve the user for missing login or access.

Done when the dispatch branch and every required input are pushed and environment prerequisites are resolved. The app check fires at dispatch, on the `BUNDLED` line.

## Claude brief additions

Use the provider/model/effort resolved by the main skill. Pass the exact supported model ID and effort explicitly through the dispatch helper; check current Claude help and cloud availability first. If the cloud service cannot honor an inherited or requested value, ask for that field's replacement before submitting. Read [Opus guidance](opus-guidance.md) for an Opus selection or [Fable guidance](fable-guidance.md) for a Fable selection; apply it to the brief while keeping the user's resolved model and effort. Use the main cloud-agents brief workflow for shared requirements.

Claude loads repository `CLAUDE.md`/`AGENTS.md`, `.claude/{skills,agents,commands,rules}`, and account-synced skills (locally mirrored in `~/.claude/skills/synced/`). Check these before relying on a procedure; absent personal and plugin procedures must travel in the brief.

Fill and paste this reporting contract:

```text
GitHub is your channel to the coordinator.
- After your first commit, open a draft PR against <base> with Closes #<N> and task checkboxes. Update them as work lands.
- Post unresolved questions on issue #<N>; continue independent work. Answers arrive as session messages.
- Before your last message, post Completed, Validation, and Blocked on me on the PR (or issue if no PR exists).
- Push to this session's assigned claude/... branch. Use the available GitHub MCP write tools; the probed proxy rejects gh issue/gh pr GraphQL calls. gh api REST is the fallback.
```

For required Codex review rounds, use "Remote review" below. Embed the shared cloud workflow's execution and event contract with these provider additions.

## Dispatch

From the repo checkout:

```bash
bash ~/.agents/skills/cloud-agents/dispatch.sh claude /tmp/cloud-brief-<slug>.md <model> <effort> <ticket> [environment]   # ticket `-` for non-ticket work
```

It prints `<session_id> <url>` and appends the main skill's ledger row, including the selected model and effort, to `~/.claude/cloud-agents/<owner>-<repo>.tsv`. `claude --cloud` demands a real terminal and takes the brief as its own value (`--cloud "<brief>"`), so the script runs it in a detached tmux session and reads the pane. A brief's quotes, `$` and backticks arrive intact.

**Environments.** `[environment]` picks the cloud environment for this one session by name, from `~/.claude/cloud-agents/environments.tsv` (`name<TAB>env_id`, matched case-insensitively). Omitted, the session uses the `/remote-env` default. The script passes the ID through `--settings`, so the user's saved default never changes. Pick it from the user's words ("on R") or the work: R/Quarto/Stan → `R`, whose setup script and network allowlist are in `~/.claude/cloud-agents/r-environment/`. A new environment is one more row in the table: its ID is what `/remote-env` prints when the user selects it.

## Manage

```bash
claude -p "<message>" --cloud <session_id> --output-format json   # steer or answer; prints {ok, session_id, url}
```

- **Read inside:** `RemoteTrigger` with `action: get_run_log` and the `session_id` returns the session's condensed log — prompt, tool calls, errors, replies. It is the coordinator's view of any cloud session, not just routines.
- **Show the user:** give them `https://claude.ai/code/<session_id>`, or `claude --teleport <session_id>` to pull the session and its branch into a terminal (interactive — suggest it, never run it).
- **Stop or archive:** the user does it at claude.ai/code; the CLI has no stop for cloud sessions.
- **A stalled run:** inspect its new log/checklist evidence before continuing it with remaining actionable work, as opus-guidance's continuation rule describes — two or three continuations at most. A dependency wait or unchanged checklist stays recorded under the shared cloud workflow.

## Remote review

The probed Claude cloud VMs had no Codex or ChatGPT login. A required Codex pass therefore needs a preflighted Codex cloud task or configured remote review runner with access to the exact pushed head/base. The local coordinator dispatches and relays that review; the Claude worker keeps the Claude pass, fixes and round count. In the brief, the rider's step 1 becomes:

```text
The monitor owner dispatches the required Codex review through <verified remote route>. When a round is due, push, then post one PR comment starting `Review round <n> ready`, naming the exact head SHA and base. Continue work independent of the review. Findings arrive as a session message; perform the Claude pass and fixes here. A missing remote review route leaves that gate pending.
```

On that new event, the monitor owner dispatches the remote reviewer once, carrying the required review procedure, exact revision/base and resolved reviewer settings. Retain its actual findings and revision evidence, convert remote absolute paths to repository-relative paths, then relay the findings with `claude -p "<findings>" --cloud <session_id>`. Reuse a review only while its reviewed scope is unchanged. If the remote route is unavailable, record `review pending` and resolve the prerequisite through the shared cloud workflow; keep the required provider and independent gate intact.

## What a cloned session has (probed 2026-09-27)

A session cloned through the Claude GitHub App starts on a fresh `claude/<slug>` branch with `origin` set and push access through the proxy. It has the GitHub MCP server scoped to the repo: issues, PRs, comments, reviews, merge. `gh` is pre-installed in both environments (probed 2026-10-01: `/usr/local/bin/gh` in R and Default sessions alike), so a setup script needn't install it. The GitHub proxy rejects all GraphQL with a 403, which takes out `gh issue view/list/comment/edit` and `gh pr ...`: only `gh api repos/<owner>/<repo>/...` (REST) and the MCP tools reach GitHub. The 403 names the REST fallback and agents switch on their own, so a repo doc prescribing `gh issue ...` needs no rewrite.

## Assigned peer handoffs (probed 2026-10-01)

Apply the shared cloud workflow's event rules before assigning a peer handoff; ordinary fleet reporting uses GitHub and the monitor owner. For an assigned handoff, cloud sessions under one account use `mcp__claude-code-remote__send_message`: pass the recipient's `session_id`, the concrete action/question and event ID, plus `priority: "later"`. It works within one environment and across environments (R ↔ Default). A message to an idle session wakes it, and the recipient reads it with `ReadNotifications` as a `<cross-session-message from-session=…>` block. `later` changes delivery timing, not the need for a reply.

- **Approval.** Each session's first `send_message` raises a claude.ai prompt ("This connector call requires your approval to proceed"). The user approves it with "always allow", and that session doesn't ask again. No account-wide setting removes it; the connectors page doesn't list this built-in server. A second, in-VM prompt would come on top, but it is removed by the allow rule the R and Default setup scripts write to `/root/.claude/settings.json`. Dispatch-time `--allowedTools`/`--settings` don't reach the cloud. A brief that needs peer messaging tells the agent to send its first message early, and tells the user to expect one approval per session.
- **Addressing.** The brief gives each agent its peers' `session_…` IDs. A session can also look them up with `mcp__claude-code-remote__list_sessions`, which is pre-allowed.
- **Dead ends.** `ListAgents`/`SendMessage` see only the session's own VM. `claude -p … --cloud` inside the VM fails with "Session expired. Please run /login". `send_later` targets only the calling session. `/mnt/user-data` is per-VM.
- **Local ↔ cloud.** Local → cloud works (`claude -p … --cloud`). Cloud → local does not: a plain local session has no ID in the cloud session API, so `send_message` to its UUID fails with "target session could not be verified". Only Remote Control sessions appear there (`environment_kind: bridge`), and that route is untested. Cloud sessions report back through the GitHub channel, or the coordinator reads them with `RemoteTrigger get_run_log`.
