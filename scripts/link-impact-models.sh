#!/usr/bin/env bash
# Impact Subpack only lists /comfyui/models/ultralytics/bbox at validation time.
# Symlink anatomy detectors from the network volume (any common layout/name).
set -euo pipefail

VOL_ROOT="${RUNPOD_VOLUME_ROOT:-/runpod-volume}"
M="${VOL_ROOT}/models"
DEST="/comfyui/models/ultralytics/bbox"

mkdir -p "${DEST}"

find_bbox_src() {
  local name="$1"
  shift
  local alt
  local candidate
  for alt in "$name" "$@"; do
    for candidate in \
      "${M}/ultralytics/bbox/${alt}" \
      "${M}/Ultralytics/bbox/${alt}" \
      "${M}/ultralytics/${alt}" \
      "${M}/Ultralytics/${alt}" \
      "${M}/bbox/${alt}"; do
      if [[ -f "${candidate}" ]]; then
        echo "${candidate}"
        return 0
      fi
    done
  done
  return 1
}

link_bbox() {
  local dest_name="$1"
  shift
  local src
  if src="$(find_bbox_src "$dest_name" "$@")"; then
    ln -sfn "${src}" "${DEST}/${dest_name}"
    echo "[link-impact] OK ${DEST}/${dest_name} <- ${src}"
    return 0
  fi
  echo "[link-impact] MISSING ${dest_name} (tried: $dest_name $*) under ${M}/ultralytics/"
  return 1
}

# Workflow expects bbox/Nipples.pt and bbox/Pussy.pt — accept common upload names too.
link_bbox Nipples.pt nipple.pt Nipple.pt || true
link_bbox Pussy.pt pussy.pt || true

# If volume keeps .pt files only in ultralytics/ root, show what we found.
if ls -1 "${M}/ultralytics/"*.pt >/dev/null 2>&1; then
  echo "[link-impact] volume ultralytics/*.pt:"
  ls -1 "${M}/ultralytics/"*.pt 2>/dev/null || true
fi