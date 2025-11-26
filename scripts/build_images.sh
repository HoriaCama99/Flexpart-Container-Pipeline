#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [[ ! -f "$REPO_ROOT/docker/flexpart/Dockerfile.arm64" ]]; then
  echo "FLEXPART Dockerfile missing" >&2
  exit 1
fi
if [[ ! -f "$REPO_ROOT/docker/flex_extract/Dockerfile.convert2" ]]; then
  echo "flex_extract Dockerfile missing" >&2
  exit 1
fi

echo "Building FLEXPART image..."
docker build -t flexpart-v10.4-arm64:latest -f "$REPO_ROOT/docker/flexpart/Dockerfile.arm64" "$REPO_ROOT"

echo "Building flex_extract convert2 image..."
docker build -t convert2:latest -f "$REPO_ROOT/docker/flex_extract/Dockerfile.convert2" "$REPO_ROOT"
