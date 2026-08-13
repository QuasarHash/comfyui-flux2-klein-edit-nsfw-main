#!/usr/bin/env python3
"""Fail Docker build if API workflows reference missing custom nodes."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent if (SCRIPT_DIR.parent / "nodes-manifest.json").exists() else SCRIPT_DIR
CUSTOM_NODES = Path("/comfyui/custom_nodes")


def node_folders() -> list[Path]:
    if not CUSTOM_NODES.is_dir():
        return []
    return [p for p in CUSTOM_NODES.iterdir() if p.is_dir()]


def class_types_in_workflow(path: Path) -> set[str]:
    wf = json.loads(path.read_text())
    return {node["class_type"] for node in wf.values()}


def main() -> int:
    manifest_path = ROOT / "nodes-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    required = set()
    for entry in manifest.get("nodes", []):
        required.update(entry.get("nodes", []))

    workflow_files = manifest.get("workflow_files") or ["api-workflow-single.json"]
    used: set[str] = set()
    for name in workflow_files:
        path = ROOT / name
        if not path.exists():
            print(f"ERROR: missing workflow file {path}", file=sys.stderr)
            return 1
        used |= class_types_in_workflow(path)

    missing = sorted(used - required)
    if missing:
        print("ERROR: class_types not listed in nodes-manifest.json:", missing, file=sys.stderr)
        return 1

    folders = node_folders()
    if folders:
        print(f"verify: {len(used)} workflow class_types, {len(folders)} custom_node folders")
    else:
        print(f"verify: {len(used)} workflow class_types (skip folder scan — build-time only)")
    for name in workflow_files:
        print("OK", name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
