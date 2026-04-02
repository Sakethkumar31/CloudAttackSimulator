from neo4j import GraphDatabase


class Neo4jEventWriter:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def ensure_constraints(self):
        constraints = [
            """
            CREATE CONSTRAINT agent_id_unique IF NOT EXISTS
            FOR (a:Agent) REQUIRE a.agent_id IS UNIQUE
            """,
            """
            CREATE CONSTRAINT fact_id_unique IF NOT EXISTS
            FOR (f:Fact) REQUIRE f.fact_id IS UNIQUE
            """,
            """
            CREATE CONSTRAINT technique_id_unique IF NOT EXISTS
            FOR (t:Technique) REQUIRE t.technique_id IS UNIQUE
            """,
            """
            CREATE CONSTRAINT tactic_name_unique IF NOT EXISTS
            FOR (ta:Tactic) REQUIRE ta.name IS UNIQUE
            """,
        ]
        with self.driver.session(database="neo4j") as session:
            for c in constraints:
                session.run(c)

    def upsert_agent(self, session, agent, active=True):
        agent_id = agent.get("paw")
        if not agent_id:
            return
        session.run(
            """
            MERGE (a:Agent {agent_id: $agent_id})
            SET a.host = $host,
                a.platform = $platform,
                a.group = $group,
                a.trusted = $trusted,
                a.active = $active,
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
                a.host_ip_addrs = $host_ip_addrs
            """,
            agent_id=agent_id,
            host=agent.get("host"),
            platform=agent.get("platform") or "linux",
            group=agent.get("group") or "red",
            trusted=agent.get("trusted", False),
            active=bool(active),
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
        )

    def write_event(self, event):
        agent = event.get("agent", {})
        fact = event.get("fact", {})
        mitre = event.get("mitre", {})

        agent_id = agent.get("paw")
        fact_id = fact.get("fact_id")
        if not agent_id or not fact_id:
            return

        with self.driver.session(database="neo4j") as session:
            self.upsert_agent(session, agent, active=True)

            session.run(
                """
                MERGE (f:Fact {fact_id: $fact_id})
                SET f.ability_id = $ability_id,
                    f.operation_id = $operation_id,
                    f.status = $status,
                    f.timestamp = $timestamp,
                    f.command = $command,
                    f.target = $target
                """,
                fact_id=fact_id,
                ability_id=fact.get("ability_id"),
                operation_id=event.get("operation_id"),
                status=fact.get("status"),
                timestamp=fact.get("timestamp"),
                command=fact.get("command"),
                target=fact.get("target"),
            )

            session.run(
                """
                MATCH (a:Agent {agent_id: $agent_id})
                MATCH (f:Fact {fact_id: $fact_id})
                MERGE (a)-[:EXECUTED]->(f)
                """,
                agent_id=agent_id,
                fact_id=fact_id,
            )

            technique_id = mitre.get("technique_id")
            if technique_id and technique_id != "auto-generated":
                session.run(
                    """
                    MERGE (t:Technique {technique_id: $technique_id})
                    SET t.name = $technique_name
                    MERGE (ta:Tactic {name: $tactic_name})
                    MERGE (t)-[:PART_OF]->(ta)
                    """,
                    technique_id=technique_id,
                    technique_name=mitre.get("technique_name") or "Unknown",
                    tactic_name=mitre.get("tactic") or "unknown",
                )
                session.run(
                    """
                    MATCH (f:Fact {fact_id: $fact_id})
                    MATCH (t:Technique {technique_id: $technique_id})
                    MERGE (f)-[:USES]->(t)
                    """,
                    fact_id=fact_id,
                    technique_id=technique_id,
                )

            session.run(
                """
                MATCH (a:Agent {agent_id: $agent_id})-[:EXECUTED]->(curr:Fact {fact_id: $fact_id})
                MATCH (a)-[:EXECUTED]->(prev:Fact)
                WHERE prev.fact_id <> curr.fact_id
                  AND prev.timestamp IS NOT NULL
                  AND curr.timestamp IS NOT NULL
                  AND prev.timestamp < curr.timestamp
                WITH curr, prev
                ORDER BY prev.timestamp DESC
                LIMIT 1
                MERGE (prev)-[:NEXT]->(curr)
                """,
                agent_id=agent_id,
                fact_id=fact_id,
            )

    def reconcile_agents(self, active_agents):
        active_agents = active_agents or []
        active_agent_ids = [a.get("paw") for a in active_agents if a.get("paw")]

        with self.driver.session(database="neo4j") as session:
            for agent in active_agents:
                self.upsert_agent(session, agent, active=True)

            session.run(
                """
                MATCH (a:Agent)
                WHERE NOT a.agent_id IN $active_agent_ids
                DETACH DELETE a
                """,
                active_agent_ids=active_agent_ids,
            )

    def reconcile_facts(self, active_fact_ids):
        active_fact_ids = [fid for fid in (active_fact_ids or []) if fid]
        with self.driver.session(database="neo4j") as session:
            session.run(
                """
                MATCH (f:Fact)
                WHERE NOT f.fact_id IN $active_fact_ids
                DETACH DELETE f
                """,
                active_fact_ids=active_fact_ids,
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

    def close(self):
        self.driver.close()
