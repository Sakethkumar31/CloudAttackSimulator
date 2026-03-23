import os

# ===== Caldera =====
CALDERA_URL = os.getenv("CALDERA_URL", "http://localhost:8888")
CALDERA_API_KEY = os.getenv("CALDERA_API_KEY", "")

# ===== Neo4j =====
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://127.0.0.1:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "replace_with_neo4j_password")

SYNC_INTERVAL = int(os.getenv("SYNC_INTERVAL", "30"))
