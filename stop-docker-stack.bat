@echo off
REM Stop all Cloud Attack Lab services
REM Usage: stop-docker-stack.bat

cd /d "C:\Users\91895\Desktop\projects\cloud-attack-lab"

echo.
echo ========================================
echo Cloud Attack Lab - Stopping Services
echo ========================================
echo.

echo [*] Stopping all containers...
docker compose down

echo.
echo [*] Containers stopped.
echo.

pause
