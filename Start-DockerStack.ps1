# Cloud Attack Lab - Docker PowerShell Automation
# Place in: C:\Users\91895\Desktop\projects\cloud-attack-lab\Start-DockerStack.ps1
# Run with: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
#          .\Start-DockerStack.ps1

param(
    [ValidateSet("start", "stop", "restart", "logs", "status", "rebuild")]
    [string]$Action = "start"
)

$ProjectPath = "C:\Users\91895\Desktop\projects\cloud-attack-lab"
Set-Location $ProjectPath

function Start-Stack {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Cloud Attack Lab - Starting Docker Stack" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
    Write-Host "[*] Starting services..." -ForegroundColor Yellow
    docker compose up -d
    
    Write-Host "[*] Waiting for services to stabilize..." -ForegroundColor Yellow
    Start-Sleep -Seconds 15
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Services Status:" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    docker compose ps
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Access Points:" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Caldera Web UI:  http://localhost:8888" -ForegroundColor Green
    Write-Host "Dashboard:       http://localhost:5000" -ForegroundColor Green
    Write-Host "Neo4j Browser:   http://localhost:7474" -ForegroundColor Green
    Write-Host "Redis CLI:       redis-cli -h localhost" -ForegroundColor Green
    Write-Host ""
}

function Stop-Stack {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Cloud Attack Lab - Stopping Services" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
    Write-Host "[*] Stopping containers..." -ForegroundColor Yellow
    docker compose down
    
    Write-Host "[+] Services stopped." -ForegroundColor Green
    Write-Host ""
}

function Restart-Stack {
    Write-Host "[*] Restarting stack..." -ForegroundColor Yellow
    Stop-Stack
    Start-Sleep -Seconds 3
    Start-Stack
}

function Show-Logs {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Cloud Attack Lab - Service Logs" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
    docker compose logs -f
}

function Show-Status {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Cloud Attack Lab - Status" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
    docker compose ps
    
    Write-Host ""
    Write-Host "Service Health:" -ForegroundColor Cyan
    $services = @("caldera", "neo4j", "redis", "dashboard", "sync-worker", "graph-writer")
    
    foreach ($service in $services) {
        $health = docker inspect --format="{{.State.Health.Status}}" $service 2>$null
        if ($health) {
            Write-Host "  $service : $health" -ForegroundColor $(if ($health -eq "healthy") { "Green" } else { "Yellow" })
        }
    }
    Write-Host ""
}

function Rebuild-Stack {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Cloud Attack Lab - Rebuilding Images" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
    Write-Host "[*] Stopping services..." -ForegroundColor Yellow
    docker compose down
    
    Write-Host "[*] Rebuilding all images..." -ForegroundColor Yellow
    docker compose build --no-cache
    
    Write-Host "[*] Starting services..." -ForegroundColor Yellow
    docker compose up -d
    
    Write-Host "[+] Rebuild complete." -ForegroundColor Green
    Write-Host ""
}

switch ($Action) {
    "start" { Start-Stack }
    "stop" { Stop-Stack }
    "restart" { Restart-Stack }
    "logs" { Show-Logs }
    "status" { Show-Status }
    "rebuild" { Rebuild-Stack }
}
