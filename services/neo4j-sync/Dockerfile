FROM python:3.11-slim

WORKDIR /app

# No separate reqs, install direct
RUN pip install neo4j requests --no-cache-dir

COPY caldera_neo4j /app/caldera_neo4j

COPY services/neo4j-sync/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]

