#!/usr/bin/env bash
set -euo pipefail

RELEASE="${1:-release_6.2.x}"

uv run saf sync-repos --release "${RELEASE}"
