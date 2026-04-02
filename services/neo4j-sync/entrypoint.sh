#!/bin/bash
set -u

cd /app/caldera_neo4j
SYNC_INTERVAL="${SYNC_INTERVAL:-30}"
SYNC_RETRY_DELAY="${SYNC_RETRY_DELAY:-10}"

while true; do
  echo "=== Sync run ==="
  if python sync.py; then
    echo "Waiting ${SYNC_INTERVAL}s..."
    sleep "${SYNC_INTERVAL}"
  else
    status=$?
    echo "Sync failed with exit code ${status}. Retrying in ${SYNC_RETRY_DELAY}s..."
    sleep "${SYNC_RETRY_DELAY}"
  fi
done
