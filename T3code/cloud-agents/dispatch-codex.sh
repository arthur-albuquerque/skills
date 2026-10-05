#!/usr/bin/env bash
# Dispatch through the current cloud app-server; record only admitted work.
set -euo pipefail
brief=${1:?usage: dispatch.sh codex <brief> <environment> <model> <effort> [ticket] [base]}
environment=${2:?current environment required}; model=${3:?resolved model required}; effort=${4:?resolved effort required}
ticket=${5:--}; base=${6:-$(git symbolic-ref --short HEAD)}
[[ -s "$brief" ]] || { echo "empty or missing brief: $brief" >&2; exit 1; }
[[ "$ticket" == - || "$ticket" =~ ^[0-9]+$ ]] || { echo 'ticket must be a number or -' >&2; exit 1; }
repo=$(gh repo view --json nameWithOwner -q .nameWithOwner)
git check-ref-format --branch "$base" >/dev/null
[[ -n "$(git ls-remote --heads origin "refs/heads/$base")" ]] || { echo 'base branch is not pushed' >&2; exit 1; }
skill_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
out=$(mktemp); trap 'rm -f "$out"' EXIT
cli=${CODEX_CLOUD_CLI:-$skill_dir/codex-cloud.py}
# stdout is JSON; diagnostic output and the saved recovery record remain on stderr.
"$cli" exec --env "$environment" --brief "$brief" --model "$model" --effort "$effort" --branch "$base" --repo "$repo" >"$out"
fields=$(python3 - "$out" <<'PY'
import json,sys
x=json.load(open(sys.argv[1]))
if x.get('phase')!='admitted': raise SystemExit('submission was not admitted')
print('\t'.join(x[k] for k in ['threadId','url','environment']))
PY
)
IFS=$'\t' read -r id url config_id <<<"$fields"
bash "$skill_dir/record-codex.sh" "$ticket" "$id" "$url" "$config_id" "$base" "$model" "$effort"
