#!/bin/bash
set -e

cd /app/caldera_neo4j
SYNC_INTERVAL="${SYNC_INTERVAL:-30}"

while true; do
  echo "=== Sync run ==="
  python sync.py
  echo "Waiting ${SYNC_INTERVAL}s..."
  sleep "${SYNC_INTERVAL}"
done
