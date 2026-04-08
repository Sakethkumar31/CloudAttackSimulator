# WSL Adversary Profile

## Goal

Provide a simple CALDERA-only `WSL Adversary` profile with 10 lab-safe Linux discovery commands for WSL-backed agents.

## Included Commands

- `whoami`
- `hostname`
- `uname -a`
- `id`
- `pwd`
- `ls -la`
- `ps aux`
- `ss -tulpen` with fallback to `ss -tuln`
- `ip addr` with fallback to `ifconfig`
- `head -n 10 /etc/passwd`

## MITRE ATT&CK Mapping

- `T1033` System Owner/User Discovery
- `T1082` System Information Discovery
- `T1083` File and Directory Discovery
- `T1057` Process Discovery
- `T1049` System Network Connections Discovery
- `T1016` System Network Configuration Discovery
- `T1087.001` Local Account

## Files

- Ability pack: `infra/caldera_abilities/wsl_adversary_abilities.yml`
- Adversary profile: `infra/caldera_adversaries/wsl_adversary.yml`
- Adversary ID: `c4e5a9b0-1d8a-4bb8-a9e6-2c8f3d7b6a41`

## Import Notes

1. Copy the ability YAML into CALDERA's `data/abilities/` path.
2. Copy the adversary YAML into CALDERA's `data/adversaries/` path.
3. Restart or reload CALDERA content, then select `WSL Adversary` in an operation.

## Dashboard Note

This profile is intentionally not wired into the custom dashboard adversary model. It exists for CALDERA operations only.
