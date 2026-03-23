#!/bin/bash
# Auto-start Cloud Attack Lab on Docker startup (WSL)
# Place in: /home/saketh/.docker/wsl/startup.sh

cd /mnt/c/Users/91895/Desktop/projects/cloud-attack-lab

echo "==========================================="
echo "Cloud Attack Lab - Docker Stack Startup"
echo "==========================================="
echo ""
echo "[*] Starting all services..."
docker compose up -d

echo ""
echo "[*] Waiting for services to stabilize..."
sleep 10

echo ""
echo "==========================================="
echo "Services Status:"
echo "==========================================="
docker compose ps

echo ""
echo "==========================================="
echo "Access Points:"
echo "==========================================="
echo "Caldera Web UI:  http://localhost:8888"
echo "Dashboard:       http://localhost:5000"
echo "Neo4j Browser:   http://localhost:7474"
echo "Redis CLI:       redis-cli -h localhost -p 6379"
echo ""
