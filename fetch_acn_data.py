"""
fetch_acn_data.py
------------------
Pulls EV charging session data from the ACN-Data API (Caltech) and saves
it as a clean CSV ready for the EV-Charging-RL-System project
(data/ev_dataset.csv).

Usage:
    python fetch_acn_data.py --api-key YOUR_TOKEN --site caltech --start 2019-01-01 --end 2020-01-01

Get your API key at: https://ev.caltech.edu/register  (or /login to retrieve an existing one)
"""

import argparse
import csv
import time
from datetime import datetime
import requests

BASE_URL = "https://ev.caltech.edu/api/v1/sessions/{site_id}"


def to_rfc1123(date_str: str) -> str:
    """Convert 'YYYY-MM-DD' to the RFC1123 format ACN-Data's API expects,
    e.g. 'Mon, 01 Jan 2024 00:00:00 GMT'."""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.strftime("%a, %d %b %Y %H:%M:%S GMT")


def fetch_sessions(api_key: str, site_id: str, start: str = None, end: str = None):
    """
    Fetch all charging sessions for a site, following pagination.
    start/end should be 'YYYY-MM-DD' strings (optional).
    """
    url = BASE_URL.format(site_id=site_id)
    params = {}

    if start and end:
        params["where"] = (
            f'connectionTime>="{to_rfc1123(start)}" and '
            f'connectionTime<="{to_rfc1123(end)}"'
        )
        print(f"  where filter: {params['where']}")

    sessions = []
    page = 1

    while url:
        resp = requests.get(url, params=params if page == 1 else None, auth=(api_key, ""))
        if resp.status_code != 200:
            raise RuntimeError(f"API error {resp.status_code}: {resp.text[:300]}")

        data = resp.json()
        batch = data.get("_items", [])
        sessions.extend(batch)

        print(f"  fetched page {page} — {len(batch)} sessions (total so far: {len(sessions)})")

        next_link = data.get("_links", {}).get("next")
        if next_link:
            url = "https://ev.caltech.edu/api/v1/" + next_link["href"]
            params = None  # params are baked into the href already
            page += 1
            time.sleep(0.2)  # be polite to their server
        else:
            url = None

    return sessions


def flatten_session(s: dict) -> dict:
    """Pull out the useful RL-relevant fields into a flat row."""
    user_inputs = s.get("userInputs") or [{}]
    ui = user_inputs[0] if user_inputs else {}

    return {
        "sessionID": s.get("sessionID"),
        "siteID": s.get("siteID"),
        "stationID": s.get("stationID"),
        "spaceID": s.get("spaceID"),
        "connectionTime": s.get("connectionTime"),
        "disconnectTime": s.get("disconnectTime"),
        "doneChargingTime": s.get("doneChargingTime"),
        "kWhDelivered": s.get("kWhDelivered"),
        "kWhRequested": ui.get("kWhRequested"),
        "milesRequested": ui.get("milesRequested"),
        "minutesAvailable": ui.get("minutesAvailable"),
        "requestedDeparture": ui.get("requestedDeparture"),
        "WhPerMile": ui.get("WhPerMile"),
        "userID": s.get("userID"),
    }


def save_csv(sessions, out_path: str):
    rows = [flatten_session(s) for s in sessions]
    if not rows:
        print("No sessions found for the given filters.")
        return

    fieldnames = list(rows[0].keys())
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nSaved {len(rows)} sessions to {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", required=True, help="Your ACN-Data API token")
    parser.add_argument("--site", default="caltech", choices=["caltech", "jpl", "office001"])
    parser.add_argument("--start", default=None, help="YYYY-MM-DD")
    parser.add_argument("--end", default=None, help="YYYY-MM-DD")
    parser.add_argument("--out", default="data/ev_dataset.csv")
    parser.add_argument("--probe", action="store_true",
                         help="Just fetch 1 page with NO date filter, print date range, then exit.")
    args = parser.parse_args()

    if args.probe:
        print(f"Probing site='{args.site}' (no filters, sorted oldest+newest)...")
        url = BASE_URL.format(site_id=args.site)
        # oldest session
        r1 = requests.get(url, params={"sort": "-connectionTime", "pretty": ""}, auth=(args.api_key, ""))
        r1.raise_for_status()
        items1 = r1.json().get("_items", [])
        # newest session
        r2 = requests.get(url, params={"sort": "connectionTime", "pretty": ""}, auth=(args.api_key, ""))
        r2.raise_for_status()
        items2 = r2.json().get("_items", [])

        print(f"Total sessions reported: {r1.json().get('_meta', {}).get('total')}")
        if items1:
            print(f"Earliest-sorted sample connectionTime: {items1[0].get('connectionTime')}")
        if items2:
            print(f"Latest-sorted sample connectionTime: {items2[0].get('connectionTime')}")
        exit()

    print(f"Fetching sessions for site='{args.site}'...")
    sessions = fetch_sessions(args.api_key, args.site, args.start, args.end)
    save_csv(sessions, args.out)