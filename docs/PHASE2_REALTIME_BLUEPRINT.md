# Phase 2 Blueprint: Real-Time SOC Engine (Option B)

## Objective
Upgrade from the current stable polling dashboard to a true real-time SOC platform **without coupling sync logic to Flask request threads**.

This design keeps your current stable stack alive while introducing isolated services.

## Why This Architecture
Your previous instability came from putting everything in one Flask process (HTTP app + scheduler + sync + socket updates).

This blueprint separates concerns:
1. `sync-worker`: pulls CALDERA every 5s
2. `event-bus`: decouples producers and consumers
3. `graph-writer`: persists to Neo4j and builds chains/MITRE links
4. `api-web`: serves dashboard/auth/query APIs
5. `realtime-gateway`: pushes live UI updates over WebSocket

## Target Topology

```text
CALDERA API
    |
    v (poll every 5s)
[ sync-worker ] -- normalized events --> [ Redis Streams ] --> [ graph-writer ] --> Neo4j
                                                        \-> [ realtime-gateway ] -> WebSocket clients

Dashboard Browser <-- REST/HTML -- [ api-web ] -- read queries --> Neo4j
Dashboard Browser <-- WS updates -- [ realtime-gateway ]
```

## Service Responsibilities

### 1) sync-worker
- Poll `/api/v2/operations` from CALDERA every 5 seconds.
- Extract `chain` links with `status == 0` (executed).
- Normalize each link into one event message.
- Publish to Redis Stream `caldera.links.v1`.
- Never writes directly to Flask session/UI.

### 2) graph-writer
- Consumer group on Redis Stream (`writers`).
- Idempotent write to Neo4j:
  - `MERGE Agent`
  - `MERGE Fact`
  - `MERGE (Agent)-[:EXECUTED]->(Fact)`
  - `MERGE Technique/Tactic` + `(:Fact)-[:USES]->(:Technique)`
- Rebuild `NEXT` edges per agent incrementally.
- Publish lightweight change notification (`graph.updated`) to Redis pubsub.

### 3) api-web (Flask)
- Keep your current login/session and dashboard pages.
- Query APIs only (no background sync loop).
- Endpoints:
  - `GET /api/graph`
  - `GET /api/targets`
  - `GET /api/agent/<id>/timeline`
  - `GET /api/risk`

### 4) realtime-gateway
- WebSocket server (separate process; FastAPI/Uvicorn recommended).
- Subscribes to `graph.updated` events.
- Broadcasts update payload to connected dashboard clients.
- Dashboard triggers partial refresh (`/api/graph?agent=...&target=...`) on message.

## Event Contracts

### A) Stream Event: `caldera.links.v1`
```json
{
  "event_id": "sha256(paw+ability_id+finish)",
  "event_time": "2026-02-26T16:41:19Z",
  "source": "caldera",
  "operation_id": "<op_id>",
  "agent": {
    "paw": "abc123",
    "host": "ubuntu-host",
    "platform": "linux",
    "group": "red"
  },
  "fact": {
    "fact_id": "<stable_fact_id>",
    "ability_id": "<ability_id>",
    "command": "whoami",
    "status": 0,
    "timestamp": "<finish>",
    "target": "target-1"
  },
  "mitre": {
    "technique_id": "T1059",
    "technique_name": "Command and Scripting Interpreter",
    "tactic": "execution"
  }
}
```

### B) PubSub Update: `graph.updated`
```json
{
  "type": "graph.updated",
  "agent_id": "abc123",
  "target": "target-1",
  "changed_at": "2026-02-26T16:41:20Z"
}
```

## Neo4j Model (Phase 2)

Nodes:
- `(:Agent {agent_id, host, platform, group, trusted})`
- `(:Fact {fact_id, ability_id, command, timestamp, status, target})`
- `(:Technique {technique_id, name})`
- `(:Tactic {name})`
- `(:Target {target_id, name})` (optional but recommended)

Relationships:
- `(Agent)-[:EXECUTED]->(Fact)`
- `(Fact)-[:NEXT]->(Fact)`
- `(Fact)-[:USES]->(Technique)`
- `(Technique)-[:PART_OF]->(Tactic)`
- `(Fact)-[:AGAINST]->(Target)` (optional)

Required constraints:
- `Agent.agent_id` unique
- `Fact.fact_id` unique
- `Technique.technique_id` unique
- `Tactic.name` unique
- Optional `Target.target_id` unique

## Reliability Rules (Non-Negotiable)

1. Idempotency
- `event_id` and `fact_id` must be deterministic.
- Consumer can safely retry the same event.

2. At-least-once processing
- Acknowledge stream message only after Neo4j commit.

3. Dead-letter handling
- On repeated failure, move message to `caldera.links.dlq`.

4. Backpressure visibility
- Track stream lag and consumer pending count.

5. Health checks
- Each service exposes `/health`.

## Security

1. Move all secrets from source files to environment variables:
- CALDERA URL/API key
- Neo4j URI/user/password
- Flask secret key
- Redis credentials

2. Keep login/session in `api-web` only.

3. For production, terminate TLS at reverse proxy (Nginx/Caddy).

## Rollout Plan (Safe Incremental)

### Phase 2.1 (No UI break)
- Introduce Redis + sync-worker + graph-writer.
- Keep current dashboard polling `/api/graph` every 5s.
- Confirm data parity with old manual sync.

### Phase 2.2 (Real-time push)
- Add realtime-gateway and browser WebSocket client.
- WebSocket message triggers selective API fetch.
- Keep existing polling as fallback toggle.

### Phase 2.3 (Advanced SOC panels)
- Per-target risk scoring panel
- MITRE heatmap endpoint/UI
- Attack progression bar from `NEXT` chain depth
- Alert feed panel sourced from stream events

### Phase 2.4 (AI assistant integration)
- Add `assistant-api` service (separate from Flask)
- Read-only query access to Neo4j + context docs
- Endpoints:
  - `POST /assistant/risk-analysis`
  - `POST /assistant/attack-path`
  - `POST /assistant/defense-suggestions`

## Suggested Repository Layout

```text
cloud-attack-lab/
  dashboard_web/                # existing Flask app (api-web)
  caldera_neo4j/                # graph writer logic (refactorable)
  services/
    sync_worker/
      main.py
      publisher.py
    graph_writer/
      main.py
      consumer.py
      writer.py
    realtime_gateway/
      main.py
      ws_server.py
  infra/
    docker-compose.phase2.yml
    redis.conf
  docs/
    PHASE2_REALTIME_BLUEPRINT.md
```

## Minimal Implementation Checklist

1. Create Redis and stream producer in `sync-worker`.
2. Refactor existing `caldera_neo4j/neo4j_writer.py` into reusable writer module for consumer.
3. Add consumer-group processing + ack + DLQ.
4. Add `graph.updated` publish after successful write.
5. Build `realtime-gateway` WebSocket broadcast service.
6. Wire dashboard JS to connect WebSocket and refresh filtered graph on event.
7. Add health/metrics endpoints.
8. Add `.env` + config loader and remove hardcoded secrets.

## Acceptance Criteria

1. New CALDERA link appears in UI in <= 7 seconds.
2. Flask stays responsive during CALDERA or Neo4j slowness.
3. Restarting any one service does not bring down others.
4. Duplicate events do not create duplicate `Fact` or duplicate edges.
5. `NEXT` chain remains consistent per agent timeline.

## Recommended Next Action

Implement **Phase 2.1 first** (queue + worker + writer, keep polling UI).
This gives stability and prepares cleanly for WebSocket push in Phase 2.2.
