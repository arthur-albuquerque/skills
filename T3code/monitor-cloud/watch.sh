#!/usr/bin/env bash
# GitHub landings and current Codex task states; compatible with old Claude ledgers.
set -uo pipefail
TICKETS=${1:?usage: watch.sh '532|533' [owner/repo]}
[[ "$TICKETS" =~ ^[0-9]+(\|[0-9]+)*$ ]] || { echo 'tickets must be numbers separated by |' >&2; exit 1; }
REPO=${2:-$(gh repo view --json nameWithOwner -q .nameWithOwner)}
[[ "$REPO" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]] || { echo 'WATCHER BLIND: no GitHub repo'; exit 1; }
INTERVAL=${WATCH_INTERVAL:-60}; POLLS=${WATCH_POLLS:-0}; QUIET_MIN=${QUIET_MIN:-120}; PR_LIMIT=${WATCH_PR_LIMIT:-1000}
for value in "$INTERVAL" "$POLLS" "$QUIET_MIN" "$PR_LIMIT"; do
  [[ "$value" =~ ^[0-9]+$ ]] || { echo 'watcher knobs must be nonnegative integers' >&2; exit 1; }
done
QUIET=$((QUIET_MIN * 60))
CLAUDE_LEDGER=${CLAUDE_LEDGER:-$HOME/.claude/cloud-agents/${REPO//\//-}.tsv}
CODEX_LEDGER=${CODEX_LEDGER:-$HOME/.codex/cloud-agents/${REPO//\//-}.tsv}
skill_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
CODEX_CLOUD_CLI=${CODEX_CLOUD_CLI:-$skill_dir/../cloud-agents/codex-cloud.py}
[[ -n "${LEDGER:-}" ]] && { CLAUDE_LEDGER=$LEDGER; CODEX_LEDGER=$LEDGER; }
if [[ -n "${WATCH_STATE:-}" ]]; then st=$WATCH_STATE; mkdir -p "$st"; else st=$(mktemp -d); trap 'rm -rf "$st"' EXIT; fi
blind=0; n=0; prev=$(cat "$st/prev" 2>/dev/null || true)

ledger_rows() {
  # Default four-column Claude rows and explicit current Codex provider rows share a format.
  for ledger in "$CLAUDE_LEDGER" "$CODEX_LEDGER"; do
    provider=claude; [[ "$ledger" == "$CODEX_LEDGER" && "$ledger" != "$CLAUDE_LEDGER" ]] && provider=codex
    [[ -f "$ledger" ]] || continue
    awk -F'\t' -v re="^($TICKETS)$" -v provider="$provider" \
      '$1 ~ re && NF>=4 {printf "%s\t%s\t%s\t%s\t%s\n",$1,$2,$3,$4,($5=="codex" || $5=="claude" ? $5 : provider)}' "$ledger"
  done | sort -u
}

snapshot() {
  local t prs count
  for t in ${TICKETS//|/ }; do
    gh issue view "$t" -R "$REPO" --json number,state,comments,updatedAt \
      -q '"\(.number)\tissue\t\(.state)\t\(.comments|length)\t\(.updatedAt)"' || return 1
  done
  prs=$(gh pr list -R "$REPO" --state all --limit "$PR_LIMIT" --json number,state,isDraft,comments,updatedAt,closingIssuesReferences) || return 1
  count=$(printf '%s' "$prs" | jq length) || return 1
  [[ "$count" -lt "$PR_LIMIT" ]] || { echo 'PR scan reached WATCH_PR_LIMIT' >&2; return 1; }
  printf '%s' "$prs" | jq -r '.[] | . as $p | .closingIssuesReferences[] | "\(.number)\tpr #\($p.number)\t\(if $p.state=="OPEN" and $p.isDraft then "DRAFT" else $p.state end)\t\($p.comments|length)\t\($p.updatedAt)"'
}

codex_snapshot() {
  local t id url epoch provider result summary
  while IFS=$'\t' read -r t id url epoch provider; do
    [[ "$provider" == codex ]] || continue
    if result=$("$CODEX_CLOUD_CLI" status "$id" 2>/dev/null) && \
       summary=$(printf '%s' "$result" | jq -er '[.latestTurn.status // "no-turn", .thread.status.type, ((.thread.status.activeFlags // [])|join(",")), .latestTurn.id // "-"] | @tsv'); then
      printf 'ticket #%s codex %s: %s\n' "$t" "$id" "$summary"
    else
      printf 'ticket #%s CODEX WATCHER BLIND %s: check login, network and task ID\n' "$t" "$id"
    fi
  done < <(ledger_rows)
}

while :; do
  if raw=$(snapshot 2>/dev/null); then
    blind=0
    raw=$(printf '%s\n' "$raw" | awk -F'\t' -v re="^($TICKETS)$" '$1 ~ re')
    cloud=$(codex_snapshot)
    cur=$({ printf '%s\n' "$raw" | awk -F'\t' 'NF{printf "ticket #%s %s: %s, %s comments\n",$1,$2,$3,$4}'; printf '%s\n' "$cloud"; } | grep . | LC_ALL=C sort)
    if [[ "$n" -eq 0 ]]; then
      vis=$(printf '%s\n' "$raw" | awk -F'\t' '$2=="issue"{n++} END{print n+0}')
      cl=$(printf '%s\n' "$raw" | awk -F'\t' '$2=="issue" && $3=="CLOSED"{n++} END{print n+0}')
      led=$(ledger_rows | awk 'END{print NR+0}')
      echo "watch armed: $REPO — $vis mapped ticket(s) visible, $cl already closed, $led dispatched in ledger${prev:+ (resumed from $st)}"
      [[ -z "$prev" ]] && printf '%s\n' "$cloud" | grep . || true
    fi
    if [[ "$n" -gt 0 || -n "$prev" ]]; then
      LC_ALL=C comm -13 <(printf '%s\n' "$prev" | LC_ALL=C sort) <(printf '%s\n' "$cur") | grep . || true
    fi
    prev=$cur; printf '%s\n' "$prev" >"$st/prev"
    now=$(date +%s)
    for t in $(ledger_rows | cut -f1 | sort -u); do
      printf '%s\n' "$raw" | awk -F'\t' -v t="$t" '$1==t && $2=="issue" && $3=="OPEN"' | grep -q . || continue
      d=$(ledger_rows | awk -F'\t' -v t="$t" '$1==t{print $4}' | sort -n | tail -1)
      [[ "$d" =~ ^[0-9]+$ ]] || { echo "WATCHER BLIND: invalid dispatch epoch for ticket #$t"; exit 1; }
      sig=$(printf '%s\n' "$raw" | awk -F'\t' -v t="$t" '$1==t{print $5}' | sort | tr '\n' ' ')
      sig="$sig dispatch=$d"
      if [[ "$sig" != "$(cat "$st/sig.$t" 2>/dev/null || true)" ]]; then
        printf '%s' "$sig" >"$st/sig.$t"; echo "$now" >"$st/at.$t"; rm -f "$st/quiet.$t"
      fi
      at=$(cat "$st/at.$t"); [[ "$d" -gt "$at" ]] && at=$d
      if [[ $((now - at)) -ge "$QUIET" && ! -e "$st/quiet.$t" ]]; then
        touch "$st/quiet.$t"
        echo "ticket #$t: no GitHub activity for $(( (now - at) / 60 ))m — inspect its provider task/session"
      fi
    done
  else
    blind=$((blind + 1))
    [[ "$blind" -ge 3 ]] && { echo "WATCHER BLIND: 3 polls without a complete snapshot from $REPO — check auth, network, mapped issues and WATCH_PR_LIMIT"; exit 1; }
  fi
  n=$((n + 1)); [[ "$POLLS" -gt 0 && "$n" -ge "$POLLS" ]] && exit 0
  sleep "$INTERVAL"
done
