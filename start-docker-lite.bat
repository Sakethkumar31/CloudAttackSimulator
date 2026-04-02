@echo off
setlocal enabledelayedexpansion

cd /d "C:\Users\91895\Desktop\projects\cloud-attack-lab"
set "COMPOSE_FILE=docker-compose.yml"
set "DOCKER_WAIT_SECONDS=120"
set /a WAITED=0

echo.
echo ========================================
echo Cloud Attack Lab - Lite Startup
echo ========================================
echo.
echo Starts only Redis, Neo4j, and Caldera to keep the machine responsive.
echo Run the full stack later only when you need the dashboard/workers.
echo.

echo [*] Waiting for Docker daemon to be ready...
:wait_for_docker
docker info >nul 2>&1
if %errorlevel%==0 goto docker_ready

if !WAITED! GEQ %DOCKER_WAIT_SECONDS% (
    echo [!] Docker daemon did not become ready within %DOCKER_WAIT_SECONDS% seconds.
    exit /b 1
)

timeout /t 5 /nobreak >nul
set /a WAITED+=5
goto wait_for_docker

:docker_ready
echo [*] Starting lite services...
docker compose -f "%COMPOSE_FILE%" up -d redis neo4j caldera
if errorlevel 1 (
    echo [!] Docker Compose failed to start the lite stack.
    exit /b 1
)

echo.
docker compose -f "%COMPOSE_FILE%" ps
echo.
echo Caldera: http://localhost:8888
echo Neo4j:   http://localhost:7474
echo Redis:   localhost:6379
echo.
