# Phase 2.1 Run Steps

## 1) Prepare environment file

From repo root:

```powershell
Copy-Item infra/.env.phase2.example infra/.env.phase2
```

Edit `infra/.env.phase2` and set:
- `CALDERA_API_KEY`
- `NEO4J_PASSWORD`
- optional `CALDERA_URL` and `NEO4J_URI`

## 2) Start Phase 2.1 services

```powershell
cd infra
docker compose --env-file .env.phase2 -f docker-compose.phase2.yml up -d
```

## 3) Verify containers

```powershell
docker compose -f docker-compose.phase2.yml ps
```

Expected running:
- `caldera_redis`
- `sync_worker`
- `graph_writer`

## 4) Verify logs

```powershell
docker logs -f sync_worker
docker logs -f graph_writer
```

You should see:
- sync worker publishing events
- graph writer consuming and writing to Neo4j

## 5) Check Redis stream and DLQ

```powershell
docker exec -it caldera_redis redis-cli XLEN caldera.links.v1
docker exec -it caldera_redis redis-cli XLEN caldera.links.dlq
```

## 6) Open dashboard

Run your Flask dashboard as usual and open:
- `/login`
- `/` dashboard

Your current dashboard polling (`/api/graph`) will now show near-live updates as graph_writer writes events continuously.

## 7) Stop services

```powershell
cd infra
docker compose --env-file .env.phase2 -f docker-compose.phase2.yml down
```

## Notes
- This is Phase 2.1 only (queue + workers). WebSocket push comes in Phase 2.2.
- Keep polling in dashboard enabled until realtime gateway is added.
