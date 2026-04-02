import json
import json
import time
import psutil  # for system metrics

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


def initialize_dependencies():
    while True:
        try:
            r = connect_redis()
            ensure_group(r)

            writer = Neo4jEventWriter(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
            writer.ensure_constraints()
            return r, writer
        except Exception as exc:
            print(f"[graph_writer] waiting for dependencies: {exc}")
            time.sleep(5)


def handle_message(r, writer, retry_counts, msg_id, fields):
    global seen_event_ids  # Track for metrics
    if 'seen_event_ids' not in globals():
        seen_event_ids = set()
    
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
        
        # Metrics: track unique events
        eid = event.get("event_id")
        if eid:
            seen_event_ids.add(eid)
            if len(seen_event_ids) > 100000:
                seen_event_ids = set(list(seen_event_ids)[-50000:])
        
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


def log_metrics(r, start_time, processed_count, last_dlq_size):
    """Log processing metrics every 30s"""
    now = time.time()
    if now - start_time < 30:
        return start_time, processed_count
    
    stream_len = r.xlen(STREAM_NAME)
    dlq_len = r.xlen(DLQ_STREAM)
    pending_len = len(r.xpending(STREAM_NAME, CONSUMER_GROUP) or [])
    seen_size = len(seen_event_ids) if 'seen_event_ids' in globals() else 0
    
    rate = (processed_count / 30) if processed_count else 0
    delta_dlq = dlq_len - last_dlq_size
    
    print(f"[METRICS] backlog={stream_len} pending={pending_len} dlq={dlq_len} "
          f"delta_dlq={delta_dlq:+} rate={rate:.1f}/s mem={psutil.Process().memory_info().rss/1024/1024:.0f}MB "
          f"seen={seen_size}")
    
    return now, 0

def process_loop():
    r, writer = initialize_dependencies()

    retry_counts = {}
    metrics_start = time.time()
    processed_total = 0
    last_dlq = 0

    while True:
        try:
            # Log metrics
            metrics_start, processed_total = log_metrics(r, metrics_start, processed_total, last_dlq)
            last_dlq = r.xlen(DLQ_STREAM)
            
            reclaimed = reclaim_stale_pending(r)
            if reclaimed:
                print(f"[graph_writer] reclaimed {len(reclaimed)} pending messages")
                for msg_id, fields in reclaimed:
                    if handle_message(r, writer, retry_counts, msg_id, fields):
                        processed_total += 1

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
                    if handle_message(r, writer, retry_counts, msg_id, fields):
                        processed_total += 1

        except Exception as exc:
            print(f"[graph_writer] loop error: {exc}")
            try:
                writer.close()
            except Exception:
                pass
            r, writer = initialize_dependencies()
            time.sleep(2)


def main():
    process_loop()


if __name__ == "__main__":
    main()
