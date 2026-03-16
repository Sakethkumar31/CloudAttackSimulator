# TODO

## Completed
- Fixed secrets exposure in `.env.phase2` and `caldera.local.yml`
- Updated `.gitignore` to exclude sensitive config files
- Created `.example` templates for all config files
- Updated README with accurate file structure and instructions
- Fixed docker-compose to work with CALDERA on localhost
- Updated run_lab.bat with configurable WSL path
- Cleaned up stray artifact files

## Running the Stack

### Clean restart (removes all containers and images):
```bash
# From WSL terminal
cd /home/saketh/cloud-attack-lab
docker compose --env-file infra/.env.phase2 -f infra/docker-compose.phase2.yml down --rmi all --volumes
docker compose --env-file infra/.env.phase2 -f infra/docker-compose.phase2.yml up -d --build
```

### Or use the helper script:
```bash
./infra/restart_clean.sh
```

### From Windows (PowerShell):
```powershell
wsl -d Ubuntu-22.04 -- bash -lc "cd /home/saketh/cloud-attack-lab && docker compose --env-file infra/.env.phase2 -f infra/docker-compose.phase2.yml down --rmi all --volumes && docker compose --env-file infra/.env.phase2 -f infra/docker-compose.phase2.yml up -d --build"
```

## Services
- Neo4j: http://localhost:7474 (bolt: 7687)
- CALDERA: http://localhost:8888
- Dashboard: http://localhost:5000
- Redis: localhost:6379

## Notes
- CALDERA runs on localhost (not in Docker) - sync_worker connects via host.docker.internal
- Ensure CALDERA is running on port 8888 before starting the stack
- Default credentials should be changed in production
