# caldera_neo4j/attack_mapping.py

from .neo4j_writer import write_attack, link_fact_to_technique

def process_attack_mapping(link):
    """
    Extract MITRE ATT&CK mapping from CALDERA link
    and write to Neo4j.
    """

    ability = link.get("ability", {})

    technique_id = ability.get("technique_id")
    technique_name = ability.get("technique_name")
    tactic = ability.get("tactic")

    # Skip auto-generated manual commands
    if not technique_id or technique_id == "auto-generated":
        return

    fact_id = link.get("id")

    if not fact_id:
        return

    # Write Technique + Tactic nodes
    write_attack(technique_id, technique_name, tactic)

    # Link Fact → Technique
    link_fact_to_technique(fact_id, technique_id)