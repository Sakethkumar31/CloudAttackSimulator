from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    "bolt://127.0.0.1:7687",
    auth=("neo4j", "replace_with_neo4j_password")
)

with driver.session(database="neo4j") as session:
    result = session.run("RETURN 1 AS test")
    print(result.single()["test"])

print("CONNECTED SUCCESSFULLY")
