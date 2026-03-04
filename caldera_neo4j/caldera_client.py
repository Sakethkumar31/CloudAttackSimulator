# caldera_client.py

import requests
from config import CALDERA_URL, CALDERA_API_KEY

HEADERS = {
    "KEY": CALDERA_API_KEY,
    "Content-Type": "application/json"
}

def get_agents():
    url = f"{CALDERA_URL}/api/v2/agents"
    r = requests.get(url, headers=HEADERS, timeout=10)
    r.raise_for_status()
    return r.json()

def get_links():
    """
    Extract executed ability links from operations
    """
    url = f"{CALDERA_URL}/api/v2/operations"
    r = requests.get(url, headers=HEADERS, timeout=10)
    r.raise_for_status()

    operations = r.json()
    links = []

    for op in operations:
        for link in op.get("chain", []):
            links.append(link)

    return links
