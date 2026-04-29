"""
Supabase loader — inserts records using the service-role key (bypasses RLS).
Strips internal `_` prefixed helper fields before inserting.
Uses upsert with on_conflict to make runs idempotent where possible.
"""
from __future__ import annotations

import math
from typing import Any

from supabase import create_client, Client

from config.settings import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
from utils.logger import get_logger

logger = get_logger(__name__)

_BATCH_SIZE = 200  # Supabase recommends ≤500 rows per request


def _get_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def _strip_internal(record: dict) -> dict:
    """Remove helper fields that start with '_' before writing to Supabase."""
    return {k: v for k, v in record.items() if not k.startswith("_")}


def upsert_batch(
    table: str,
    records: list[dict[str, Any]],
    on_conflict: str | None = None,
) -> list[dict[str, Any]]:
    """
    Insert records in batches. Returns list of inserted rows (with generated UUIDs).
    """
    if not records:
        logger.info("%s — nothing to insert", table)
        return []

    client = _get_client()
    clean = [_strip_internal(r) for r in records]
    total = len(clean)
    inserted: list[dict] = []

    batches = math.ceil(total / _BATCH_SIZE)
    for i in range(batches):
        chunk = clean[i * _BATCH_SIZE : (i + 1) * _BATCH_SIZE]
        logger.info("%s — inserting batch %d/%d (%d rows)", table, i + 1, batches, len(chunk))
        try:
            q = client.table(table).insert(chunk)
            resp = q.execute()
            inserted.extend(resp.data or [])
        except Exception as exc:
            logger.error("%s — batch %d failed: %s", table, i + 1, exc)
            raise

    logger.info("%s — inserted %d/%d rows", table, len(inserted), total)
    return inserted


def insert_profiles(profiles: list[dict]) -> list[dict]:
    return upsert_batch("profiles", profiles)


def insert_vehicles(vehicles: list[dict]) -> list[dict]:
    return upsert_batch("vehicles", vehicles)


def insert_drivers(drivers: list[dict]) -> list[dict]:
    return upsert_batch("drivers", drivers)


def insert_opportunities(opportunities: list[dict]) -> list[dict]:
    return upsert_batch("opportunities", opportunities)


def insert_insurance_folders(folders: list[dict]) -> list[dict]:
    return upsert_batch("insurance_folders", folders)


def insert_insurance_folder_carriers(carriers: list[dict]) -> list[dict]:
    return upsert_batch("insurance_folder_carriers", carriers)


def insert_policy_coverages(coverages: list[dict]) -> list[dict]:
    return upsert_batch("policy_coverages", coverages)


def insert_activities(activities: list[dict]) -> list[dict]:
    return upsert_batch("activities", activities)


def insert_cases(cases: list[dict]) -> list[dict]:
    return upsert_batch("cases", cases)
