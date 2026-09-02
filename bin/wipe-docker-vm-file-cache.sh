#!/usr/bin/env bash
#
# Flush the Docker Desktop VM's page/dentry/inode caches, forcing VirtioFS to
# release its host-side macOS file handles. Fixes "Too many open files in
# system" errors inside containers doing heavy I/O on bind mounts (pnpm,
# composer, etc.). Non-destructive; handles re-accumulate over time, so run
# again whenever the error reappears.

set -euo pipefail

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: docker command not found. Is Docker Desktop installed?" >&2
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "ERROR: Docker daemon is not running. Start Docker Desktop first." >&2
  exit 1
fi

before=$(sysctl -n kern.num_files)
maxfiles=$(sysctl -n kern.maxfiles)

echo "i  Open files before: ${before} / ${maxfiles}"
echo "i  Flushing Docker VM caches..."

docker run --rm --privileged alpine sh -c 'sync; echo 3 > /proc/sys/vm/drop_caches'

sleep 3
after=$(sysctl -n kern.num_files)

echo "✅ Done. Open files after: ${after} / ${maxfiles} (freed $((before - after)))"
