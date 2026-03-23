#!/bin/bash
# Cloud Attack Lab - Quick Reference Script
# Save as: ~/quick-commands.sh
# Usage: bash ~/quick-commands.sh [command]

PROJECT_PATH="/mnt/c/Users/91895/Desktop/projects/cloud-attack-lab"
cd "$PROJECT_PATH"

show_help() {
    cat << EOF
Cloud Attack Lab - Docker Management Commands
=============================================

Usage: script.sh [command]

QUICK ACTIONS:
  start         - Start all services
  stop          - Stop all services
  restart       - Restart all services
  logs          - Follow all logs
  logs-cal      - Follow Caldera logs only
  status        - Show service status
  health        - Show health check status
  rebuild       - Rebuild all images (--no-cache)
  clean         - Remove all containers & volumes (DESTRUCTIVE)
  info          - Show project info

DETAILED LOGS:
  logs-neo4j    - Neo4j logs
  logs-redis    - Redis logs
  logs-dash     - Dashboard logs
  logs-sync     - Sync Worker logs
  logs-graph    - Graph Writer logs

TESTING:
  test-cal      - Test Caldera connectivity
  test-dashboard - Test Dashboard connectivity
  test-neo4j    - Test Neo4j connectivity
  test-redis    - Test Redis connectivity

COMMANDS:
  docker compose ps                          - Show running containers
  docker compose exec caldera bash           - Shell into Caldera
  docker compose exec neo4j cypher-shell     - Neo4j shell
  docker compose exec redis redis-cli        - Redis CLI

URLS:
  Caldera:      http://localhost:8888
  Dashboard:    http://localhost:5000
  Neo4j:        http://localhost:7474
  Redis:        localhost:6379

EOF
}

case "$1" in
    start)
        echo "[*] Starting services..."
        docker compose up -d
        sleep 10
        docker compose ps
        ;;
    stop)
        echo "[*] Stopping services..."
        docker compose down
        ;;
    restart)
        echo "[*] Restarting services..."
        docker compose restart
        sleep 5
        docker compose ps
        ;;
    logs)
        docker compose logs -f
        ;;
    logs-cal)
        docker compose logs -f caldera
        ;;
    logs-neo4j)
        docker compose logs -f neo4j
        ;;
    logs-redis)
        docker compose logs -f redis
        ;;
    logs-dash)
        docker compose logs -f dashboard
        ;;
    logs-sync)
        docker compose logs -f sync-worker
        ;;
    logs-graph)
        docker compose logs -f graph-writer
        ;;
    status)
        docker compose ps
        ;;
    health)
        echo "Service Health Status:"
        for service in caldera neo4j redis dashboard sync-worker graph-writer; do
            health=$(docker inspect --format='{{.State.Health.Status}}' $service 2>/dev/null || echo "N/A")
            echo "  $service: $health"
        done
        ;;
    rebuild)
        echo "[*] Rebuilding all images..."
        docker compose down
        docker compose build --no-cache
        docker compose up -d
        ;;
    clean)
        echo "[!] DESTRUCTIVE: Removing all containers & volumes..."
        read -p "Continue? (y/N): " confirm
        if [ "$confirm" = "y" ]; then
            docker compose down -v
            echo "[+] Cleaned."
        fi
        ;;
    test-cal)
        echo "[*] Testing Caldera..."
        curl -f http://localhost:8888 && echo "[+] Caldera UP" || echo "[-] Caldera DOWN"
        ;;
    test-dashboard)
        echo "[*] Testing Dashboard..."
        curl -f http://localhost:5000 && echo "[+] Dashboard UP" || echo "[-] Dashboard DOWN"
        ;;
    test-neo4j)
        echo "[*] Testing Neo4j..."
        curl -f http://localhost:7474 && echo "[+] Neo4j UP" || echo "[-] Neo4j DOWN"
        ;;
    test-redis)
        echo "[*] Testing Redis..."
        redis-cli -h localhost ping && echo "[+] Redis UP" || echo "[-] Redis DOWN"
        ;;
    info)
        echo "Project: Cloud Attack Lab"
        echo "Path: $PROJECT_PATH"
        echo "Backend: Caldera C2 Framework"
        echo "Database: Neo4j 5"
        echo "Cache: Redis 7"
        echo "Dashboard: Flask Web UI"
        echo ""
        echo "Services:"
        docker compose ps
        ;;
    *)
        show_help
        ;;
esac
