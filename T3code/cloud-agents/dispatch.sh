#!/usr/bin/env bash
# Provider router. The old Claude argument order remains supported through the symlink.
set -euo pipefail
skill_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
case "${1:-}" in
  claude) shift; exec bash "$skill_dir/dispatch-claude.sh" "$@" ;;
  codex) shift; exec bash "$skill_dir/dispatch-codex.sh" "$@" ;;
  -h|--help|'')
    printf '%s\n' \
      'dispatch.sh claude <brief> <model> <effort> [ticket] [environment-name]' \
      'dispatch.sh codex <brief> <current-environment-name-or-id> <model> <effort> [ticket] [base]' \
      'Legacy: dispatch.sh <brief> <model> <effort> [ticket] [environment-name]'
    exit 0 ;;
  *) exec bash "$skill_dir/dispatch-claude.sh" "$@" ;;
esac
