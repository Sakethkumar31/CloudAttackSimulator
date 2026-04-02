# Cloud Attack Path Simulator - Friend Handoff Packet

Last updated: 2026-04-02

## 1. Project Name

Cloud Attack Path Simulator

## 2. One-Line Description

A SOC-focused cyber range platform that uses MITRE CALDERA, Redis, Neo4j, and a Flask dashboard to simulate attack activity, reconstruct attack paths, score risk, and guide defensive learning through graph views, analyst coaching, a maze game, and CTF challenges.

## 3. Problem the Project Solves

Security teams often see isolated alerts but struggle to understand how attacker actions connect into a full attack path. This project addresses that problem by:

- collecting attack execution data from CALDERA,
- converting executed actions into structured events,
- building agent-to-fact-to-technique relationships in Neo4j,
- reconstructing progression chains over time,
- presenting the result through a SOC dashboard with risk and defense guidance,
- and extending the same data into learning modules for students and reviewers.

## 4. Core Objective

The main objective is to create a lab-safe platform where simulated adversary behavior can be observed as an attack path instead of as disconnected logs. The system is meant for:

- security training,
- attack-path visualization,
- MITRE ATT&CK mapping,
- blue-team response practice,
- reviewer/demo presentation,
- and research/report documentation.

## 5. High-Level Architecture

```text
CALDERA API -> sync_worker -> Redis Streams -> graph_writer -> Neo4j -> Flask dashboard
```

Main pipeline:

1. CALDERA runs operations and generates executed links.
2. `sync_worker` polls CALDERA APIs and normalizes operation/agent data.
3. Redis Streams acts as a buffer/event bus.
4. `graph_writer` consumes events and updates Neo4j.
5. The Flask dashboard queries Neo4j and renders:
   - attack graphs,
   - MITRE technique summaries,
   - risk scores,
   - defense recommendations,
   - map-based attacker context,
   - maze learning mode,
   - CTF learning mode.

## 6. Main Technologies Used

- Python
- Flask
- Neo4j
- Redis
- Docker / Docker Compose
- MITRE CALDERA
- HTML/CSS/JavaScript
- Cytoscape.js for graph visualization
- Leaflet for geospatial view
- Gemini API integration for tutoring/advisor features

## 7. Important Repository Areas

- `dashboard_web/`
  Flask web app, API routes, graph queries, risk logic, learning flows, AI tutor features, UI templates, and static assets.
- `services/sync_worker/`
  Polls CALDERA, normalizes executed links and agent snapshots, and publishes them to Redis Streams.
- `services/graph_writer/`
  Consumes Redis events, writes graph entities into Neo4j, reconciles stale agents/facts, and publishes update notifications.
- `caldera_neo4j/`
  Supporting integration logic between CALDERA data and Neo4j graph handling.
- `infra/`
  Deployment templates, environment examples, Docker stack files, and adversary definitions.
- `docs/`
  Design notes, deployment notes, reviewer demo script, GitHub reference notes, and phase guidance.

## 8. Main Features Implemented

### A. Attack Graph Visualization

- Shows agent nodes and fact nodes.
- Connects agents to facts through `EXECUTED` edges.
- Connects sequential facts through `NEXT` edges.
- Helps analysts understand ordered attack progression.

### B. MITRE ATT&CK Mapping

- Extracts technique IDs from CALDERA abilities.
- Stores technique nodes in Neo4j.
- Displays top observed techniques in the dashboard.
- Supports scenario-based interpretation and reviewer explanation.

### C. Risk Scoring

- Builds a graph summary using counts of facts, chains, and techniques.
- Converts graph activity into a score and risk label such as `LOW`, `ELEVATED`, or `CRITICAL`.
- Highlights high-risk paths and exposed targets.

### D. Attack Path Reconstruction

- Finds fact chains using `NEXT` relationships.
- Creates ranked attack paths based on depth and technique diversity.
- Displays likely paths for triage and demonstration.

### E. Defense Recommendations

- Matches observed technique combinations to attack playbook patterns.
- Produces detection, telemetry, and response recommendations.
- Builds per-agent defense profiles.

### F. Live Operations Overview

- Tracks active CALDERA agents and operations.
- Shows alive/dead agent state.
- Supports filtering by agent and target.

### G. Geospatial Analyst View

- Resolves public or analyst-entered location data.
- Places analyst and attacker markers on a map.
- Helps demos show where suspicious infrastructure or agents appear to originate.

### H. Learning Modules

- Interactive Maze:
  teaches containment and mitigation as a step-by-step defensive mission.
- CTF module:
  introduces beginner-to-hard security questions and tutor-assisted practice.
- SOC tutor / advisor:
  offers guided explanations, hints, and simplified reasoning support.

## 9. Neo4j Data Model

Primary nodes:

- `Agent`
- `Fact`
- `Technique`
- `Tactic`

Primary relationships:

- `(Agent)-[:EXECUTED]->(Fact)`
- `(Fact)-[:NEXT]->(Fact)`
- `(Fact)-[:USES]->(Technique)`
- `(Technique)-[:PART_OF]->(Tactic)`

Why this matters:

- It turns raw execution events into a queryable attack graph.
- It preserves temporal sequencing.
- It makes MITRE-based analysis and reporting easier.

## 10. Event Flow in Simple Words

1. A CALDERA operation runs on an agent.
2. Executed links are returned by the CALDERA API.
3. The sync worker converts each executed link into a normalized JSON event.
4. Events are pushed to a Redis Stream.
5. The graph writer reads the stream and updates Neo4j.
6. The dashboard queries Neo4j and renders graph/risk/defense data.
7. The user sees the simulated attack path as a live SOC workflow.

## 11. Simulation / Attack Phases

These are the clearest attack-simulation phases already reflected in the repo documentation and dashboard logic.

### Phase 1. WSL Execution Foothold

- Goal: establish lab-safe attacker execution from a WSL/Linux environment.
- Technique focus: `T1059`
- Meaning for report: this phase demonstrates initial command execution and foothold visibility.

### Phase 2. Credential or Session Reuse

- Goal: emulate valid-account or session-abuse behavior in a safe lab context.
- Technique focus: `T1078`, `T1078.004`
- Meaning for report: this phase shows how identity misuse can increase attack scope without destructive behavior.

### Phase 3. Multi-System Fan-Out / Lateral Movement

- Goal: simulate spread from one host to multiple systems.
- Technique focus: `T1021`, `T1047`
- Meaning for report: this phase demonstrates chained movement, greater graph depth, and increased risk.

### Phase 4. Collection and Controlled Egress

- Goal: generate collection/exfiltration-style indicators in a safe environment.
- Technique focus: `T1041`, `T1567`
- Meaning for report: this phase shows how outbound or staged activity can be visualized and prioritized for response.

## 12. Platform / Development Phases

The repo also describes phased platform evolution:

- Phase 2.1:
  Introduce Redis + workers while keeping dashboard polling stable.
- Phase 2.2:
  Add real-time push/websocket style updates.
- Phase 2.3:
  Add advanced SOC panels, risk views, and progression surfaces.
- Phase 2.4:
  Add AI assistant integration for attack-path and defense guidance.

This distinction is useful in a paper:

- attack phases describe simulated adversary behavior,
- development phases describe system evolution and engineering design.

## 13. Research / Report Friendly Contributions

Possible contributions to mention:

1. A graph-based cyber range for attack-path reconstruction using CALDERA telemetry.
2. A queue-backed architecture that separates data collection, processing, storage, and visualization.
3. Integration of ATT&CK mapping with path scoring and defense suggestions.
4. Extension of analyst-facing telemetry into educational modes like Maze and CTF.
5. A reviewer-friendly demo platform that connects red-team simulation with blue-team interpretation.

## 14. Practical Use Cases

- SOC training and analyst onboarding
- cyber range demonstrations
- attack-path research prototypes
- teaching MITRE ATT&CK concepts
- explaining how single actions become multi-step incident chains
- student projects involving graph databases and security telemetry

## 15. What Makes the Project Distinct

- It is not just a normal dashboard.
- It combines simulation, graph analytics, risk interpretation, and education in one platform.
- It turns CALDERA operation output into an explainable attack chain.
- It includes both analyst and learner views instead of only raw telemetry.

## 16. Current Working Screens / Modules

Based on the codebase and existing documentation, the project currently includes:

- login page
- SOC dashboard
- backend/health and sync-status APIs
- graph API
- defense recommendation APIs
- analyst-location API
- maze UI and maze APIs
- CTF registration, challenge, scoreboard, and tutor chat
- tutor mode and advisor chat endpoints

## 17. Suggested Evidence for a Report

Useful evidence items to cite from this repo:

- architecture flow from CALDERA to Neo4j to dashboard
- CALDERA agent check-in evidence
- dashboard graph with agent and fact nodes
- MITRE technique list
- risk score and attack-path panel
- geospatial attacker/analyst map
- maze training interface
- CTF challenge interface
- Dockerized deployment setup

## 18. Suggested Limitations to Mention Honestly

- This is a lab/simulation platform, not a production EDR product.
- Risk scoring is heuristic, not a formal probabilistic model.
- Real-world attack fidelity depends on the CALDERA adversary profile and available lab agents.
- Geolocation can be approximate, especially in WSL/private-network contexts.
- AI tutoring quality depends on the configured model and prompt scope.

## 19. Suggested Future Work

- stronger real-time event push instead of dashboard polling fallback
- richer evaluation datasets and benchmark scenarios
- more attack playbooks and scenario matching
- multi-user SOC sessions and role-based collaboration
- alert history export and evidence-pack generation
- cloud-native telemetry sources beyond CALDERA

## 20. Short Ready-to-Send Summary

You can send this paragraph directly:

The Cloud Attack Path Simulator is a security training and visualization platform that converts MITRE CALDERA attack activity into a graph-based SOC workflow. It uses a queue-driven pipeline where CALDERA operation data is collected by a sync worker, passed through Redis, written into Neo4j, and then rendered in a Flask dashboard. The system reconstructs attack paths, maps actions to MITRE ATT&CK techniques, scores risk, and generates defense guidance. It also includes a geospatial attacker view, an interactive Maze for defensive response training, and a CTF mode with tutor support. The project is best described as a cyber range plus SOC digital twin for attack-path detection, simulation, mitigation guidance, and analyst education.

## 21. Recommended Keywords

- cloud attack path simulation
- SOC dashboard
- MITRE ATT&CK
- CALDERA
- Neo4j
- Redis Streams
- attack graph
- cyber range
- blue-team training
- adversary emulation
- risk scoring
- security education
