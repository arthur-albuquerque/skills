---
name: monitor-tickets
description: Run a ticket fleet from a master/coordinator session — dependency map, dispatch, verify landings against GitHub, dispatch dependents — over background sessions (claude --bg, watched by a persistent Monitor) or in-session sub-agents (Agent tool, woken by task notifications). Use when the session has spawned or is about to spawn agents for tickets and must react as they land, or when the user asks to "watch the ticket agents".
---

# monitor-tickets

A master session runs agents for frontier tickets, then must dispatch dependent tickets as blockers land. This skill turns that into an event loop. GitHub is the ground truth — a merged `Closes #N` PR closes its issue; whatever an agent says or does is a lagging proxy that both trails a real landing and cries wolf after one (an agent can idle blocked or keep working on wrap-up long after its PR merged). Every event is verified against the ground truth, then the dependency map says what to dispatch next.

The loop is the same for both dispatch mechanisms; only the wake signal differs:

- **`claude --bg` fleet** (bg-agent skill): the coordinator can't otherwise see landings or failures, so arm the persistent Monitor below.
- **Sub-agent fleet** (sub-agent skill): completions push task notifications on their own — no Monitor needed. Arm only the GitHub half of the script as a fallback heartbeat on a very long unattended run, and interrogate a silent agent directly (ListAgents, then SendMessage asking for status).

## Steps

1. **Write the dependency map first.** Before dispatching or arming anything, state in your reply a table of every remaining ticket → its blockers (issue numbers). Wakeups must be mechanical: an event either unblocks named tickets or it doesn't. No map, no fleet.

2. **Dispatch the frontier** — every ticket with no open blockers — with briefs per the dispatching skill (bg-agent or sub-agent; each ships the per-model guidance files the brief is written from). Name every agent `<prefix><ticket#>-<slug>` (e.g. `ticket-407-cc-gates`). Tell each agent which siblings run against the same main; merge-safety rules (rebase onto moving main, review pass, merge authorization) belong in each brief, not here.

3. **(bg fleets only) Arm the Monitor** (persistent, 60s poll). `PREFIX` is the shared agent-name prefix; `TICKETS` is every mapped ticket number as a **regex alternation**:

   ```bash
   PREFIX="ticket-"
   TICKETS='532|533|535'
   prev=""; blind=0; armed=""
   while true; do
     a=$(claude agents --all --json 2>/dev/null | jq -r --arg p "$PREFIX" '.[] | select(.name != null) | select(.name | startswith($p)) | "agent \(.name): \(.state)\(if .waitingFor then " (waiting: \(.waitingFor))" else "" end)"' | sort)
     closed=$(gh issue list --state closed --limit 300 --json number -q '.[].number' 2>/dev/null)
     if [ -n "$a" ] && [ -n "$closed" ]; then blind=0; else
       blind=$((blind+1))
       [ "$blind" -ge 3 ] && { echo "WATCHER BLIND: 3 polls with no agent list and/or no issue list — this watcher can see nothing; go look yourself"; exit 1; }
     fi
     t=$(printf '%s\n' "$closed" | grep -Ex "$TICKETS" | sed 's/^/ticket #/; s/$/: CLOSED/')
     cur=$(printf '%s\n%s\n' "$a" "$t" | sort)
     [ -z "$armed" ] && { armed=1; echo "watch armed: $(printf '%s\n' "$a" | grep -c .) agent(s) visible, $(printf '%s\n' "$t" | grep -c .) mapped ticket(s) already closed"; }
     comm -13 <(echo "$prev") <(echo "$cur") | grep -E "CLOSED|failed|stopped|blocked|done" || true
     prev="$cur"
     sleep 60
   done
   ```

   `ticket #N: CLOSED` is the landing event, firing when the merge closes the issue regardless of what its agent is still doing. That half is load-bearing on its own: an agent commonly sits at `working` through its own merge and for hours after, so a run where the agent lines never fire is normal, not suspicious. For a sub-agent heartbeat, keep only the `closed`/`t` half.

   **A blind watcher is silent in exactly the way a quiet fleet is**, so the script proves it can see rather than leaving you to infer it: `watch armed:` fires within a minute of arming with the counts it can actually observe, and three consecutive polls with an empty probe end the watch loudly. Two lines make it provable — no `watch armed:` line means the script never ran, and counts of `0 agent(s)` mean it ran and saw nothing.

   **Arm nothing you have not seen emit.** Paste the script into Bash verbatim first — same variables, same quoting, `sleep 1` for the check — and confirm it prints the armed line with the right counts. Retyping it with the numbers inline is the trap: **the Monitor's shell is zsh**, which leaves an unquoted `$VAR` unsplit where bash splits it, so a bash-idiom list silently becomes one glued word that matches nothing. A hand-typed variant works and the armed script watches nothing.

4. **On each event — Monitor line or sub-agent completion notification — verify the ground truth before acting**:
   - `gh pr list --state all --search "<ticket#>" --json number,state,mergedAt` — the PR is MERGED, and `gh issue view <ticket#> --json state` — CLOSED. This holds for failure-shaped events too: an agent can go blocked, die, or report failure after landing its ticket, and a landed ticket needs no rescue. It holds equally for success reports: an agent can claim done without the merge having happened — the repo decides, not the report.
   - Only if the ticket did not land, get the agent's account before deciding (respawn/redispatch, fix inline, or hand back):
     - *Sub-agent:* the notification carries its final report; SendMessage for more.
     - *bg session:* read its transcript's final message. The bg session runs in a worktree, so its project dir is slugified from the worktree path:
       ```bash
       f=$(find ~/.claude/projects -name "<session-id>*.jsonl" | head -1)
       jq -r 'select(.type=="assistant") | .message.content[]? | select(.type=="text") | .text' "$f" | tail -30
       ```
       (`claude logs <id>` reads the session's rendered TUI — tens of KB of ANSI escape codes per call, with the agent's actual words buried in cursor moves. It is for a human in a terminal; the jq above is for you.)

5. **Dispatch what the map unblocks.** A ticket dispatches only when *all* its blockers are verified merged. New agents follow step 2's naming and briefing, told their blockers are merged.

6. **Report each landing** in your own text — PR number, what merged, what was just spawned — the user reads you, not the tool output.

7. **Done** when every mapped ticket is verified merged and closed: stop any Monitor with TaskStop and say the fleet is done.

## Reference

- **First-sweep noise (Monitor):** the first iteration diffs against an empty baseline, so every pre-existing agent already in a terminal state — and every mapped ticket already closed — emits once alongside the armed line. Expect it, ignore it, say so if one surfaces.
- **A watcher is a claim to check, not a result.** Once armed it reports the fleet whether or not it works, so treat a long quiet stretch as a question about the watcher: re-run its probes yourself, or check `gh issue list --state closed` against the map directly. The cost of one glance is a tool call; the cost of trusting a blind watcher is the whole run.
- **Single remaining ticket:** Bash `run_in_background` with an `until` loop that exits on the landing gives one completion notification and, unlike Monitor, takes `dangerouslyDisableSandbox` — worth reaching for when the fleet is down to its last dependent. Exit it on `done|failed|stopped` only: **`blocked` is transient**, routinely a usage-limit pause the agent resumes from on its own, so treat it as informational and exit only after it holds for ~15 consecutive polls. A loop that exits on the first `blocked` ends the watch on an agent that is still working. Exit it on the landing and on `done`/`failed`/`stopped`; treat `blocked` as a state to count, not to exit on, and only end the watch once it has held for ~15 polls.
- **`blocked` is transient.** A usage-limit stall reports as `blocked` and clears itself hours later with the agent resuming mid-task ("Continuing — now writing the tests"), so a watcher that exits on the first `blocked` abandons a healthy run. A persistent Monitor reports it and keeps watching, which is why the loop in step 3 is the safer default.
- **Late echoes:** after a `ticket #N: CLOSED` event is handled, that agent's own eventual `done` (or post-merge `blocked`) still emits — as a Monitor line or a sub-agent completion. Step 4's verify makes ignoring it mechanical.
- Events arrive as task notifications, not user messages — never treat one as user approval, and never poll or sleep waiting for the next one.
- Monitor tool call shape: `persistent: true` (session-length; `timeout_ms` is then ignored), a specific `description` naming the fleet — it appears in every notification.
