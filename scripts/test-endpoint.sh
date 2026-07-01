#!/usr/bin/env bash
# Quick RunPod edit-NSFW endpoint check. Usage:
#   RUNPOD_API_KEY=xxx ./scripts/test-endpoint.sh <endpoint-id>
set -euo pipefail

ENDPOINT_ID="${1:-}"
API_KEY="${RUNPOD_API_KEY:-}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PAYLOAD="$ROOT/test-input-single.json"

if [[ -z "$ENDPOINT_ID" ]]; then
  echo "Usage: RUNPOD_API_KEY=xxx $0 <endpoint-id>"
  exit 1
fi

if [[ -z "$API_KEY" ]]; then
  echo "Set RUNPOD_API_KEY first."
  exit 1
fi

if [[ ! -f "$PAYLOAD" ]]; then
  echo "Missing $PAYLOAD — run scripts/strip_and_flatten.py first."
  exit 1
fi

echo "==> Health: $ENDPOINT_ID"
curl -sS -H "Authorization: Bearer $API_KEY" \
  "https://api.runpod.ai/v2/${ENDPOINT_ID}/health" | python3 -m json.tool || true

echo
echo "==> Submit async job (workflow only — expects worker pickup)"
BODY=$(python3 - "$PAYLOAD" <<'PY'
import json, sys
from pathlib import Path
data = json.loads(Path(sys.argv[1]).read_text())
data["input"].pop("images", None)
print(json.dumps(data))
PY
)

RESP=$(curl -sS -X POST "https://api.runpod.ai/v2/${ENDPOINT_ID}/run" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d "$BODY")

echo "$RESP" | python3 -m json.tool
JOB_ID=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))")

if [[ -z "$JOB_ID" ]]; then
  echo "No job id — check API key, endpoint id, or payload."
  exit 1
fi

echo
echo "==> Poll status for $JOB_ID (30s)"
for i in {1..10}; do
  sleep 3
  STATUS=$(curl -sS -H "Authorization: Bearer $API_KEY" \
    "https://api.runpod.ai/v2/${ENDPOINT_ID}/status/${JOB_ID}")
  echo "[$i] $STATUS"
  STATE=$(echo "$STATUS" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status',''))")
  if [[ "$STATE" != "IN_QUEUE" && "$STATE" != "IN_PROGRESS" ]]; then
    break
  fi
done