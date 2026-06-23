"""
MongoDB connection and query helpers for the Weather Advisor.
"""

import streamlit as st
from pymongo import MongoClient


@st.cache_resource
def get_db():
    """Return the MongoDB collection, cached as a Streamlit resource.

    Uses st.secrets for connection details — never hard-code credentials.
    """
    client = MongoClient(st.secrets["mongodb"]["uri"])
    db = client[st.secrets["mongodb"]["db_name"]]
    return db[st.secrets["mongodb"]["collection"]]


def upsert_forecast(collection, doc: dict):
    """Insert or replace a document keyed by (date, province/district, level).

    Used by the ETL script only — the dashboard is read-only.

    Args:
        collection: PyMongo collection object.
        doc: Forecast document dict.
    """
    level = doc.get("level", "province")
    if level == "district" and "district" in doc:
        key = {"date": doc["date"], "district": doc["district"], "level": level}
    else:
        key = {"date": doc["date"], "province": doc["province"], "level": level}

    collection.update_one(
        filter=key,
        update={"$set": doc},
        upsert=True,
    )


def get_forecasts(collection, date: str, regions: list[str] | None = None,
                  level: str = "province") -> list[dict]:
    """Return all location docs for a given date, optionally filtered by region.

    Args:
        collection: PyMongo collection object.
        date: Date string in YYYY-MM-DD format.
        regions: Optional list of region names to filter by.
        level: "province" | "district" — granularity level.

    Returns:
        List of forecast dicts (without _id field).
    """
    query = {"date": date}
    # Only filter by level if the field exists in any document
    # (backward-compatible with documents that pre-date the level field)
    query["level"] = level
    if regions:
        query["region"] = {"$in": regions}
    sort_key = "district" if level == "district" else "province"
    return list(collection.find(query, {"_id": 0}).sort(sort_key, 1))


def get_date_range(collection) -> tuple[str | None, str | None]:
    """Return (min_date, max_date) of logged data.

    Args:
        collection: PyMongo collection object.

    Returns:
        Tuple of (earliest_date, latest_date) strings, or (None, None) if empty.
    """
    pipeline = [
        {"$group": {"_id": None, "min": {"$min": "$date"}, "max": {"$max": "$date"}}}
    ]
    result = list(collection.aggregate(pipeline))
    if result:
        return result[0]["min"], result[0]["max"]
    return None, None
