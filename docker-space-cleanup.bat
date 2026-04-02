@echo off
setlocal

cd /d "C:\Users\91895\Desktop\projects\cloud-attack-lab"

echo.
echo ========================================
echo Cloud Attack Lab - Docker Space Cleanup
echo ========================================
echo.
echo This cleanup preserves named volumes so Neo4j, Redis, and Caldera data remain intact.
echo.

docker info >nul 2>&1
if errorlevel 1 (
    echo [!] Docker daemon is not ready. Open Docker Desktop and rerun this script.
    exit /b 1
)

echo [*] Current Docker disk usage:
docker system df

echo.
set /p CONFIRM=Proceed with cleanup of stopped containers, dangling images, and build cache? [y/N]: 
if /I not "%CONFIRM%"=="Y" (
    echo [*] Cleanup cancelled.
    exit /b 0
)

echo.
echo [*] Removing stopped containers...
docker container prune -f

echo [*] Removing unused images not referenced by containers...
docker image prune -a -f

echo [*] Removing unused build cache...
docker builder prune -af

echo.
echo [*] Docker disk usage after cleanup:
docker system df

echo.
echo [*] Named volumes were preserved.
echo.
pause
