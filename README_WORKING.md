# Cloud Attack Lab

Technical README for running and understanding the working system. For the visual project walk-through with screenshots, see [README.md](README.md).

## Architecture

```text
CALDERA (localhost:8888) -> sync_worker -> Redis -> graph_writer -> Neo4j -> dashboard_web
```

- **sync_worker**: Polls CALDERA API every 5s, publishes events to Redis stream
- **graph_writer**: Consumes Redis stream, builds attack graph in Neo4j
- **dashboard_web**: Flask app with Cytoscape visualization, risk scoring, MITRE mapping, AI tutor

## Repo Layout

```text
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

## Quick Start (Full Stack With Docker)

### Prerequisites

- Docker Desktop running with WSL2 backend on Windows
- Ubuntu-22.04 WSL distribution with Docker Engine installed
- CALDERA running on `http://localhost:8888` or in Docker

### 1. Setup Environment Files

```powershell
Copy-Item infra\.env.phase2.example infra\.env.phase2
Copy-Item infra\caldera.local.yml.example infra\caldera.local.yml
```

Edit `infra\.env.phase2` and set:

- `CALDERA_API_KEY`
- `NEO4J_PASSWORD`
- `DASHBOARD_PASS`

### 2. Start The Stack

Windows with WSL:

```powershell
.\run_lab.bat
```

Manual from WSL:

```bash
cd /home/saketh/cloud-attack-lab
docker compose --env-file infra/.env.phase2 -f infra/docker-compose.phase2.yml up -d
```

### 3. Access Services

- Dashboard: `http://localhost:5000/login`
- CALDERA: `http://localhost:8888`
- Neo4j Browser: `http://localhost:7474`

### 4. Stop The Stack

```powershell
.\run_lab.bat stop
```

Or manually:

```bash
docker compose --env-file infra/.env.phase2 -f infra/docker-compose.phase2.yml down
```

### 5. Clean Restart

```bash
cd /home/saketh/cloud-attack-lab
docker compose --env-file infra/.env.phase2 -f infra/docker-compose.phase2.yml down --rmi all --volumes --remove-orphans
docker compose --env-file infra/.env.phase2 -f infra/docker-compose.phase2.yml up -d --build
```

## Dashboard Only

### 1. Create Python Environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
cd dashboard_web
pip install -r requirements.txt
```

### 2. Set Environment Variables

```powershell
$env:NEO4J_URI="neo4j://localhost:7687"
$env:NEO4J_USER="neo4j"
$env:NEO4J_PASSWORD="your_password"
$env:DASHBOARD_USER="socadmin"
$env:DASHBOARD_PASS="your_password"
```

### 3. Run Dashboard

```powershell
python app.py
.\run_dashboard_web.bat
```

Access: `http://127.0.0.1:5000/login`

## Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `CALDERA_URL` | CALDERA API endpoint | `http://host.docker.internal:8888` |
| `CALDERA_API_KEY` | CALDERA API key | required |
| `NEO4J_URI` | Neo4j connection URL | `neo4j://neo4j:7687` |
| `NEO4J_USER` | Neo4j username | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j password | required |
| `DASHBOARD_USER` | Dashboard login username | `socadmin` |
| `DASHBOARD_PASS` | Dashboard login password | required |
| `GEMINI_API_KEY` | Gemini API key for AI tutor | optional |
| `GEMINI_MODEL` | Gemini model name | `gemini-2.0-flash` |

## Features

- Real-time attack graph visualization
- Risk scoring from LOW to CRITICAL
- MITRE ATT&CK technique mapping
- Attack path reconstruction
- AI tutor and advisor flows
- Maze defender simulation
- CTF learner mode

## Documentation Views

- Visual project representation: [README.md](README.md)
- Working technical guide: [README_WORKING.md](README_WORKING.md)
- Screenshot context details: [docs/SCREENSHOT_CONTEXTS.md](docs/SCREENSHOT_CONTEXTS.md)

## Reference Notes

- Demo/reviewer evidence summary: [docs/GITHUB_REFERENCE.md](docs/GITHUB_REFERENCE.md)
- Screenshot-by-screenshot context pack: [docs/SCREENSHOT_CONTEXTS.md](docs/SCREENSHOT_CONTEXTS.md)
- Friend handoff document: [docs/FRIEND_PROJECT_HANDOFF.md](docs/FRIEND_PROJECT_HANDOFF.md)
- Research paper brief: [docs/RESEARCH_PAPER_BRIEF.md](docs/RESEARCH_PAPER_BRIEF.md)

## Media And Copyright

Project screenshots, custom diagrams, and repository-authored explanatory media are copyright the repository owner unless otherwise noted.

Third-party product names, logos, map tiles, and trademarks visible inside screenshots, including CALDERA, Redis, Neo4j, Flask, Leaflet, and OpenStreetMap attribution, remain the property of their respective owners and are shown only to document integration, demonstration, and academic/project presentation.
