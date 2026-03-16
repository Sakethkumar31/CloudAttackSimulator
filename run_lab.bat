@echo off
setlocal

REM Change to the directory where this script lives
cd /d "%~dp0"

echo.
echo [cloud-attack-lab] Starting lab stack inside WSL (Ubuntu-22.04)...
echo   - Requires: Docker Engine inside Ubuntu-22.04
echo   - Caldera build context: /home/saketh/cloud-attack-lab/caldera
echo   - Update WSL_PATH in this script if your repo is in a different location
echo.

REM Use phase 2 environment if present (path inside WSL)
set "COMPOSE_FILE=infra/docker-compose.phase2.yml"
set "ENV_FILE=infra/.env.phase2"

if not exist "%COMPOSE_FILE:\=/%" (
    echo [cloud-attack-lab] ERROR: %COMPOSE_FILE% not found in repo.
    goto :eof
)

REM Set your WSL path here - update if your repo is in a different location
set "WSL_PATH=/home/saketh/cloud-attack-lab"

echo Launching docker compose via WSL...
wsl -d Ubuntu-22.04 -- bash -lc "cd '%WSL_PATH%' && if [ -f '%ENV_FILE%' ]; then docker compose --env-file '%ENV_FILE%' -f '%COMPOSE_FILE%' up -d; else docker compose -f '%COMPOSE_FILE%' up -d; fi"

if errorlevel 1 (
    echo.
    echo [cloud-attack-lab] Docker compose failed inside WSL.
    echo - Ensure Ubuntu-22.04 has Docker installed and the daemon is running.
    echo - From WSL: sudo service docker start   (or your distro-specific command)
    echo - Then re-run: run_lab.bat
) else (
    echo.
    echo [cloud-attack-lab] Lab stack is starting in the background.
    echo   - Neo4j      : http://localhost:7474
    echo   - Caldera UI : http://localhost:8888
    echo   - Dashboard  : http://localhost:5000
)

endlocal

