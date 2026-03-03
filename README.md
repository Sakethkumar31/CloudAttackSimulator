# CloudAttackPathSimulator

Cloud Attack Path Simulator with:
- Frontend: Flask dashboard in `dashboard_web/`
- Backend workers: `services/sync_worker` and `services/graph_writer`
- Infra: Docker Compose in `infra/`

## Repo Layout

```text
cloud-attack-lab/
  dashboard_web/      # web frontend (Flask templates + API endpoints)
  services/           # backend workers
  infra/              # docker compose for Redis + workers
  docs/               # run guides and notes
```

## Quick Start (Windows PowerShell)

### 1) Clone and enter project

```powershell
git clone https://github.com/Sakethkumar31/CloudAttackPathSimulator.git
cd CloudAttackPathSimulator
```

### 2) Create Python environment and install dashboard deps

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install flask neo4j requests
```

### 3) Set required env vars

```powershell
$env:NEO4J_URI="neo4j://localhost:7687"
$env:NEO4J_USER="neo4j"
$env:NEO4J_PASSWORD="your_password"
```

Optional:

```powershell
$env:OPENAI_API_KEY="your_key"
$env:FLASK_SECRET_KEY="change_me"
```

### 4) Run frontend (dashboard)

```powershell
cd dashboard_web
python app.py
```

Open: `http://127.0.0.1:5000/login`

### 5) Run backend workers (optional but recommended)

From repo root:

```powershell
Copy-Item infra/.env.phase2.example infra/.env.phase2
```

Edit `infra/.env.phase2` values (at least `CALDERA_API_KEY`, `NEO4J_PASSWORD`), then:

```powershell
cd infra
docker compose --env-file .env.phase2 -f docker-compose.phase2.yml up -d
docker compose -f docker-compose.phase2.yml ps
```

To stop:

```powershell
docker compose --env-file .env.phase2 -f docker-compose.phase2.yml down
```

## GitHub Workflow

Use this every time after changes:

```powershell
git add .
git commit -m "your change message"
git push origin main
```
