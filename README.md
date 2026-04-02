# Cloud Attack Lab

Security Operations Center (SOC) dashboard that visualizes attack paths from CALDERA (MITRE adversarial emulation framework) in real-time.

## Architecture

```
CALDERA (localhost:8888) -> sync_worker -> Redis -> graph_writer -> Neo4j -> dashboard_web
```

- **sync_worker**: Polls CALDERA API every 5s, publishes events to Redis stream
- **graph_writer**: Consumes Redis stream, builds attack graph in Neo4j
- **dashboard_web**: Flask app with Cytoscape visualization, risk scoring, MITRE mapping, AI tutor

## Repo Layout

```
cloud-attack-lab/
  dashboard_web/       # Flask dashboard (frontend)
  services/            # Backend workers
    graph_writer/      # Redis -> Neo4j graph writer
    sync_worker/       # CALDERA API -> Redis sync service
  infra/               # Docker Compose configuration
    docker-compose.phase2.yml   # Main compose file
    .env.phase2.example         # Environment template
    caldera.local.yml.example   # CALDERA config template
  caldera/             # MITRE CALDERA framework (submodule)
```

## Quick Start (Full Stack with Docker)

### Prerequisites

- Docker Desktop running (with WSL2 backend on Windows)
- Ubuntu-22.04 WSL distribution with Docker Engine installed
- CALDERA running on `http://localhost:8888` (or in Docker)

### 1) Setup environment files

```powershell
# From repo root (PowerShell)
Copy-Item infra\.env.phase2.example infra\.env.phase2
Copy-Item infra\caldera.local.yml.example infra\caldera.local.yml
```

Edit `infra\.env.phase2` and set:
- `CALDERA_API_KEY` - from your CALDERA instance
- `NEO4J_PASSWORD` - your Neo4j password
- `DASHBOARD_PASS` - dashboard login password

### 2) Start the stack

**Windows (using WSL):**
```powershell
.\run_lab.bat
```

**Manual (from WSL):**
```bash
cd /home/saketh/cloud-attack-lab
docker compose --env-file infra/.env.phase2 -f infra/docker-compose.phase2.yml up -d
```

### 3) Access services

- **Dashboard**: http://localhost:5000/login
- **CALDERA**: http://localhost:8888
- **Neo4j Browser**: http://localhost:7474

### 4) Stop the stack

```powershell
.\run_lab.bat stop
# Or manually:
docker compose --env-file infra/.env.phase2 -f infra/docker-compose.phase2.yml down
```

### 5) Clean restart (remove all containers and images)

```bash
# Run from WSL
cd /home/saketh/cloud-attack-lab
docker compose --env-file infra/.env.phase2 -f infra/docker-compose.phase2.yml down --rmi all --volumes --remove-orphans
docker compose --env-file infra/.env.phase2 -f infra/docker-compose.phase2.yml up -d --build
```

---

## Dashboard Only (No Docker)

### 1) Create Python environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
cd dashboard_web
pip install -r requirements.txt
```

### 2) Set environment variables

```powershell
$env:NEO4J_URI="neo4j://localhost:7687"
$env:NEO4J_USER="neo4j"
$env:NEO4J_PASSWORD="your_password"
$env:DASHBOARD_USER="socadmin"
$env:DASHBOARD_PASS="your_password"
```

### 3) Run dashboard

```powershell
python app.py
# Or use the launcher:
.\run_dashboard_web.bat
```

Access: http://127.0.0.1:5000/login

---

## Running CALDERA on Localhost (Recommended for WSL)

The compose file is configured to connect to CALDERA running on your host machine at `http://localhost:8888`.

### Start CALDERA manually (in WSL):

```bash
cd /home/saketh/cloud-attack-lab/caldera
python3 caldera.py --config /path/to/caldera.local.yml
```

Or run CALDERA in Docker by uncommenting the `caldera` service in `docker-compose.phase2.yml`.

---

## Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `CALDERA_URL` | CALDERA API endpoint | `http://host.docker.internal:8888` |
| `CALDERA_API_KEY` | CALDERA API key | (required) |
| `NEO4J_URI` | Neo4j connection URL | `neo4j://neo4j:7687` |
| `NEO4J_USER` | Neo4j username | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j password | (required) |
| `DASHBOARD_USER` | Dashboard login username | `socadmin` |
| `DASHBOARD_PASS` | Dashboard login password | (required) |
| `GEMINI_API_KEY` | Gemini API key (for AI tutor) | (optional) |
| `GEMINI_MODEL` | Gemini model name | `gemini-2.0-flash` |

---

## Features

- **Real-time attack graph visualization** using Cytoscape.js
- **Risk scoring** (LOW -> CRITICAL, 0-100 scale)
- **MITRE ATT&CK technique mapping**
- **Attack path reconstruction**
- **AI tutor** (Google Gemini integration)
- **CTF learning modes** (beginner/intermediate/expert)
- **SOC learning bot** (chat interface)

## Simulation Phases

The main adversary model in this repo follows a safe multi-stage flow that is useful for demos, reports, and screenshots:

1. **WSL execution foothold**
   Command execution from a WSL/Linux operator context becomes visible in the dashboard graph.
2. **Credential or session reuse**
   Valid-account style behavior is simulated to show identity-driven attack expansion.
3. **Multi-system fan-out**
   Lateral movement style activity increases chain depth, target spread, and overall risk.
4. **Collection and controlled egress**
   Safe exfiltration-style indicators show how outbound activity appears in the attack path.

Research/report handoff docs:

- Full friend-ready packet: [docs/FRIEND_PROJECT_HANDOFF.md](/c:/Users/91895/Desktop/projects/cloud-attack-lab/docs/FRIEND_PROJECT_HANDOFF.md)
- Research paper brief: [docs/RESEARCH_PAPER_BRIEF.md](/c:/Users/91895/Desktop/projects/cloud-attack-lab/docs/RESEARCH_PAPER_BRIEF.md)

---

## GitHub Workflow

```powershell
git add .
git commit -m "your change message"
git push origin main
```

---

## Docker Hub Workflow

Use the prebuilt-image path when you want to run the project on another machine without rebuilding from source.

1. Copy `infra/.env.dockerhub.example` to `infra/.env.dockerhub`
2. Fill in your Docker Hub namespace and runtime secrets
3. Log in with `docker login`
4. Push images:

```powershell
.\scripts\push-dockerhub.ps1 -Namespace your-dockerhub-username -PushCaldera
```

5. Pull and run anywhere:

```powershell
docker compose --env-file infra/.env.dockerhub -f docker-compose.hub.yml pull
docker compose --env-file infra/.env.dockerhub -f docker-compose.hub.yml up -d
```

More detail: [docs/DOCKER_HUB_DEPLOYMENT.md](/c:/Users/91895/Desktop/projects/cloud-attack-lab/docs/DOCKER_HUB_DEPLOYMENT.md)

## Reference Notes

- Demo/reviewer evidence summary: [docs/GITHUB_REFERENCE.md](/c:/Users/91895/Desktop/projects/cloud-attack-lab/docs/GITHUB_REFERENCE.md)
- Screenshot-by-screenshot context pack: [docs/SCREENSHOT_CONTEXTS.md](/c:/Users/91895/Desktop/projects/cloud-attack-lab/docs/SCREENSHOT_CONTEXTS.md)

## Screenshot Plan

For a public GitHub visitor, the screenshots should appear in this story order:

1. **Architecture overview**
   Explain the full platform: CALDERA -> `sync_worker` -> Redis -> `graph_writer` -> Neo4j -> Dashboard.
2. **Data pipeline**
   Show the implementation-focused service flow that turns operations into a graph-backed SOC view.
3. **CALDERA source**
   Show the upstream attack-emulation platform that provides agents, operations, and executed links.
4. **SOC dashboard overview**
   Show the analyst landing page with risk, sync health, live operations, and geospatial context.
5. **Attack graph**
   Show the agent-to-fact graph that proves the execution data becomes a visual attack path.
6. **Attack focus**
   Show the path-ranking and triage panel that adds guidance beyond simple graph rendering.
7. **Geospatial map**
   Show mapped agent/attacker context and analyst-console location awareness.
8. **Maze defender simulation**
   Show the response-training mode that converts attack-path ideas into guided mitigation steps.
9. **CTF learner mode**
   Show the question-and-tutor flow used for student practice and onboarding.

Suggested file names and full captions are documented in [docs/SCREENSHOT_CONTEXTS.md](/c:/Users/91895/Desktop/projects/cloud-attack-lab/docs/SCREENSHOT_CONTEXTS.md).

## Media And Copyright

Project screenshots, custom diagrams, and repository-authored explanatory media are copyright the repository owner unless otherwise noted.

Third-party product names, logos, map tiles, and trademarks visible inside screenshots, including CALDERA, Redis, Neo4j, Flask, Leaflet, and OpenStreetMap attribution, remain the property of their respective owners and are shown only to document integration, demonstration, and academic/project presentation.
