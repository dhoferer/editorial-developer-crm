#!/usr/bin/env python3
"""
Lokales Fetch-Tool für Huxley Nominations & In-App Events (IAE).

Läuft AUSSCHLIESSLICH lokal (nicht in GitHub Actions), weil Huxley eine
gültige AppleConnect-SSO-Browser-Session braucht, die GitHub-hosted Runner
nicht herstellen können (kein Netzwerkzugriff auf das Apple-interne Netz,
kein SSO-Cookie).

Ablauf:
  1. Erster Lauf: Ein sichtbares Chromium-Fenster öffnet sich, du loggst dich
     einmalig per AppleConnect SSO ein (Login/2FA). Danach werden die
     Session-Cookies in einem lokalen Profilordner (--profile-dir) gespeichert.
  2. Folgeläufe: Nutzt automatisch die gespeicherte Session (kein erneuter
     Login nötig, solange die Session gültig ist).
  3. Für jede App in data/developers.json werden /iap/roadmaps (Nominations)
     und /iap/events (IAE) aufgerufen, die JSON-Antwort geparst und in
     data/nominations.json bzw. data/iae.json geschrieben.

Nutzung:
  python3 scripts/local_fetch_huxley.py
  python3 scripts/local_fetch_huxley.py --headless      # nach erstem Login
  python3 scripts/local_fetch_huxley.py --storefront 143441   # US Storefront
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEVS_FILE = ROOT / "data" / "developers.json"
NOM_OUT = ROOT / "data" / "nominations.json"
IAE_OUT = ROOT / "data" / "iae.json"
PROFILE_DIR = ROOT / ".huxley-browser-profile"

BASE = "https://huxley.itunes.apple.com/v2/detail/{adam_id}/{storefront}/iap/{endpoint}"


def get_playwright():
    try:
        from playwright.sync_api import sync_playwright
        return sync_playwright
    except ImportError:
        # Fall back to vendored install (./vendor) if not on default path
        vendor = ROOT / "vendor"
        if vendor.exists():
            sys.path.insert(0, str(vendor))
            from playwright.sync_api import sync_playwright
            return sync_playwright
        raise


def extract_json_from_page(page):
    """Huxley API endpoints return raw JSON rendered as page text (or wrapped
    in a <pre>/<body> tag depending on browser JSON viewer). Try a few
    strategies to get the raw JSON string."""
    # Strategy 1: page.content() body text is pure JSON
    body_text = page.inner_text("body")
    try:
        return json.loads(body_text)
    except json.JSONDecodeError:
        pass

    # Strategy 2: some browsers wrap JSON in a <pre> viewer
    try:
        pre_text = page.inner_text("pre")
        return json.loads(pre_text)
    except Exception:
        pass

    # Strategy 3: strip HTML if the SPA renders it as a formatted UI (not raw
    # JSON) — try to find an embedded JSON blob via regex as last resort.
    html = page.content()
    match = re.search(r'(\{.*\})', html, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    return {"error": "could not parse JSON from page", "raw_preview": body_text[:300]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--headless", action="store_true",
                         help="Ohne sichtbares Browser-Fenster starten (nur nach erfolgreichem Erst-Login sinnvoll).")
    parser.add_argument("--storefront", default="514210363",
                         help="Huxley Storefront-ID (Default: 514210363 = Germany).")
    parser.add_argument("--profile-dir", default=str(PROFILE_DIR),
                         help="Ordner für die persistente Browser-Session (SSO-Cookies).")
    parser.add_argument("--limit", type=int, default=None,
                         help="Nur die ersten N Apps abrufen (zum Testen).")
    args = parser.parse_args()

    sync_playwright = get_playwright()
    devs = json.loads(DEVS_FILE.read_text())
    if args.limit:
        devs = devs[: args.limit]

    nominations = {}
    iae = {}

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            args.profile_dir,
            headless=args.headless,
            viewport={"width": 1280, "height": 900},
        )
        page = context.new_page()

        for dev in devs:
            adam_id = str(dev["adamId"])
            name = dev["appName"]

            for endpoint, store, label in (
                ("roadmaps", nominations, "Nominations"),
                ("events", iae, "IAE"),
            ):
                url = BASE.format(adam_id=adam_id, storefront=args.storefront, endpoint=endpoint)
                print(f"→ {label:12s} {name} ({adam_id}) ...", file=sys.stderr)
                try:
                    page.goto(url, wait_until="networkidle", timeout=30000)
                    # Falls SSO-Login nötig ist, wartet der Nutzer hier manuell
                    # (nur beim allerersten, nicht-headless Lauf relevant).
                    data = extract_json_from_page(page)
                except Exception as e:
                    data = {"error": str(e), "url": url}
                store[adam_id] = {"appName": name, "data": data}
                time.sleep(0.4)

        context.close()

    NOM_OUT.write_text(json.dumps(nominations, indent=2))
    IAE_OUT.write_text(json.dumps(iae, indent=2))
    print(f"\n✅ Geschrieben: {NOM_OUT}", file=sys.stderr)
    print(f"✅ Geschrieben: {IAE_OUT}", file=sys.stderr)
    print("\nNächster Schritt: git add data/nominations.json data/iae.json && git commit && git push", file=sys.stderr)


if __name__ == "__main__":
    main()
