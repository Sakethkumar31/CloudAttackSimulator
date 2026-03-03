import os

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

STREAM_NAME = os.getenv("STREAM_NAME", "caldera.links.v1")
DLQ_STREAM = os.getenv("DLQ_STREAM", "caldera.links.dlq")
PUBSUB_CHANNEL = os.getenv("PUBSUB_CHANNEL", "graph.updated")
CONSUMER_GROUP = os.getenv("CONSUMER_GROUP", "writers")
CONSUMER_NAME = os.getenv("CONSUMER_NAME", "writer-1")
BLOCK_MS = int(os.getenv("BLOCK_MS", "5000"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "5"))

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://127.0.0.1:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "Saketh2004")
