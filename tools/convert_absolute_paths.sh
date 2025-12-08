#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${1:-}"
MODE="${2:-dry-run}"

if [[ -z "${ROOT_DIR}" ]]; then
  echo "Usage: $0 <root_dir> [dry-run|execute|rollback|verify]"
  exit 1
fi

ARGS=( --root "${ROOT_DIR}" )
case "${MODE}" in
  dry-run) ARGS+=( --dry-run --verify ) ;;
  execute) ARGS+=( --execute --verify ) ;;
  rollback) ARGS+=( --rollback ) ;;
  verify) ARGS+=( --dry-run --verify ) ;;
  *) echo "Unknown mode: ${MODE}"; exit 2 ;;
esac

python "tools/convert_absolute_paths.py" "${ARGS[@]}"

