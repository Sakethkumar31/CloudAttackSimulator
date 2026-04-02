@echo off
REM Auto-start Cloud Attack Lab Docker Stack
REM This script starts the full stack in stages to reduce startup load

setlocal enabledelayedexpansion

cd /d "C:\Users\91895\Desktop\projects\cloud-attack-lab"
set "COMPOSE_FILE=docker-compose.yml"
set "DOCKER_WAIT_SECONDS=120"
set "HEALTH_WAIT_SECONDS=240"
set /a WAITED=0
set "CORE_SERVICES=redis neo4j caldera"
set "EXTENDED_SERVICES=dashboard neo4j-sync graph-writer"

echo.
echo ========================================
echo Cloud Attack Lab - Docker Stack Startup
echo ========================================
echo.

echo [*] Waiting for Docker daemon to be ready...
:wait_for_docker
docker info >nul 2>&1
if %errorlevel%==0 goto docker_ready

if !WAITED! GEQ %DOCKER_WAIT_SECONDS% (
    echo [!] Docker daemon did not become ready within %DOCKER_WAIT_SECONDS% seconds.
    echo [!] Open Docker Desktop, wait for it to finish starting, then rerun this script.
    exit /b 1
)

timeout /t 5 /nobreak >nul
set /a WAITED+=5
goto wait_for_docker

:docker_ready

echo [*] Starting core services first...
docker compose -f "%COMPOSE_FILE%" up -d --remove-orphans %CORE_SERVICES%
if errorlevel 1 (
    echo [!] Docker Compose failed to start the core services.
    exit /b 1
)

echo.
echo [*] Waiting for core services to become healthy...
for %%S in (%CORE_SERVICES%) do (
    call :wait_for_healthy %%S
    if errorlevel 1 exit /b 1
)

echo [*] Starting dashboard and workers...
docker compose -f "%COMPOSE_FILE%" up -d --no-deps %EXTENDED_SERVICES%
if errorlevel 1 (
    echo [!] Docker Compose failed to start the dashboard/worker services.
    exit /b 1
)

echo.
echo [*] Waiting for the full stack to stabilize...
timeout /t 15 /nobreak >nul

echo.
echo ========================================
echo Services Status:
echo ========================================
docker compose -f "%COMPOSE_FILE%" ps

echo.
echo ========================================
echo Access Points:
echo ========================================
echo Caldera Web UI:  http://localhost:8888
echo Dashboard:       http://localhost:5000
echo Neo4j Browser:   http://localhost:7474
echo Redis:           localhost:6379
echo.
exit /b 0

:wait_for_healthy
set "SERVICE=%~1"
set /a SERVICE_WAITED=0

:health_loop
set "STATUS="
for /f "delims=" %%H in ('docker inspect --format "{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}" %SERVICE% 2^>nul') do (
    set "STATUS=%%H"
)

if /I "!STATUS!"=="healthy" (
    echo [*] %SERVICE% is healthy.
    exit /b 0
)

if /I "!STATUS!"=="running" (
    echo [*] %SERVICE% is running without a healthcheck.
    exit /b 0
)

if !SERVICE_WAITED! GEQ %HEALTH_WAIT_SECONDS% (
    echo [!] %SERVICE% did not become healthy within %HEALTH_WAIT_SECONDS% seconds. Current status: !STATUS!
    exit /b 1
)

timeout /t 5 /nobreak >nul
set /a SERVICE_WAITED+=5
goto health_loop
