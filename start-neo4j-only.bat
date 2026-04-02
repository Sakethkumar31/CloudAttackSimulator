@echo off
setlocal enabledelayedexpansion

cd /d "C:\Users\91895\Desktop\projects\cloud-attack-lab"
set "COMPOSE_FILE=docker-compose.yml"
set "DOCKER_WAIT_SECONDS=180"
set /a WAITED=0

echo.
echo ========================================
echo Cloud Attack Lab - Neo4j Startup
echo ========================================
echo.
echo Starts only Neo4j so it is available with minimal load.
echo.

echo [*] Waiting for Docker engine...
:wait_for_docker
docker info >nul 2>&1
if %errorlevel%==0 goto docker_ready

if !WAITED! GEQ %DOCKER_WAIT_SECONDS% (
    echo [!] Docker engine did not become ready within %DOCKER_WAIT_SECONDS% seconds.
    exit /b 1
)

timeout /t 5 /nobreak >nul
set /a WAITED+=5
goto wait_for_docker

:docker_ready
echo [*] Starting Neo4j...
docker compose -f "%COMPOSE_FILE%" up -d neo4j
if errorlevel 1 (
    echo [!] Failed to start Neo4j.
    exit /b 1
)

echo.
docker compose -f "%COMPOSE_FILE%" ps neo4j
echo.
echo Neo4j Browser: http://localhost:7474
echo Bolt:          bolt://localhost:7687
echo.
