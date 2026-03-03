# sync.py

import requests
from config import CALDERA_URL, CALDERA_API_KEY
from neo4j_writer import (
    ensure_constraints,
    write_agent,
    write_fact,
    link_agent_to_fact,
    write_attack,
    link_fact_to_technique,
    build_timeline_for_agent
)

HEADERS = {
    "KEY": CALDERA_API_KEY,
    "Content-Type": "application/json"
}


def fetch_operations():
    url = f"{CALDERA_URL}/api/v2/operations"
    response = requests.get(url, headers=HEADERS, verify=False)
    response.raise_for_status()
    return response.json()


def main():
    print("Starting sync...")

    ensure_constraints()

    operations = fetch_operations()

    if not operations:
        print("No operations found.")
        return

    processed_agents = set()

    for op in operations:

        # 🔴 YOUR CALDERA USES 'chain'
        links = op.get("chain", [])

        for link in links:

            if link.get("status") != 0:
                continue

            agent_id = link.get("paw")
            if not agent_id:
                continue

            agent_data = {
                "paw": agent_id,
                "host": link.get("host"),
                "platform": "linux",
                "group": "red",
                "trusted": False
            }

            agent_id = write_agent(agent_data)
            processed_agents.add(agent_id)

            fact_id = write_fact(link)
            link_agent_to_fact(agent_id, fact_id)

            ability = link.get("ability", {})

            technique_id = ability.get("technique_id")
            technique_name = ability.get("technique_name")
            tactic_name = ability.get("tactic")

            if technique_id and technique_id != "auto-generated":
                write_attack(
                    technique_id,
                    technique_name or "Unknown",
                    tactic_name or "unknown"
                )
                link_fact_to_technique(fact_id, technique_id)

    for agent_id in processed_agents:
        build_timeline_for_agent(agent_id)

    print("Sync completed successfully.")


if __name__ == "__main__":
    main()