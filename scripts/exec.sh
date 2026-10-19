#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'HELP'
Usage: scripts/exec.sh [--open-files N] [--mimalloc-purge-delay MS] -- COMMAND [ARGS...]

Apply only explicitly requested launch settings, then exec an existing command.
No build, server lifecycle, privileged setup or timing default is implied.
HELP
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --open-files)
      [[ $# -ge 2 && "$2" =~ ^[1-9][0-9]*$ ]] || { echo 'Positive open-file limit required.' >&2; exit 2; }
      ulimit -S -n "$2"
      shift 2
      ;;
    --mimalloc-purge-delay)
      [[ $# -ge 2 && "$2" =~ ^[0-9]+$ ]] || { echo 'Non-negative purge delay required.' >&2; exit 2; }
      export MIMALLOC_PURGE_DELAY="$2"
      shift 2
      ;;
    --help|-h) usage; exit 0 ;;
    --) shift; break ;;
    *) usage >&2; exit 2 ;;
  esac
done
[[ $# -gt 0 ]] || { usage >&2; exit 2; }
exec "$@"
