# Screenshot Contexts

Last updated: 2026-04-02

This document explains what each shared screenshot represents, how it should be named in the repository, and what a viewer should understand from it.

## Recommended Screenshot Order

1. Architecture overview
2. Pipeline / data-flow diagram
3. CALDERA frontend / attack-emulation source
4. SOC dashboard overview
5. Attack graph
6. Attack focus / path triage
7. Geospatial attacker map
8. Maze defender simulation
9. CTF learning mode

## Screenshot Set

### 1. `docs/screenshots/phase-0-architecture-overview.png`

Use image:

- the blue architecture board showing CALDERA, `sync_worker`, `graph_writer`, Redis Stream, SOC Dashboard, Maze, CTF, and Risk Assessments

What it shows:

- the end-to-end system architecture
- attack emulation as the source layer
- event processing as the middleware layer
- graph intelligence as the analysis layer
- SOC, Maze, and CTF as the application layer

Why it matters:

- this is the best top-level image for a first-time GitHub visitor
- it explains that the project is more than one UI and includes the full processing pipeline

Suggested caption:

The complete Cloud Attack Path Simulator architecture. CALDERA generates adversary-emulation activity, `sync_worker` normalizes events, Redis buffers them, `graph_writer` builds graph relationships in Neo4j, and the SOC Dashboard exposes analyst, Maze, CTF, and risk-assessment views.

### 2. `docs/screenshots/phase-0-data-pipeline.png`

Use image:

- the white pipeline diagram showing CALDERA Server -> `sync_worker` -> Redis Event Stream -> `graph_writer` -> Neo4j <-> Flask SOC Dashboard

What it shows:

- the implementation-focused data flow
- separation between ingestion, buffering, graph persistence, and presentation

Why it matters:

- this is useful in a technical report because it clearly maps to the actual services in the repo

Suggested caption:

Implementation pipeline for the platform. CALDERA operations are polled by `sync_worker`, published into Redis Streams, consumed by `graph_writer`, stored as an attack graph in Neo4j, and served to the Flask dashboard for graph, MITRE, Maze, CTF, and tutor features.

### 3. `docs/screenshots/phase-1-caldera-source.png`

Use image:

- the CALDERA collage / source-environment screenshot showing terminal activity and CALDERA UI

What it shows:

- the attack-emulation framework used as the upstream source of operations, agents, and technique-mapped activity

Why it matters:

- it grounds the project in a real adversary-emulation platform rather than a manually fabricated dataset

Suggested caption:

CALDERA serves as the attack-emulation engine for the project. Operations and agent activity created here are polled and transformed into the graph-based SOC workflow shown by the platform.

Note:

- this screenshot is stronger than a plain login screen because it shows both the CALDERA interface and the activity source context

### 4. `docs/screenshots/phase-2-soc-dashboard-overview.png`

Use image:

- the full SOC dashboard screenshot showing current risk, visible scope, sync health, live operations, and the attacker map

What it shows:

- the main analyst landing page
- health and visibility KPIs
- operation feed
- geospatial context
- analyst-console and mapped-agent surfaces

Why it matters:

- this is the strongest screenshot for explaining the platform as a SOC dashboard instead of only a graph viewer

Suggested caption:

SOC dashboard overview. The platform combines attack visibility, sync health, live operations, risk posture, and geospatial context in a single analyst-facing workspace.

### 5. `docs/screenshots/phase-3-attack-graph.png`

Use image:

- the graph screenshot showing agent `honpfj` connected to fact `hostname`

What it shows:

- the core graph model in action
- an `Agent` node connected to an observed `Fact`
- graph counts such as nodes, edges, and paths
- backend status and risk summary

Why it matters:

- this is the most direct proof that CALDERA execution is turned into a Neo4j-backed attack graph

Suggested caption:

Attack graph view. Executed activity from CALDERA is transformed into graph entities so analysts can inspect agent-to-fact relationships, path depth, and visible attack progression instead of reading isolated events.

### 6. `docs/screenshots/phase-3-attack-focus.png`

Use image:

- the close-up panel showing `ATTACK PATHS` and `CURRENT ATTACK FOCUS`

What it shows:

- ranked attack-path summaries
- current triage focus
- guidance text for containment and evidence preservation
- per-agent risk context

Why it matters:

- it demonstrates that the project does not stop at visualization; it adds analyst interpretation and response guidance

Suggested caption:

Attack focus panel. Ranked attack-path summaries are paired with contextual guidance so the analyst can prioritize scope, containment, and evidence preservation around the most important path.

### 7. `docs/screenshots/phase-4-geospatial-map.png`

Use image:

- the dashboard map screenshot showing analyst console and mapped attacker/agent pins near Hyderabad

What it shows:

- attacker/agent geospatial visualization
- tracked and mappable agent counts
- analyst-console location context
- explanatory note about approximate marker placement in private or WSL environments

Why it matters:

- it expands the project beyond graph-only analysis into spatial situational awareness

Suggested caption:

Geospatial attacker view. The platform overlays analyst and agent context on a map to support location-aware investigation while warning that WSL or private-network addresses can only be approximated.

### 8. `docs/screenshots/phase-5-maze-defender.png`

Use image:

- the Interactive Maze screenshot

What it shows:

- the defensive training extension of the platform
- mitigation steps such as recon, review logs, isolate host, block IOC, and verify containment
- a guided path from incident understanding to response execution

Why it matters:

- it shows that the project is not only for monitoring but also for teaching defensive reasoning

Suggested caption:

Interactive Maze mode. Attack-path concepts are converted into a guided defender simulation where the user practices the correct mitigation sequence and verifies that the path is actually closed.

### 9. `docs/screenshots/phase-5-ctf-level1.png`

Use image:

- the CTF Level 1 screenshot with mission brief, answer box, and tutor chatbot

What it shows:

- question-based learner practice
- chatbot-assisted hints and explanations
- difficulty and tutor-depth support

Why it matters:

- it highlights the project's training and student-onboarding value for demos and academic presentation

Suggested caption:

CTF mode extends the SOC platform into guided learner practice. Users answer security questions, request hints, and interact with a tutor chatbot that teaches reasoning without breaking the learning flow.

## Suggested README Layout

Recommended public GitHub order:

1. architecture overview
2. data pipeline
3. CALDERA source
4. SOC dashboard overview
5. attack graph
6. attack focus
7. maze
8. CTF

This order tells a clear story:

- where the data comes from,
- how it is processed,
- how analysts consume it,
- and how learners practice with it.

## Copyright and Attribution Guidance

Use a note close to the screenshots section:

Project screenshots, custom diagrams, and repository-authored explanatory media are copyright the repository owner unless otherwise noted. Product names, logos, map tiles, and third-party marks visible inside screenshots, including CALDERA, Redis, Neo4j, Flask, Leaflet, and OpenStreetMap attribution, remain the property of their respective owners and are shown only to document system integration and academic/demo use.

Practical guidance:

- claim copyright only over your original screenshots, diagrams, writing, and project-specific layouts
- do not claim ownership of third-party logos or trademarks visible inside the screenshots
- keep visible OpenStreetMap attribution where map tiles appear
- if you later add a license, make sure it does not imply ownership of external brands
