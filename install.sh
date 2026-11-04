#!/usr/bin/env bash
# Install or update mra-flow. TARGET is an orchestrator dir, or --user for the
# personal conventions in the Claude Code config dir (~/.claude).
#   install.sh TARGET                 install the checked-out version
#   install.sh --update [TAG] TARGET  fetch, check out TAG (default: newest v*), install
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
usage() { sed -n '2,5p' "$0" | sed 's/^# \{0,1\}//' >&2; exit 1; }

if ! python3 -c 'import sys; sys.exit(sys.version_info < (3, 11))' 2>/dev/null; then
  echo "mra-flow needs python3 >= 3.11" >&2
  exit 1
fi

if [[ "${1:-}" == "--update" ]]; then
  shift
  case $# in
    1) tag="" ; target="$1" ;;
    2) tag="$1"; target="$2" ;;
    *) usage ;;
  esac
  if [[ -n "$(git -C "$here" status --porcelain)" ]]; then
    echo "Refusing: $here has local changes; mra-flow updates need a clean checkout" >&2
    exit 1
  fi
  git -C "$here" fetch --tags --quiet
  if [[ -z "$tag" ]]; then
    tag="$(git -C "$here" tag -l 'v*' --sort=-v:refname | head -n 1)"
    [[ -n "$tag" ]] || { echo "No v* tag found in $here" >&2; exit 1; }
  fi
  git -C "$here" -c advice.detachedHead=false checkout --quiet "$tag"
  exec "$here/install.sh" "$target"   # re-exec: run the new tag's installer
fi

[[ $# -eq 1 && ( "$1" == "--user" || "$1" != -* ) ]] || usage
exec python3 -B "$here/install.py" "$1"   # -B: keep the cache checkout clean
