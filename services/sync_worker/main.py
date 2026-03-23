import hashlib
import json
import time
from datetime import datetime, timezone

import redis
import requests

from config import (
    CALDERA_API_KEY,
    CALDERA_URL,
    POLL_INTERVAL_SECONDS,
    REDIS_DB,
    REDIS_HOST,
    REDIS_PASSWORD,
    REDIS_PORT,
    REQUEST_TIMEOUT_SECONDS,
    STREAM_NAME,
)


def build_headers():
    return {
        "KEY": CALDERA_API_KEY,
        "Content-Type": "application/json",
    }


def get_operations():
    url = f"{CALDERA_URL}/api/v2/operations"
    res = requests.get(url, headers=build_headers(), timeout=REQUEST_TIMEOUT_SECONDS, verify=False)
    res.raise_for_status()
    return res.json()


def get_agents():
    url = f"{CALDERA_URL}/api/v2/agents"
    res = requests.get(url, headers=build_headers(), timeout=REQUEST_TIMEOUT_SECONDS, verify=False)
    res.raise_for_status()
    return res.json()


def unwrap_items(payload, preferred_keys):
    if isinstance(payload, list):
        return payload

    if isinstance(payload, dict):
        for key in preferred_keys:
            value = payload.get(key)
            if isinstance(value, list):
                return value

        for value in payload.values():
            if isinstance(value, list):
                return value

    return []


def event_id_for(link):
    raw = f"{link.get('paw','')}-{link.get('ability', {}).get('ability_id','')}-{link.get('finish','')}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def normalize_event(operation_id, link):
    ability = link.get("ability", {})
    return {
        "event_type": "executed_link",
        "event_id": event_id_for(link),
        "event_time": datetime.now(timezone.utc).isoformat(),
        "source": "caldera",
        "operation_id": operation_id,
        "agent": {
            "paw": link.get("paw"),
            "host": link.get("host"),
            "platform": link.get("platform") or "linux",
            "group": link.get("group") or "red",
            "trusted": bool(link.get("trusted", False)),
        },
        "fact": {
            "fact_id": link.get("id") or event_id_for(link),
            "ability_id": ability.get("ability_id"),
            "command": link.get("command"),
            "status": link.get("status"),
            "timestamp": link.get("finish"),
            "target": link.get("target"),
        },
        "mitre": {
            "technique_id": ability.get("technique_id"),
            "technique_name": ability.get("technique_name"),
            "tactic": ability.get("tactic"),
        },
    }


def normalize_agent(agent):
    return {
        "paw": agent.get("paw"),
        "host": agent.get("host"),
        "platform": agent.get("platform") or "linux",
        "group": agent.get("group") or "red",
        "trusted": bool(agent.get("trusted", False)),
    }


def build_agent_snapshot_event(agents):
    normalized = [normalize_agent(a) for a in agents if a.get("paw")]
    normalized.sort(key=lambda a: a["paw"])

    raw = json.dumps(normalized, sort_keys=True)
    snapshot_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()

    return {
        "event_type": "agent_snapshot",
        "event_id": f"snapshot-{snapshot_hash}",
        "event_time": datetime.now(timezone.utc).isoformat(),
        "source": "caldera",
        "active_agents": normalized,
        "active_agent_ids": [a["paw"] for a in normalized],
    }


def publish_events(r, events):
    for event in events:
        r.xadd(STREAM_NAME, {"data": json.dumps(event)}, maxlen=20000, approximate=True)


def collect_executed_links(operations):
    events = []
    for op in unwrap_items(operations, ["operations", "items", "data"]):
        if not isinstance(op, dict):
            continue
        state = str(op.get("state", "")).strip().lower()
        if state in {"finished", "cleanup", "out_of_time", "closed", "archived"}:
            continue
        op_id = op.get("id")
        for link in op.get("chain", []):
            if not isinstance(link, dict):
                continue
            if link.get("status") != 0:
                continue
            if not link.get("paw"):
                continue
            events.append(normalize_event(op_id, link))
    return events


def collect_active_fact_ids(operations):
    fact_ids = []
    for op in unwrap_items(operations, ["operations", "items", "data"]):
        if not isinstance(op, dict):
            continue
        state = str(op.get("state", "")).strip().lower()
        if state in {"finished", "cleanup", "out_of_time", "closed", "archived"}:
            continue
        for link in op.get("chain", []):
            if not isinstance(link, dict):
                continue
            if link.get("status") != 0:
                continue
            if not link.get("paw"):
                continue
            fact_id = link.get("id") or event_id_for(link)
            fact_ids.append(fact_id)
    return sorted(set(fact_ids))


def build_operation_snapshot_event(operations):
    active_fact_ids = collect_active_fact_ids(operations)
    raw = json.dumps(active_fact_ids, sort_keys=True)
    snapshot_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return {
        "event_type": "operation_snapshot",
        "event_id": f"ops-{snapshot_hash}",
        "event_time": datetime.now(timezone.utc).isoformat(),
        "source": "caldera",
        "active_fact_ids": active_fact_ids,
    }


def main():
    r = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=REDIS_PASSWORD,
        decode_responses=True,
    )

    seen_event_ids = set()
    while True:
        try:
            operations = get_operations()
            agents = get_agents()
            agent_items = unwrap_items(agents, ["agents", "items", "data"])

            events = collect_executed_links(operations)
            fresh = []

            for event in events:
                eid = event["event_id"]
                if eid in seen_event_ids:
                    continue
                seen_event_ids.add(eid)
                fresh.append(event)

            # Always publish agent snapshot every poll for eventual consistency.
            # This guarantees agent create/delete reconciliation even if a prior
            # snapshot failed downstream once.
            snapshot_event = build_agent_snapshot_event(agent_items)
            fresh.append(snapshot_event)
            fresh.append(build_operation_snapshot_event(operations))

            if fresh:
                publish_events(r, fresh)
                print(f"[sync_worker] published {len(fresh)} events to {STREAM_NAME}")
            else:
                print("[sync_worker] no new executed links")

            if len(seen_event_ids) > 50000:
                seen_event_ids = set(list(seen_event_ids)[-20000:])

        except Exception as exc:
            print(f"[sync_worker] error: {exc}")

        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
