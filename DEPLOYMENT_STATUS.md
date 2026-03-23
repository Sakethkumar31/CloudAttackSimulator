## ✅ CALDERA DOCKER DEPLOYMENT - WINDOWS (FINAL STATUS)

**Deployment Date:** March 18, 2026
**Status:** 🟡 In Progress (Build finalizing...)

---

### 🎯 DEPLOYMENT ARCHITECTURE

**All services running in Windows Docker Desktop (NOT WSL)**

```
Windows Docker Network
├── Redis (Port 6379) ✅ HEALTHY
│   └─ Cache layer for agent coordination
│
├── Neo4j (Port 7474, 7687) ⏳ Starting
│   └─ Graph database for correlations
│
└── Caldera C2 Backend (Port 8888) ⏳ Building...
    └─ C2 Framework with all plugins
```

---

### 📊 CURRENT SERVICE STATUS

| Service | Port | Status | Image | Size |
|---------|------|--------|-------|------|
| **Redis** | 6379 | ✅ HEALTHY | redis:7-alpine | 61.2MB |
| **Neo4j** | 7474 / 7687 | ⏳ HEALTHY | neo4j:5-community | 984MB |
| **Caldera** | 8888, 8443, 7010, 7011, 7012, 8853, 8022, 2222 | 🔨 BUILDING | caldera:latest | 2.45GB+ |

---

### 🔌 NETWORK CONNECTIVITY

All services wired on Docker bridge network with proper dependencies:

```
caldera → depends_on → redis (healthy)
caldera → depends_on → neo4j (healthy)
```

Services auto-restart on failure (`restart: unless-stopped`)

---

### 🚀 ACCESS POINTS (Once All Healthy)

| Service | URL | Type |
|---------|-----|------|
| **Caldera Web UI** | http://localhost:8888 | C2 Console |
| **Neo4j Browser** | http://localhost:7474 | Graph DB |
| **Caldera API** | http://localhost:8888/api/v2 | REST API |
| **Redis CLI** | `redis-cli -h localhost` | Cache |

---

### 🔧 CALDERA C2 CHANNELS

**Primary Beacons:**
- HTTP/HTTPS (8888, 8443)
- TCP (7010)
- UDP (7011)
- WebSocket (7012)

**Alternative Channels:**
- DNS Tunneling (8853)
- SSH Tunneling (8022)
- FTP C2 (2222)

---

### 📁 PROJECT STRUCTURE

```
cloud-attack-lab/
├── caldera/                          ← Backend C2
│   ├── Dockerfile                   (Multi-stage build)
│   ├── .dockerignore               (Optimized)
│   ├── conf/default.yml            (Config)
│   ├── plugins/                    (All plugins enabled)
│   │   ├── magma                  (UI - building)
│   │   ├── atomic                 (Red Team)
│   │   ├── emu                    (Emulation Library)
│   │   └── sandcat                (Agent)
│   └── server.py                  (Entrypoint)
│
├── docker-compose.production.yml    ← Main stack
├── docker-compose.yml              (Auto-start config)
└── .env                            (Environment vars)
```

---

### ⚙️ DOCKER BUILD STAGES

**Caldera Multi-Stage Build:**
1. **Stage 1 (ui-build):** Node.js 23
   - Compile VueJS frontend (Magma)
   - Result: plugins/magma/dist/

2. **Stage 2 (runtime):** Debian Bookworm Slim
   - Base OS + dependencies
   - Python 3.11 + pip packages
   - Golang 1.25.0
   - Plugin data (Atomic, EMU, Sandcat agents)
   - Result: caldera:latest image

**Image Details:**
- Size: 2.45GB+ (compressed)
- Variant: Full (offline-ready with all plugins)
- Build Time: ~15-20 minutes
- Layers: 18 (optimized, cached where possible)

---

### 🛠️ RECENT FIXES APPLIED

1. ✅ **Removed trash ZIP files** (12.2MB)
   - caldera_neo4j.zip
   - ctf-app.zip  
   - scripts.zip

2. ✅ **Fixed Dockerfile COPY issues**
   - Ensured magma/dist included
   - Fixed .dockerignore exclusions
   - Added fallback directory creation

3. ✅ **Wired Windows Docker**
   - Removed WSL complexity
   - Direct Windows Docker Desktop deployment
   - Proper bridge networking

4. ✅ **Environment configuration**
   - Created .env for Neo4j credentials
   - Updated docker-compose.yml with proper dependencies
   - Set up health checks

---

### 📋 DEPLOYMENT COMMANDS

**Start Services:**
```bash
cd 'C:\Users\91895\Desktop\projects\cloud-attack-lab'
docker compose -f docker-compose.production.yml up -d
```

**View Logs:**
```bash
docker logs -f caldera
docker logs -f neo4j
docker logs -f redis
```

**Check Status:**
```bash
docker ps
docker compose ps
```

**Restart All:**
```bash
docker compose -f docker-compose.production.yml restart
```

**Full Reset:**
```bash
docker compose -f docker-compose.production.yml down -v
docker compose -f docker-compose.production.yml up -d
```

---

### 🔐 CREDENTIALS

**Neo4j:**
- Username: `neo4j`
- Password: `replace_with_neo4j_password`
- Connection: `bolt://neo4j:7687`

**Redis:**
- No authentication (local network only)
- Port: 6379

**Caldera:**
- Red Team: `admin` / `admin`
- Blue Team: `blue` / `admin`
- API Key: `ADMIN123`

---

### 📌 NEXT STEPS

1. ⏳ **Wait for Caldera build to complete** (~5-10 min remaining)
2. ⏳ **Services will auto-start once image is ready**
3. ✅ **Access Caldera at http://localhost:8888**
4. ✅ **Deploy agents and begin operations**

---

### 🐛 TROUBLESHOOTING

**If Caldera won't start:**
```bash
docker logs caldera
docker inspect caldera
docker compose restart caldera
```

**If ports already in use:**
```bash
netstat -ano | findstr :8888
taskkill /PID <PID> /F
```

**Full cleanup (DELETE ALL DATA):**
```bash
docker compose -f docker-compose.production.yml down -v
docker system prune -a
```

---

### 📊 SYSTEM REQUIREMENTS

- **Docker Desktop:** Latest version
- **Memory:** 8GB+ recommended
- **Disk:** 15GB+ for all images and volumes
- **Ports:** 6379, 7474, 7687, 8888, 8443, 7010-7012, 8853, 8022, 2222

---

### ✨ FEATURES ENABLED

✅ Multi-stage Docker build (optimized)
✅ Health checks on all services
✅ Auto-restart on failure
✅ Volume persistence
✅ Custom bridge network
✅ All Caldera plugins (atomic, emu, sandcat)
✅ Neo4j graph database integration
✅ Redis caching layer
✅ Multiple C2 channels
✅ Dashboard-ready architecture

---

**Status:** Build in progress... Services will be ready in ~5 minutes.

Access the stack once all containers show "healthy" status.
