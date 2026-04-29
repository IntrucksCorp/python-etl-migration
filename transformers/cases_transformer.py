"""
Maps Nowcerts TasksList → Supabase `cases` table.

Field mapping:
  title        → title
  category     → subcategory
  description  → description
  insuredId    → client_id
  status       → status (mapped)
"""
from __future__ import annotations

from typing import Any

from config.settings import TARGET_ORG_ID
from utils.helpers import safe_str, parse_date
from utils.logger import get_logger

logger = get_logger(__name__)

_STATUS_MAP = {
    "open": "pending",
    "pending": "pending",
    "completed": "completed",
    "closed": "completed",
    "in progress": "in_progress",
}


def transform_cases(
    tasks: list[dict[str, Any]],
    nowcerts_to_supabase_profile: dict[str, str],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []

    for task in tasks:
        insured_id = safe_str(task.get("insuredDatabaseId"))
        profile_id = nowcerts_to_supabase_profile.get(insured_id or "")

        if not profile_id:
            logger.warning("Task %s — no matching profile, skipping", task.get("databaseId"))
            continue

        raw_status = safe_str(task.get("status") or "").lower()
        status = _STATUS_MAP.get(raw_status, "pending")

        record: dict[str, Any] = {
            "client_id": profile_id,
            "title": safe_str(task.get("title") or task.get("subject")),
            "subcategory": safe_str(task.get("category")),
            "description": safe_str(task.get("description") or task.get("notes")),
            "status": status,
            "due_date": parse_date(task.get("dueDate")),
            "org_id": TARGET_ORG_ID or None,
            "_nowcerts_id": safe_str(task.get("databaseId")),
        }
        result.append(record)

    logger.info("Transformed %d cases", len(result))
    return result
