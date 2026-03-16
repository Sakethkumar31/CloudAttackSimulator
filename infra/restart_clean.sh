#!/bin/bash
# Clean restart script for Cloud Attack Lab
# Stops all containers, removes images, and rebuilds from scratch

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

ENV_FILE="${1:-infra/.env.phase2}"
COMPOSE_FILE="${2:-infra/docker-compose.phase2.yml}"

echo "[Cloud Attack Lab] Stopping and removing all containers..."
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" down --remove-orphans 2>/dev/null || true

echo "[Cloud Attack Lab] Removing dangling images..."
docker image prune -af

echo "[Cloud Attack Lab] Removing unused volumes (optional - add --volumes to remove all)..."
# docker volume prune -f  # Uncomment if you want to remove volumes

echo "[Cloud Attack Lab] Building and starting fresh..."
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d --build

echo ""
echo "[Cloud Attack Lab] Stack is starting..."
echo "  - Dashboard: http://localhost:5000"
echo "  - CALDERA:   http://localhost:8888"
echo "  - Neo4j:     http://localhost:7474"
echo ""
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" ps
