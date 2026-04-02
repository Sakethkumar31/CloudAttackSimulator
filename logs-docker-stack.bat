@echo off
REM View logs for all services or specific service
REM Usage: logs-docker-stack.bat [service_name]
REM Example: logs-docker-stack.bat caldera

cd /d "C:\Users\91895\Desktop\projects\cloud-attack-lab"
set "COMPOSE_FILE=docker-compose.yml"

if "%1"=="" (
    echo [*] Showing logs for all services...
    docker compose -f "%COMPOSE_FILE%" logs -f
) else (
    echo [*] Showing logs for %1...
    docker compose -f "%COMPOSE_FILE%" logs -f %1
)

pause
