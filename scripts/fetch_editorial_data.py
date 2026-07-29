#!/usr/bin/env python3
"""
Fetch Nominations (Roadmaps) and In-App Events (IAE) for all developers/apps
listed in data/developers.json from the internal Huxley API and write the
results to data/nominations.json and data/iae.json.

Usage:
    python3 scripts/fetch_editorial_data.py

Requires network access to huxley.itunes.apple.com (Apple internal / VPN).
Storefront defaults to 143443 (Germany / DE) — adjust STOREFRONT env var
if you need a different market.
"""
import json
import os
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parent.parent
DEVS_FILE = ROOT / "data" / "developers.json"
NOM_OUT = ROOT / "data" / "nominations.json"
IAE_OUT = ROOT / "data" / "iae.json"

STOREFRONT = os.environ.get("HUXLEY_STOREFRONT", "143443")  # 143443 = Germany
BASE = "https://huxley.itunes.apple.com/v2/detail/{adam_id}/{storefront}/iap/{endpoint}"

HEADERS = {
    "User-Agent": "EditorialDRI-CRM/1.0",
    "Accept": "application/json",
}


def fetch(adam_id: str, endpoint: str, storefront: str = STOREFRONT):
    url = BASE.format(adam_id=adam_id, storefront=storefront, endpoint=endpoint)
    req = Request(url, headers=HEADERS)
    try:
        with urlopen(req, timeout=20) as resp:
            data = resp.read()
            return json.loads(data)
    except HTTPError as e:
        return {"error": f"HTTP {e.code}", "url": url}
    except URLError as e:
        return {"error": str(e), "url": url}
    except json.JSONDecodeError:
        return {"error": "invalid JSON response", "url": url}


def main():
    devs = json.loads(DEVS_FILE.read_text())

    nominations = {}
    iae = {}

    for dev in devs:
        adam_id = str(dev["adamId"])
        name = dev["appName"]
        print(f"Fetching {name} ({adam_id}) ...", file=sys.stderr)

        nominations[adam_id] = {
            "appName": name,
            "data": fetch(adam_id, "roadmaps"),
        }
        time.sleep(0.3)

        iae[adam_id] = {
            "appName": name,
            "data": fetch(adam_id, "events"),
        }
        time.sleep(0.3)

    NOM_OUT.write_text(json.dumps(nominations, indent=2))
    IAE_OUT.write_text(json.dumps(iae, indent=2))
    print(f"Wrote {NOM_OUT} and {IAE_OUT}", file=sys.stderr)


if __name__ == "__main__":
    main()
