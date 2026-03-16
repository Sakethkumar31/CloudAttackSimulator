@echo off
setlocal

echo [Cloud Attack Lab] Clean restart - removing all containers and images...
echo.

REM Set your WSL path - using /mnt/c for Windows C: drive
set "WSL_PATH=/mnt/c/Users/91895/Desktop/projects/cloud-attack-lab"

REM Stop and remove all containers
echo [Cloud Attack Lab] Stopping containers...
wsl -d Ubuntu-22.04 -- bash -lc "cd '%WSL_PATH%' && docker compose --env-file infra/.env.phase2 -f infra/docker-compose.phase2.yml down --remove-orphans"

REM Remove dangling images
echo [Cloud Attack Lab] Removing unused images...
wsl -d Ubuntu-22.04 -- bash -lc "docker image prune -af"

REM Remove volumes (optional - comment out if you want to keep Neo4j data)
echo [Cloud Attack Lab] Removing unused volumes...
wsl -d Ubuntu-22.04 -- bash -lc "docker volume prune -f"

REM Rebuild and start
echo [Cloud Attack Lab] Building and starting fresh...
wsl -d Ubuntu-22.04 -- bash -lc "cd '%WSL_PATH%' && docker compose --env-file infra/.env.phase2 -f infra/docker-compose.phase2.yml up -d --build"

echo.
echo [Cloud Attack Lab] Stack is starting...
echo   - Dashboard: http://localhost:5000
echo   - CALDERA:   http://localhost:8888
echo   - Neo4j:     http://localhost:7474
echo.

wsl -d Ubuntu-22.04 -- bash -lc "cd '%WSL_PATH%' && docker compose --env-file infra/.env.phase2 -f infra/docker-compose.phase2.yml ps"

endlocal
