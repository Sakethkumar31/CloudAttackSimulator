# sync.py

from datetime import datetime, timezone

import requests

from config import CALDERA_API_KEY, CALDERA_URL
from neo4j_writer import (
    build_timeline_for_agent,
    ensure_constraints,
    link_agent_to_fact,
    link_fact_to_technique,
    reconcile_agents,
    reconcile_facts,
    write_agent,
    write_attack,
    write_fact,
)

HEADERS = {
    "KEY": CALDERA_API_KEY,
    "Content-Type": "application/json",
}


def fetch_operations():
    url = f"{CALDERA_URL}/api/v2/operations"
    response = requests.get(url, headers=HEADERS, verify=False)
    response.raise_for_status()
    return response.json()


def fetch_agents():
    url = f"{CALDERA_URL}/api/v2/agents"
    response = requests.get(url, headers=HEADERS, verify=False)
    response.raise_for_status()
    return response.json()


def parse_iso_datetime(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def agent_status(agent):
    now = datetime.now(timezone.utc)
    last_seen = parse_iso_datetime(agent.get("last_seen"))
    if not last_seen:
        return "unknown"

    sleep_min = int(agent.get("sleep_min") or 0)
    sleep_max = int(agent.get("sleep_max") or 0)
    watchdog = int(agent.get("watchdog") or 0)
    elapsed_ms = max(0, int((now - last_seen).total_seconds() * 1000))
    is_alive = elapsed_ms < (sleep_max * 1000)

    if elapsed_ms <= 60000 and sleep_min == 3 and sleep_max == 3 and watchdog == 1:
        return "pending kill"
    return "alive" if (elapsed_ms <= 60000 or is_alive) else "dead"


def main():
    print("Starting sync...")
    ensure_constraints()

    operations = fetch_operations()
    agents = fetch_agents()

    current_agent_ids = []
    current_fact_ids = []
    touched_agents = set()

    for agent in agents:
        if not isinstance(agent, dict):
            continue
        paw = agent.get("paw")
        if not paw:
            continue
        enriched_agent = dict(agent)
        status = agent_status(enriched_agent)
        enriched_agent["status"] = status
        enriched_agent["active"] = status in {"alive", "pending kill"}
        write_agent(enriched_agent)
        current_agent_ids.append(paw)
        touched_agents.add(paw)

    for op in operations:
        links = op.get("chain", [])
        for link in links:
            if not isinstance(link, dict):
                continue
            if link.get("status") != 0:
                continue

            paw = link.get("paw")
            if not paw:
                continue

            touched_agents.add(paw)
            enriched_link = dict(link)
            enriched_link["operation_id"] = op.get("id")

            fact_id = write_fact(enriched_link)
            current_fact_ids.append(fact_id)
            link_agent_to_fact(paw, fact_id)

            ability = link.get("ability", {}) or {}
            technique_id = ability.get("technique_id")
            technique_name = ability.get("technique_name")
            tactic_name = ability.get("tactic")

            if technique_id and technique_id != "auto-generated":
                write_attack(
                    technique_id,
                    technique_name or "Unknown",
                    tactic_name or "unknown",
                )
                link_fact_to_technique(fact_id, technique_id)

    reconcile_agents(sorted(set(current_agent_ids)))
    reconcile_facts(sorted(set(current_fact_ids)))

    for paw in sorted(touched_agents):
        build_timeline_for_agent(paw)

    print(
        f"Sync completed successfully. agents={len(set(current_agent_ids))} facts={len(set(current_fact_ids))}"
    )


if __name__ == "__main__":
    main()
