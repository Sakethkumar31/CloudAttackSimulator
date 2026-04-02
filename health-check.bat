@echo off
REM Health check for all services
REM Usage: health-check.bat

cd /d "C:\Users\91895\Desktop\projects\cloud-attack-lab"
set "COMPOSE_FILE=docker-compose.yml"

echo.
echo ========================================
echo Cloud Attack Lab - Health Status
echo ========================================
echo.

echo [*] Service Health:
docker compose -f "%COMPOSE_FILE%" ps

echo.
echo [*] Detailed health check:
echo.

for /f "tokens=1" %%A in ('docker compose -f "%COMPOSE_FILE%" ps --format "{{.Names}}"') do (
    echo Checking %%A...
    docker inspect --format="Status: {{.State.Status}} / Health: {{.State.Health.Status}}" %%A
)

echo.
pause
