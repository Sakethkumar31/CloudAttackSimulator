@echo off
REM Auto-start Cloud Attack Lab Docker Stack
REM This script starts all services including Caldera

setlocal enabledelayedexpansion

cd /d "C:\Users\91895\Desktop\projects\cloud-attack-lab"

echo.
echo ========================================
echo Cloud Attack Lab - Docker Stack Startup
echo ========================================
echo.

echo [*] Waiting for Docker daemon to be ready...
timeout /t 5 /nobreak

echo [*] Starting services...
docker compose -f docker-compose.production.yml up -d

echo.
echo [*] Waiting for services to become healthy...
timeout /t 15 /nobreak

echo.
echo ========================================
echo Services Status:
echo ========================================
docker compose -f docker-compose.production.yml ps

echo.
echo ========================================
echo Access Points:
echo ========================================
echo Caldera Web UI:  http://localhost:8888
echo Dashboard:       http://localhost:5000
echo Neo4j Browser:   http://localhost:7474
echo Redis:           localhost:6379
echo.

pause
