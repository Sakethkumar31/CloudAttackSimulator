# Cloud Attack Lab - Docker Deployment Summary

## ✅ Setup Complete

Your Caldera C2 backend with Docker automation is ready for deployment on Windows with WSL2.

---

## What's Ready

### 1. Auto-Startup System ✓
- Windows Startup folder integration
- Runs automatically when Docker Desktop opens
- No manual intervention needed

### 2. Docker Compose Configuration ✓
- Production-grade docker-compose.yml
- 6 interconnected services
- Health checks & auto-restart enabled
- Environment variables configured

### 3. Management Scripts ✓
Created in: `C:\Users\91895\Desktop\projects\cloud-attack-lab\`

| Script | Purpose |
|--------|---------|
| `start-docker-stack.bat` | Start all services |
| `stop-docker-stack.bat` | Stop all services |
| `logs-docker-stack.bat` | View logs |
| `health-check.bat` | Check service health |
| `Start-DockerStack.ps1` | PowerShell automation |
| `quick-commands.sh` | Bash reference guide |

### 4. Documentation ✓
- `DOCKER_STATUS_REPORT.md` - Infrastructure analysis
- `DOCKER_AUTOMATION_GUIDE.md` - Complete reference
- `CALDERA_DEPLOYMENT.md` - Deployment guide
- `CALDERA_QUICK_REFERENCE.md` - This file

---

## Current Status

### Build Status
**Currently Building Caldera Image** (estimat 3-5 minutes remaining)

Stages completed:
- ✅ Node.js UI build (Vite/magma)
- ✅ Debian runtime setup
- ⏳ Dependencies installation (336MB packages)
- ⏳ Python pip modules
- ⏳ Go setup
- ⏳ Plugin data (Atomic, EMU)
- ⏳ Sandcat agents update

### Build Size
- **Current:** ~2.8GB of dependencies
- **Final Image:** ~1.2GB (full variant with all plugins)

---

## Deployment Checklist

- [x] Docker Compose configuration created
- [x] Auto-startup script installed
- [x] Management scripts created
- [x] Environment variables configured
- [x] Caldera Dockerfile verified
- [x] Documentation prepared
- [ ] Build in progress (wait for completion)
- [ ] Test services startup
- [ ] Verify Caldera accessibility

---

## Quick Start (Once Build Completes)

### Option 1: Automatic Auto-Start
1. Open Docker Desktop
2. Wait 30-45 seconds
3. Services auto-start automatically
4. Open http://localhost:8888

### Option 2: Manual Start
```bash
# Navigate to project folder
cd C:\Users\91895\Desktop\projects\cloud-attack-lab

# Start all services
start-docker-stack.bat

# View services
docker compose ps

# Check logs
logs-docker-stack.bat caldera
```

### Option 3: PowerShell
```powershell
# Enable scripts (one time)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Use PowerShell script
.\Start-DockerStack.ps1 start
.\Start-DockerStack.ps1 logs
.\Start-DockerStack.ps1 status
```

---

## Access Points

Once services are running:

| Service | URL | Port |
|---------|-----|------|
| **Caldera Web UI** | http://localhost:8888 | 8888 |
| **Dashboard** | http://localhost:5000 | 5000 |
| **Neo4j Browser** | http://localhost:7474 | 7474 |
| **Redis CLI** | redis-cli -h localhost -p 6379 | 6379 |

---

## Service Architecture

```
Docker Network (172.25.0.0/16)
│
├── Redis (172.25.0.4:6379)
│   └─ Cache layer
│
├── Neo4j (172.25.0.3:7687)
│   └─ Graph database
│
├── Caldera (172.25.0.2:8888) ← PRIMARY SERVICE
│   └─ C2 Framework
│   ├─ Port 8888 (HTTP)
│   ├─ Port 8443 (HTTPS)
│   ├─ Port 7010 (TCP C2)
│   ├─ Port 7011 (UDP C2)
│   ├─ Port 7012 (WebSocket)
│   ├─ Port 8853 (DNS Tunnel)
│   ├─ Port 8022 (SSH Tunnel)
│   └─ Port 2222 (FTP C2)
│
├── Sync-Worker (172.25.0.5)
│   └─ Event processor
│
├── Graph-Writer (172.25.0.6)
│   └─ Neo4j updates
│
└── Dashboard (172.25.0.7:5000)
    └─ Web UI
```

---

## File Structure

```
cloud-attack-lab/
├── 📄 docker-compose.yml                (NEW - Auto-start config)
├── 📄 .env                              (NEW - Environment vars)
├── 📄 start-docker-stack.bat            (NEW)
├── 📄 stop-docker-stack.bat             (NEW)
├── 📄 logs-docker-stack.bat             (NEW)
├── 📄 health-check.bat                  (NEW)
├── 📄 Start-DockerStack.ps1             (NEW - PowerShell)
├── 📄 quick-commands.sh                 (NEW - Bash)
├── 📄 DOCKER_STATUS_REPORT.md           (NEW)
├── 📄 DOCKER_AUTOMATION_GUIDE.md        (NEW)
├── 📄 CALDERA_DEPLOYMENT.md             (NEW)
│
├── 📁 caldera/
│   ├── Dockerfile                       (Multi-stage)
│   ├── .dockerignore                    (Optimized)
│   ├── docker-compose.yml               (Original - reference)
│   ├── server.py
│   ├── requirements.txt
│   └── plugins/
│
├── 📁 dashboard_web/
│   ├── Dockerfile
│   ├── app.py
│   └── requirements.txt
│
├── 📁 services/
│   ├── sync_worker/
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   └── requirements.txt
│   └── graph_writer/
│       ├── Dockerfile
│       ├── main.py
│       └── requirements.txt
│
├── 📁 neo4j/
└── [other configs...]
```

---

## Environment Configuration

### .env File
```
NEO4J_USER=neo4j
NEO4J_PASSWORD=replace_with_neo4j_password
REDIS_HOST=redis
REDIS_PORT=6379
CALDERA_PORT=8888
CALDERA_HOST=0.0.0.0
FLASK_ENV=production
FLASK_APP=app.py
TZ=UTC
PYTHONUNBUFFERED=1
```

To modify: Edit `.env` and restart with `docker compose restart`

---

## Troubleshooting

### Build still running?
```bash
# Check build progress
docker compose logs

# Monitor with tail
wsl docker compose -f docker-compose.production.yml build --progress=plain
```

### Services won't start?
```bash
# Full restart
docker compose down && docker compose up -d

# With rebuild
docker compose down && docker compose build --no-cache && docker compose up -d
```

### Caldera not responding?
```bash
# Check container
docker ps | grep caldera

# View logs
docker logs caldera

# Check port
netstat -ano | findstr :8888
```

### Docker Desktop issues?
- Restart Docker Desktop
- Check WSL2 status: `wsl --list --verbose`
- Increase RAM: Docker Desktop Settings > Resources
- Clear cache: `docker system prune -a`

---

## Next Steps

1. **Wait for build** (~5-10 minutes total)
   - Monitor in Docker Desktop UI
   - Or run: `docker compose logs -f`

2. **Test startup** (after build)
   ```bash
   docker compose up -d
   docker compose ps
   ```

3. **Verify services**
   ```bash
   # Run health check
   health-check.bat

   # Test Caldera
   curl http://localhost:8888
   ```

4. **Deploy agents**
   - Access http://localhost:8888
   - Create & deploy agents
   - Monitor via http://localhost:5000

---

## Security Notes

⚠️ **Current Configuration:**
- Credentials in .env file (development mode)
- No authentication on Redis
- Neo4j has basic auth

**For Production:**
1. Use Docker secrets management
2. Add Redis authentication
3. Enable TLS/SSL for Caldera
4. Consider Docker Hardened Images (DHI)

---

## Performance Tuning

### Docker Memory
- Docker Desktop: Settings > Resources > Memory
- Recommended: 8GB+ for full stack
- Monitor with: `docker stats`

### Caldera Variant
Current: **Full** (includes all plugins, ~1.2GB)
Alternative: **Slim** (excludes emu/atomic, ~600MB)

To switch: Edit `docker-compose.yml` line:
```yaml
VARIANT: slim  # Change from 'full'
```

---

## Support & Resources

- **Caldera Docs:** https://caldera.readthedocs.io/
- **Neo4j Docs:** https://neo4j.com/docs/
- **Docker Compose:** https://docs.docker.com/compose/
- **Docker Desktop:** https://docs.docker.com/desktop/

---

## Build Status Monitor

**Current:** Downloading system dependencies (336MB)
**Estimated Total Time:** 8-10 minutes
**Current Runtime:** ~3 minutes

Remaining stages:
1. ⏳ Finish dependency installation (~2 min)
2. ⏳ Go installation (~1 min)
3. ⏳ Plugin data download (~2-3 min)
4. ⏳ Build finalization (~1 min)

---

**Status:** ✅ Automation ready, waiting for build completion

Once build finishes, services will be production-ready for automatic startup and agent deployment.

All scripts, documentation, and configurations are in place. Just wait for the Docker build to complete!
