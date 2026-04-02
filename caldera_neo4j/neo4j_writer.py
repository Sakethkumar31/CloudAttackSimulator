# neo4j_writer.py

import hashlib
from neo4j import GraphDatabase
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USER, NEO4J_PASSWORD)
)

def ensure_constraints():
    constraints = [
        """
        CREATE CONSTRAINT agent_id_unique IF NOT EXISTS
        FOR (a:Agent)
        REQUIRE a.agent_id IS UNIQUE
        """,
        """
        CREATE CONSTRAINT fact_id_unique IF NOT EXISTS
        FOR (f:Fact)
        REQUIRE f.fact_id IS UNIQUE
        """,
        """
        CREATE CONSTRAINT technique_id_unique IF NOT EXISTS
        FOR (t:Technique)
        REQUIRE t.technique_id IS UNIQUE
        """,
        """
        CREATE CONSTRAINT tactic_name_unique IF NOT EXISTS
        FOR (ta:Tactic)
        REQUIRE ta.name IS UNIQUE
        """
    ]

    with driver.session() as session:
        for c in constraints:
            session.run(c)


def write_agent(agent):
    agent_id = agent.get("paw") or agent.get("id")
    if not agent_id:
        return None

    query = """
    MERGE (a:Agent {agent_id: $id})
    SET a.host = $host,
        a.platform = $platform,
        a.group = $group,
        a.trusted = $trusted,
        a.display_name = $display_name,
        a.username = $username,
        a.privilege = $privilege,
        a.last_seen = $last_seen,
        a.created = $created,
        a.sleep_min = $sleep_min,
        a.sleep_max = $sleep_max,
        a.watchdog = $watchdog,
        a.contact = $contact,
        a.pending_contact = $pending_contact,
        a.host_ip_addrs = $host_ip_addrs,
        a.status = $status,
        a.active = $active
    """

    with driver.session() as session:
        session.run(
            query,
            id=agent_id,
            host=agent.get("host"),
            platform=agent.get("platform"),
            group=agent.get("group"),
            trusted=agent.get("trusted"),
            display_name=agent.get("display_name") or agent_id,
            username=agent.get("username"),
            privilege=agent.get("privilege"),
            last_seen=agent.get("last_seen"),
            created=agent.get("created"),
            sleep_min=agent.get("sleep_min"),
            sleep_max=agent.get("sleep_max"),
            watchdog=agent.get("watchdog"),
            contact=agent.get("contact"),
            pending_contact=agent.get("pending_contact"),
            host_ip_addrs=agent.get("host_ip_addrs") or [],
            status=agent.get("status") or "unknown",
            active=bool(agent.get("active", True)),
        )

    return agent_id


def _generate_fact_id(link):
    raw = (
        f"{link.get('paw')}-"
        f"{link.get('ability', {}).get('ability_id')}-"
        f"{link.get('finish')}"
    )
    return hashlib.sha256(raw.encode()).hexdigest()


def write_fact(link):
    fact_id = link.get("id") or _generate_fact_id(link)

    query = """
    MERGE (f:Fact {fact_id: $id})
    SET f.ability_id = $ability_id,
        f.status = $status,
        f.pid = $pid,
        f.timestamp = $timestamp,
        f.command = $command,
        f.target = $target,
        f.operation_id = $operation_id
    """

    with driver.session() as session:
        session.run(
            query,
            id=fact_id,
            ability_id=link.get("ability", {}).get("ability_id"),
            status=link.get("status"),
            pid=link.get("pid"),
            timestamp=link.get("finish"),
            command=link.get("plaintext_command") or link.get("command") or link.get("ability", {}).get("name"),
            target=link.get("target"),
            operation_id=link.get("operation_id"),
        )

    return fact_id


def link_agent_to_fact(agent_id, fact_id):
    query = """
    MATCH (a:Agent {agent_id: $agent_id})
    MATCH (f:Fact {fact_id: $fact_id})
    MERGE (a)-[:EXECUTED]->(f)
    """

    with driver.session() as session:
        session.run(query, agent_id=agent_id, fact_id=fact_id)


def write_attack(technique_id, technique_name, tactic_name):
    query = """
    MERGE (t:Technique {technique_id: $technique_id})
    SET t.name = $technique_name
    MERGE (ta:Tactic {name: $tactic_name})
    MERGE (t)-[:PART_OF]->(ta)
    """

    with driver.session() as session:
        session.run(
            query,
            technique_id=technique_id,
            technique_name=technique_name,
            tactic_name=tactic_name
        )


def link_fact_to_technique(fact_id, technique_id):
    query = """
    MATCH (f:Fact {fact_id: $fact_id})
    MATCH (t:Technique {technique_id: $technique_id})
    MERGE (f)-[:USES]->(t)
    """

    with driver.session() as session:
        session.run(
            query,
            fact_id=fact_id,
            technique_id=technique_id
        )


def build_timeline_for_agent(agent_id):
    query = """
    MATCH (:Agent {agent_id: $agent_id})-[:EXECUTED]->(:Fact)-[r:NEXT]->(:Fact)<-[:EXECUTED]-(:Agent {agent_id: $agent_id})
    DELETE r
    """

    rebuild = """
    MATCH (a:Agent {agent_id: $agent_id})-[:EXECUTED]->(f:Fact)
    WITH f
    ORDER BY f.timestamp, f.fact_id
    WITH collect(f) AS facts
    UNWIND range(0, size(facts)-2) AS i
    WITH facts[i] AS f1, facts[i+1] AS f2
    MERGE (f1)-[:NEXT]->(f2)
    """

    with driver.session() as session:
        session.run(query, agent_id=agent_id)
        session.run(rebuild, agent_id=agent_id)


def reconcile_agents(current_agent_ids):
    with driver.session() as session:
        session.run(
            """
            MATCH (a:Agent)
            WHERE NOT a.agent_id IN $current_agent_ids
            DETACH DELETE a
            """,
            current_agent_ids=current_agent_ids,
        )


def reconcile_facts(current_fact_ids):
    with driver.session() as session:
        session.run(
            """
            MATCH (f:Fact)
            WHERE NOT f.fact_id IN $current_fact_ids
            DETACH DELETE f
            """,
            current_fact_ids=current_fact_ids,
        )
        session.run(
            """
            MATCH (t:Technique)
            WHERE NOT (:Fact)-[:USES]->(t)
            DETACH DELETE t
            """
        )
        session.run(
            """
            MATCH (ta:Tactic)
            WHERE NOT (:Technique)-[:PART_OF]->(ta)
            DETACH DELETE ta
            """
        )
