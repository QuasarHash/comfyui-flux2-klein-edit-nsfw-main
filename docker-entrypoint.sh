#!/usr/bin/env bash
set -euo pipefail

if [[ -x /link-impact-models.sh ]]; then
  /link-impact-models.sh || echo "[entrypoint] link-impact-models.sh had warnings" >&2
fi

exec /start.sh "$@"