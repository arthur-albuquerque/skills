#!/usr/bin/env bash
# Record an already-created current Codex Cloud task; this command never starts one.
set -euo pipefail
ticket=${1:?ticket or -}; id=${2:?thread ID}; url=${3:?task URL}; environment=${4:?config ID}; base=${5:?base branch}; model=${6:--}; effort=${7:--}
[[ "$ticket" == - || "$ticket" =~ ^[0-9]+$ ]] || { echo 'ticket must be a number or -' >&2; exit 1; }
for value in "$id" "$url" "$environment" "$base" "$model" "$effort"; do
  [[ -n "$value" && "$value" != *$'\t'* && "$value" != *$'\n'* ]] || { echo 'ledger fields must be single-line and contain no tabs' >&2; exit 1; }
done
[[ "$url" == https://chatgpt.com/* ]] || { echo 'use the actual ChatGPT cloud task URL' >&2; exit 1; }
repo=$(gh repo view --json nameWithOwner -q .nameWithOwner)
[[ "$repo" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]] || { echo 'not a GitHub checkout' >&2; exit 1; }
state=${CLOUD_STATE_DIR:-$HOME/.codex/cloud-agents}; mkdir -p "$state"
ledger=$state/${repo//\//-}.tsv
if [[ -f "$ledger" ]] && awk -F'\t' -v id="$id" '$2==id{found=1} END{exit !found}' "$ledger"; then
  echo "already recorded: $id"; exit 0
fi
printf '%s\t%s\t%s\t%s\tcodex\t%s\t%s\t%s\t%s\n' "$ticket" "$id" "$url" "$(date +%s)" "$environment" "$base" "$model" "$effort" >>"$ledger"
printf '%s %s\n' "$id" "$url"
