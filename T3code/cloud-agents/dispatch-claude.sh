#!/usr/bin/env bash
# Dispatch one cloud session and record it in the ledger. Run from the repo checkout.
#   dispatch.sh <brief-file> <model> <effort> [ticket] [environment]
# [environment] is a name from ~/.claude/cloud-agents/environments.tsv (name<TAB>env_id); omitted,
# the session runs in the /remote-env default. Either way the saved default is left unchanged.
# Prints the session ID and URL; exits non-zero with the CLI's output when no session was created.
# `claude --cloud` refuses to run without a TTY, so it runs inside a detached tmux session.
set -euo pipefail
brief=${1:?usage: dispatch.sh <brief-file> <model> <effort> [ticket]}; model=${2:?model}; effort=${3:?effort}; ticket=${4:--}; envname=${5:-}
[ -s "$brief" ] || { echo "empty or missing brief: $brief"; exit 1; }
state_dir=${CLOUD_STATE_DIR:-$HOME/.claude/cloud-agents}
settings=()
if [ -n "$envname" ]; then
  envid=$(awk -F'\t' -v n="$envname" 'tolower($1) == tolower(n) { print $2 }' "$state_dir/environments.tsv" 2>/dev/null || true)
  [ -n "$envid" ] || { echo "unknown environment: $envname (known: $(cut -f1 "$state_dir/environments.tsv" | paste -sd, -))"; exit 1; }
  settings=(--settings "{\"remote\":{\"defaultEnvironmentId\":\"$envid\"}}")
fi
repo=$(gh repo view --json nameWithOwner -q .nameWithOwner) || { echo "not in a GitHub checkout"; exit 1; }
ledger=$state_dir/${repo//\//-}.tsv; mkdir -p "${ledger%/*}"
tag=cloud-dispatch-$$; out=$(mktemp); dbg=$(mktemp)
printf -v command '%q ' claude --debug-file "$dbg" ${settings[@]+"${settings[@]}"} --model "$model" --effort "$effort" --cloud "$(cat -- "$brief")"
cleanup() { tmux kill-session -t "$tag" 2>/dev/null || true; rm -f "$out" "$dbg"; }
trap cleanup EXIT
# Keep the capture pane alive briefly after completion; every argument is shell-escaped.
tmux new-session -d -s "$tag" -x 250 -y 50 "$command; echo EXITED=\$?; sleep 300"
for _ in $(seq 1 60); do
  tmux capture-pane -p -t "$tag" -S -500 >"$out" 2>/dev/null; grep -q '^EXITED=' "$out" && break
  grep -qi 'trust this folder' "$out" && { echo "workspace trust prompt: run claude once in this folder interactively, then retry"; tmux kill-session -t "$tag"; exit 1; }
  sleep 2
done
tmux kill-session -t "$tag" 2>/dev/null || true
sid=$(grep -oE 'session_[A-Za-z0-9]+' "$out" | head -1 || true)
url=$(grep -oE 'https://claude\.ai/code/session_[A-Za-z0-9]+' "$out" | head -1 || true)
if [ -z "$sid" ]; then echo "dispatch failed:"; cat "$out"; rm -f "$out"; exit 1; fi
printf '%s\t%s\t%s\t%s\tclaude\t%s\t-\t%s\t%s\n' "$ticket" "$sid" "$url" "$(date +%s)" "${envname:--}" "$model" "$effort" >>"$ledger"
rm -f "$out"; echo "$sid $url"
# A bundled session has no remote, no gh and no GitHub tools: it can't push, open a PR or comment.
if reason=$(grep -oE 'Bundling \(reason: [a-z_]+\)' "$dbg" | head -1 || true) && [ -n "$reason" ]; then
  echo "BUNDLED — $reason. $(grep -oE 'GitHub app is not installed on [^ ]+' "$dbg" | head -1 || true)"
  echo "This session can't reach GitHub. Hand the Claude GitHub App install to the user before dispatching more."
fi
rm -f "$dbg"
