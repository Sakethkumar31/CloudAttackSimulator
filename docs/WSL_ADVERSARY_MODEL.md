# WSL Adversary Model

## Goal

Use a lab-safe red-team model where one red user operates from a WSL foothold and simulates coordinated activity across multiple systems in the same CALDERA operation.

## Adversary Summary

- Name: `WSL Red User Multi-System Adversary`
- CALDERA adversary ID: `9e5ec39b-c0f8-4f65-a7f3-6d8d7f1a9a31`
- CALDERA file: `data/adversaries/9e5ec39b-c0f8-4f65-a7f3-6d8d7f1a9a31.yml`
- Platform: `WSL / Linux`
- Operation style: concurrent multi-agent operation
- Primary objective: emulate command execution, credential/session reuse, lateral movement, and controlled exfiltration signals across several lab systems at once

## Suggested Lab Scope

- WSL operator host
- Windows admin or jump host
- Application host
- Database or identity-connected host

## Recommended Simulation Phases

1. WSL execution foothold
   - Technique focus: `T1059`
   - Intent: simulate operator command execution from WSL with logging enabled

2. Credential or session reuse
   - Technique focus: `T1078`, `T1078.004`
   - Intent: emulate approved lab account reuse without real credential theft

3. Multi-system fan-out
   - Technique focus: `T1021`, `T1047`
   - Intent: generate parallel remote admin and lateral movement telemetry across more than one agent

4. Collection and controlled egress
   - Technique focus: `T1041`, `T1567`
   - Intent: create safe exfiltration-style indicators for blue-team response practice

## CALDERA Operation Setup

1. Register or reuse a WSL-backed agent.
2. Ensure the required Windows/Linux lab agents are alive before launching the operation.
3. Select adversary `WSL Red User Multi-System Adversary` in CALDERA.
4. Build one operation that includes multiple target agents, so the red user activity appears in parallel.
5. Prefer simulation-safe abilities that create telemetry rather than destructive impact.
6. Watch the dashboard for per-target risk, attack-path progression, and scenario-based defense guidance.

## Reviewer-Ready Description

This adversary model represents a red user working from a WSL foothold who attacks multiple systems at the same time. The purpose is not real compromise, but safe emulation of how command execution, account abuse, lateral movement, and outbound transfer indicators appear together in an enterprise attack path.

## Defense Suggestions

- Monitor both Windows and WSL process chains, especially `wsl.exe` spawning shells or network-capable tools.
- Correlate host, identity, and east-west network telemetry instead of reviewing each alert in isolation.
- Apply MFA, least privilege, and just-in-time admin controls for accounts that can reach several systems.
- Segment application, admin, and database tiers to limit spread from a single WSL-connected workstation.
- Alert on concurrent remote administration bursts and unusual outbound destinations after WSL activity.

## API Key Note

The dashboard uses Gemini via `GEMINI_API_KEY`. Do not hardcode keys into the repo. Set them through environment variables only.
