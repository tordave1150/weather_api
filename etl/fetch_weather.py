#!/usr/bin/env python3
"""
Daily ETL — fetch Open-Meteo forecasts for all 77 Thai provinces → upsert MongoDB.

Spec: OPEN_METEO_FETCH.md sections 7, 9

Usage:
    python etl/fetch_weather.py                    # default: morning round
    python etl/fetch_weather.py --round afternoon  # afternoon refresh

Cron schedule (UTC):
    0 22 * * *   python etl/fetch_weather.py --round morning    (= 05:00 Bangkok)
    0  6 * * *   python etl/fetch_weather.py --round afternoon  (= 13:00 Bangkok)

This script runs standalone without Streamlit — secrets loaded via toml.
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone, timedelta

import toml
from pymongo import MongoClient

# ── Path setup ────────────────────────────────────────────────────────────────
ROOT           = Path(__file__).parents[1]
SECRETS        = toml.load(ROOT / ".streamlit/secrets.toml")
PROVINCES_PATH = ROOT / "data/provinces.json"

# ── Import shared weather client ──────────────────────────────────────────────
sys.path.insert(0, str(ROOT))
from app.weather import fetch_all_provinces  # noqa: E402

TZ_BANGKOK = timezone(timedelta(hours=7))


def get_collection():
    """Return the MongoDB collection using credentials from secrets.toml."""
    client = MongoClient(SECRETS["mongodb"]["uri"])
    db     = client[SECRETS["mongodb"]["db_name"]]
    return db[SECRETS["mongodb"]["collection"]]


def upsert_all(collection, docs: list[dict]) -> int:
    """Upsert all forecast documents, keyed by (date, province).

    Spec: OPEN_METEO_FETCH.md section 7 — afternoon round overwrites morning
    """
    success = 0
    for doc in docs:
        try:
            collection.update_one(
                filter={"date": doc["date"], "province": doc["province"]},
                update={"$set": doc},
                upsert=True,
            )
            success += 1
        except Exception as e:
            print(f"  Upsert failed for {doc['province']}: {e}")
    return success


def main():
    parser = argparse.ArgumentParser(description="Weather & Routing Advisor ETL")
    parser.add_argument(
        "--round",
        choices=["morning", "afternoon"],
        default="morning",
        help="Fetch round: morning (05:00 BKK) or afternoon (13:00 BKK)"
    )
    args = parser.parse_args()

    print(f"\n{'='*55}")
    print(f"Weather ETL -- {args.round.upper()} ROUND")
    print(f"{datetime.now(tz=TZ_BANGKOK).strftime('%Y-%m-%d %H:%M:%S')} (Bangkok)")
    print(f"{'='*55}\n")

    # Load province list
    provinces = json.loads(PROVINCES_PATH.read_text(encoding="utf-8"))
    print(f"Loaded {len(provinces)} provinces\n")

    # Fetch from Open-Meteo (free tier — no API key)
    docs = fetch_all_provinces(provinces, fetch_round=args.round)

    if not docs:
        print("No data fetched. Check network or Open-Meteo API status.")
        sys.exit(1)

    # Upsert to MongoDB Atlas
    print(f"\nUpserting {len(docs)} documents to MongoDB ...")
    collection = get_collection()
    saved = upsert_all(collection, docs)

    date_label = docs[0]["date"] if docs else "unknown"
    print(f"\n{'='*55}")
    print(f"Done: {saved}/{len(docs)} saved  |  Date: {date_label}")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    main()
