import json
import time

import redis

from config import (
    BLOCK_MS,
    CONSUMER_GROUP,
    CONSUMER_NAME,
    DLQ_STREAM,
    MAX_RETRIES,
    PENDING_BATCH_SIZE,
    PENDING_IDLE_MS,
    NEO4J_PASSWORD,
    NEO4J_URI,
    NEO4J_USER,
    PUBSUB_CHANNEL,
    REDIS_DB,
    REDIS_HOST,
    REDIS_PASSWORD,
    REDIS_PORT,
    STREAM_NAME,
)
from writer import Neo4jEventWriter


def connect_redis():
    return redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=REDIS_PASSWORD,
        decode_responses=True,
    )


def ensure_group(r):
    try:
        r.xgroup_create(STREAM_NAME, CONSUMER_GROUP, id="0", mkstream=True)
    except redis.ResponseError as exc:
        if "BUSYGROUP" not in str(exc):
            raise


def parse_data(fields):
    payload = fields.get("data")
    if not payload:
        return None
    return json.loads(payload)


def publish_update(r, event):
    event_type = event.get("event_type", "executed_link")
    msg = {
        "type": "graph.updated",
        "event_type": event_type,
        "agent_id": event.get("agent", {}).get("paw"),
        "target": event.get("fact", {}).get("target"),
        "changed_at": event.get("event_time"),
    }
    r.publish(PUBSUB_CHANNEL, json.dumps(msg))


def send_to_dlq(r, msg_id, data, reason):
    dlq_payload = {
        "id": msg_id,
        "reason": reason,
        "data": json.dumps(data),
        "failed_at": str(int(time.time())),
    }
    r.xadd(DLQ_STREAM, dlq_payload, maxlen=50000, approximate=True)


def handle_message(r, writer, retry_counts, msg_id, fields):
    event = parse_data(fields)
    if not event:
        r.xack(STREAM_NAME, CONSUMER_GROUP, msg_id)
        return True

    try:
        event_type = event.get("event_type", "executed_link")
        if event_type == "agent_snapshot":
            active_agents = event.get("active_agents")
            if active_agents is None:
                active_agents = [{"paw": aid} for aid in event.get("active_agent_ids", [])]
            writer.reconcile_agents(active_agents)
        elif event_type == "operation_snapshot":
            writer.reconcile_facts(event.get("active_fact_ids", []))
        else:
            writer.write_event(event)

        publish_update(r, event)
        r.xack(STREAM_NAME, CONSUMER_GROUP, msg_id)
        retry_counts.pop(msg_id, None)
        return True
    except Exception as exc:
        count = retry_counts.get(msg_id, 0) + 1
        retry_counts[msg_id] = count
        print(f"[graph_writer] failed msg={msg_id} attempt={count} err={exc}")

        if count >= MAX_RETRIES:
            send_to_dlq(r, msg_id, event, str(exc))
            r.xack(STREAM_NAME, CONSUMER_GROUP, msg_id)
            retry_counts.pop(msg_id, None)
        return False


def reclaim_stale_pending(r):
    reclaimed = []
    start_id = "0-0"

    while True:
        result = r.xautoclaim(
            name=STREAM_NAME,
            groupname=CONSUMER_GROUP,
            consumername=CONSUMER_NAME,
            min_idle_time=PENDING_IDLE_MS,
            start_id=start_id,
            count=PENDING_BATCH_SIZE,
        )

        next_start, messages = result[0], result[1]
        if not messages:
            break

        reclaimed.extend(messages)
        start_id = next_start
        if len(messages) < PENDING_BATCH_SIZE:
            break

    return reclaimed


def process_loop():
    r = connect_redis()
    ensure_group(r)

    writer = Neo4jEventWriter(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    writer.ensure_constraints()

    retry_counts = {}

    while True:
        try:
            reclaimed = reclaim_stale_pending(r)
            if reclaimed:
                print(f"[graph_writer] reclaimed {len(reclaimed)} pending messages")
                for msg_id, fields in reclaimed:
                    handle_message(r, writer, retry_counts, msg_id, fields)

            response = r.xreadgroup(
                groupname=CONSUMER_GROUP,
                consumername=CONSUMER_NAME,
                streams={STREAM_NAME: ">"},
                count=50,
                block=BLOCK_MS,
            )

            if not response:
                continue

            for _, messages in response:
                for msg_id, fields in messages:
                    handle_message(r, writer, retry_counts, msg_id, fields)

        except Exception as exc:
            print(f"[graph_writer] loop error: {exc}")
            time.sleep(2)


def main():
    process_loop()


if __name__ == "__main__":
    main()
