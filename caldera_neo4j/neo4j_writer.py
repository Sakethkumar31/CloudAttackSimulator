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
        a.trusted = $trusted
    """

    with driver.session() as session:
        session.run(
            query,
            id=agent_id,
            host=agent.get("host"),
            platform=agent.get("platform"),
            group=agent.get("group"),
            trusted=agent.get("trusted")
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
        f.command = $command
    """

    with driver.session() as session:
        session.run(
            query,
            id=fact_id,
            ability_id=link.get("ability", {}).get("ability_id"),
            status=link.get("status"),
            pid=link.get("pid"),
            timestamp=link.get("finish"),
            command=link.get("command")
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