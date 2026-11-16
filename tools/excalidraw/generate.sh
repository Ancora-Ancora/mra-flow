#!/usr/bin/env bash
# Regenerate payload/orchestrator/.mra-flow/docs/mra-flow.excalidraw from mra-flow.md.
# Needs node and Chromium's system libraries (npx playwright install-deps chromium, once).
set -euo pipefail
cd "$(dirname "$0")"
out="../../payload/orchestrator/.mra-flow/docs/mra-flow.excalidraw"
[[ -d node_modules ]] || npm install --silent --no-audit --no-fund
npx --no-install playwright install chromium >/dev/null
python3 -B prepare.py
for attempt in 1 2 3 4; do   # headless Chromium sometimes closes on its first page here; retry
  if timeout 120 node extract.cjs | tee /dev/stderr | grep -q '^err: none'; then break; fi
  [[ $attempt == 4 ]] && { echo "extract failed" >&2; exit 1; }
done
python3 -B build.py "$out"
echo "wrote $out"
