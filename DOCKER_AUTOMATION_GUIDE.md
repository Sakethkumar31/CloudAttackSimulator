# Cloud Attack Lab - Docker Automation Setup

## Quick Start

### Option 1: Auto-Start on Windows Boot
The stack will automatically start when Docker Desktop opens.

**Setup:**
1. Run `start-docker-stack.bat` once to verify
2. Auto-startup script is already installed at:
   - `C:\Users\91895\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\start-cloud-attack-lab.vbs`

### Option 2: Manual Start
Double-click one of these scripts from the project folder:

- **start-docker-stack.bat** - Start all services
- **stop-docker-stack.bat** - Stop all services
- **logs-docker-stack.bat** - View live logs
- **health-check.bat** - Check service health

---

## Access Points (Once Running)

| Service | URL | Port |
|---------|-----|------|
| **Caldera (C2 Backend)** | http://localhost:8888 | 8888 |
| **Dashboard UI** | http://localhost:5000 | 5000 |
| **Neo4j Browser** | http://localhost:7474 | 7474 |
| **Redis** | localhost:6379 | 6379 |
| **Caldera HTTPS** | https://localhost:8443 | 8443 |
| **Caldera TCP C2** | localhost:7010 | 7010 |
| **Caldera UDP C2** | localhost:7011 | 7011/udp |
| **Caldera WebSocket** | localhost:7012 | 7012 |
| **DNS Tunnel** | localhost:8853 | 8853 |
| **SSH Tunnel** | localhost:8022 | 8022 |
| **FTP Channel** | localhost:2222 | 2222 |

---

## Services Architecture

```
attack-lab (172.25.0.0/16)
├── Neo4j Database (172.25.0.3:7687)
├── Redis Cache (172.25.0.4:6379)
├── Caldera Backend (172.25.0.2:8888) ← MAIN C2 FRAMEWORK
├── Sync Worker (172.25.0.5) - Event processor
├── Graph Writer (172.25.0.6) - Neo4j updates
└── Dashboard (172.25.0.7:5000) - Web UI
```

---

## Docker Compose Files

- **docker-compose.yml** - Main compose file (auto-starts services with `restart: unless-stopped`)
- **docker-compose.production.yml** - Original production config

---

## Environment Variables

Stored in `.env` file:
```
NEO4J_USER=neo4j
NEO4J_PASSWORD=replace_with_neo4j_password
REDIS_HOST=redis
REDIS_PORT=6379
CALDERA_PORT=8888
CALDERA_HOST=0.0.0.0
TZ=UTC
```

---

## Common Commands

### View all services
```bash
docker compose ps
```

### View Caldera logs
```bash
docker compose logs -f caldera
```

### Restart Caldera
```bash
docker compose restart caldera
```

### Stop all services
```bash
docker compose down
```

### Stop and remove all data
```bash
docker compose down -v
```

### Rebuild Caldera image
```bash
docker compose build --no-cache caldera
```

### Full restart
```bash
docker compose down && docker compose up -d
```

---

## Caldera Backend Information

**Location (WSL):** `/mnt/c/Users/91895/Desktop/projects/cloud-attack-lab/caldera`

**Exposed Ports:**
- 8888 - HTTP Web UI & Agent beacons
- 8443 - HTTPS (requires SSL plugin)
- 7010 - TCP contact port
- 7011/udp - UDP contact port
- 7012 - WebSocket contact port
- 8853 - DNS tunneling
- 8022 - SSH tunneling
- 2222 - FTP C2 channel

**Volumes:**
- `caldera_data` - Agent data, facts, abilities
- `caldera_plugins` - Plugin extensions

**Dependencies:**
- Redis (required for startup)
- Optional: Neo4j (for graph integration)

---

## Health Checks

Each service has automatic health checks:
- Neo4j: HTTP curl to 7474
- Redis: redis-cli ping
- Caldera: HTTP curl to 8888 (30s startup delay)
- Dashboard: HTTP curl to 5000 (20s startup delay)
- Workers: Redis ping test

Check status with `health-check.bat`

---

## Troubleshooting

### Caldera not starting
```bash
docker compose logs -f caldera
docker inspect caldera
```

### Port already in use
Find the process using the port:
```bash
netstat -ano | findstr :8888
```

Kill the process:
```bash
taskkill /PID <PID> /F
```

### Services not connecting
```bash
docker network ls
docker network inspect cloud-attack-lab_attack-lab
```

### Rebuild everything from scratch
```bash
docker compose down -v
docker compose build --no-cache
docker compose up -d
```

---

## Notes

- All services restart automatically if they crash (`restart: unless-stopped`)
- Volumes persist data between container restarts
- Network isolation via custom bridge network (172.25.0.0/16)
- Production-ready with health checks and dependencies
- Auto-startup configured via Windows Startup folder

---

## Next Steps

1. Open Docker Desktop
2. Run `start-docker-stack.bat` (or wait for auto-startup)
3. Wait 30-45 seconds for services to stabilize
4. Open http://localhost:8888 to access Caldera
5. Open http://localhost:5000 to access Dashboard
6. Monitor logs with `logs-docker-stack.bat caldera`

Let me know if you need any adjustments!
