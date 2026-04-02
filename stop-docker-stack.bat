@echo off
REM Stop all Cloud Attack Lab services
REM Usage: stop-docker-stack.bat

cd /d "C:\Users\91895\Desktop\projects\cloud-attack-lab"
set "COMPOSE_FILE=docker-compose.yml"

echo.
echo ========================================
echo Cloud Attack Lab - Stopping Services
echo ========================================
echo.

echo [*] Stopping all containers...
docker compose -f "%COMPOSE_FILE%" down

echo.
echo [*] Containers stopped.
echo.

pause
