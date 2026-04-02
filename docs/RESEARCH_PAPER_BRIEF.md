# Cloud Attack Path Simulator - Research Paper Brief

Last updated: 2026-04-02

## Suggested Paper Titles

1. Cloud Attack Path Simulator: A Graph-Based SOC Digital Twin for Adversary Emulation and Defensive Training
2. From CALDERA to Neo4j: Attack-Path Reconstruction for Security Operations Training
3. A Queue-Driven Cyber Range for MITRE ATT&CK-Aligned Attack Visualization and Response Guidance

## Abstract Seed

This project presents the Cloud Attack Path Simulator, a lab-safe security operations platform that transforms adversary-emulation telemetry into a graph-based attack-path view for analysts and learners. The system integrates MITRE CALDERA for attack execution, Redis Streams for event buffering, Neo4j for graph persistence, and a Flask dashboard for interactive visualization, risk scoring, defense recommendations, and guided learning. By modeling agents, facts, techniques, and tactic relationships as a connected graph, the platform helps users move from isolated alerts to interpretable attack progression. Beyond analyst triage, the project extends the same operational context into game-like learning modules, including an interactive maze and CTF flow. The platform is positioned as a cyber range and SOC training environment rather than a production EDR system, with emphasis on explainability, modular architecture, and reviewer-friendly demonstration.

## Problem Statement

Existing lab demos often show commands or alerts, but not the full attack path connecting them. Analysts and students therefore miss:

- sequence awareness,
- relationship awareness,
- MITRE contextualization,
- and practical mitigation reasoning.

The project solves this by turning executed adversary actions into graph-linked evidence that is easier to explain, query, and visualize.

## Objectives

1. Simulate attack activity using CALDERA in a safe lab environment.
2. Normalize attack execution into structured events.
3. Persist events in a graph model that captures execution order and ATT&CK context.
4. Present attack-path progression through a SOC dashboard.
5. Generate risk and defense-oriented interpretation from graph state.
6. Support security learning through interactive educational modes.

## System Architecture

```text
CALDERA -> sync_worker -> Redis Streams -> graph_writer -> Neo4j -> Flask dashboard
```

Architecture rationale:

- CALDERA provides adversary-emulation realism.
- Redis decouples ingestion from graph persistence.
- Neo4j captures relationships more naturally than flat tables.
- Flask provides a fast, explainable frontend and API layer.

## Methodology

### Data Source

- Executed CALDERA operation links
- CALDERA agent status and metadata

### Processing Steps

1. Poll CALDERA APIs at a configured interval.
2. Extract executed links with valid agent context.
3. Normalize records into deterministic event payloads.
4. Publish events to Redis Streams.
5. Consume and write idempotent graph updates to Neo4j.
6. Reconcile stale agents and stale facts.
7. Query graph state from the dashboard for visualization and guidance.

### Graph Modeling

Nodes:

- Agent
- Fact
- Technique
- Tactic

Edges:

- EXECUTED
- NEXT
- USES
- PART_OF

### Analysis Layer

- attack path extraction
- technique frequency counting
- heuristic risk scoring
- matched scenario / defense recommendation generation
- agent-specific defensive profile building

## Key Contributions

1. A modular queue-backed SOC simulation architecture.
2. A graph-native representation of attack progression.
3. ATT&CK-aligned visibility from executed adversary behavior.
4. Integration of defensive reasoning into the same platform as attack simulation.
5. Educational expansion through Maze and CTF interfaces.

## Attack-Simulation Phases

### Phase 1: WSL foothold

- demonstrates command execution visibility
- corresponds to initial foothold and execution behavior

### Phase 2: credential or session reuse

- demonstrates identity misuse in a lab-safe scenario
- shows how trust abuse changes operational risk

### Phase 3: multi-system fan-out

- demonstrates lateral movement and graph growth
- reveals how one foothold becomes multi-host activity

### Phase 4: collection and controlled egress

- demonstrates outbound or staged exfiltration indicators
- supports response prioritization and path interpretation

## Evaluation Angles for the Paper

The friend preparing the document can frame evaluation around:

1. Visibility
   Can the platform show a connected attack path rather than isolated events?

2. Explainability
   Can a reviewer understand agent, command, technique, and sequence relationships?

3. Responsiveness
   How quickly does a CALDERA action appear in the dashboard workflow?

4. Training usefulness
   Do Maze and CTF modules make the system more valuable for learner onboarding?

5. Modularity
   Does the architecture remain stable when components are separated into workers and services?

## Example Metrics to Mention

- number of active agents
- number of executed facts
- number of `NEXT` chain links
- number of distinct ATT&CK techniques observed
- computed risk score per graph state
- top path depth
- per-target or per-agent path count
- update latency from CALDERA execution to dashboard visibility

## Honest Limitations

- heuristic scoring may not reflect real enterprise severity
- lab agent scope limits realism
- real-time behavior may still depend on polling intervals in some flows
- educational modules are training aids, not validated assessment instruments
- cloud-specific telemetry sources beyond CALDERA are limited in the current design

## Future Research Directions

- integrating more cloud-native attack telemetry
- comparing graph scoring methods
- evaluating training outcomes for learners using Maze and CTF modes
- automating evidence-pack export for reviewers
- adding richer real-time event push and collaborative SOC workflows

## Short Contribution Paragraph

This project contributes a graph-based cyber range workflow that connects adversary emulation, ATT&CK mapping, attack-path reconstruction, risk interpretation, and learner guidance in one modular platform. Instead of showing only command execution or alert lists, it reconstructs how attacker behavior progresses through a sequence of linked actions and presents that progression through both analyst and educational interfaces.

## Keywords

- attack graph
- SOC digital twin
- CALDERA
- MITRE ATT&CK
- adversary emulation
- Neo4j
- Redis Streams
- cyber defense education
- attack-path analysis
