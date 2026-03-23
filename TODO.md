# Manual Sync Fix - Cloud Attack Lab

Status: Steps 1-3 Complete ✅

## 1. Verify Neo4j [x] ✅ CONNECTED
```cmd
python caldera_neo4j/test.py
```
Expected: CONNECTED SUCCESSFULLY

## 2. Verify Caldera API [x] ✅ AGENTS/OPS DATA FOUND
```cmd
curl http://localhost:8888/api/v2/agents
curl http://localhost:8888/api/v2/operations
```
Expected: [] or data

## 3. Run Sync [x] ✅ COMPLETED - DATA WRITTEN TO NEO4J
```cmd
cd caldera_neo4j
python sync.py
```
Expected: Starting sync... Sync completed.

## 4. Check Neo4j Data [ ] 
Neo4j browser http://localhost:7474
```
MATCH (n) RETURN n LIMIT 20
```

## 5. Start Dashboard [ ] 
```cmd
run_dashboard_web.bat
```
Expected: Graph shows agents/facts after refresh.

## 6. Generate Data [ ] 
- Caldera UI http://localhost:8888
- Create agent, operation → re-run sync.py → dashboard update.

## Continuous Sync [ ] 
```cmd
# Terminal 1: caldera server
# Terminal 2: python caldera_neo4j/sync.py  (loop: while true; do python sync.py; sleep 5; done)
```

Next: Complete step 1, report output.

