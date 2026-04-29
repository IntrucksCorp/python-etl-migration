"""
Maps Nowcerts NotesList → Supabase `activities` table.

Field mapping:
  subject      → subject
  description  → description
  insuredId    → client_id (via profile lookup)
  type         → activity_type = 'note'
"""
from __future__ import annotations

from typing import Any

from config.settings import TARGET_ORG_ID
from utils.helpers import safe_str
from utils.logger import get_logger

logger = get_logger(__name__)


def transform_activities(
    notes: list[dict[str, Any]],
    nowcerts_to_supabase_profile: dict[str, str],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []

    for note in notes:
        insured_id = safe_str(note.get("insuredDatabaseId"))
        profile_id = nowcerts_to_supabase_profile.get(insured_id or "")

        if not profile_id:
            logger.warning("Note %s — no matching profile, skipping", note.get("databaseId"))
            continue

        record: dict[str, Any] = {
            "client_id": profile_id,
            "activity_type": "note",
            "subject": safe_str(note.get("subject")),
            "description": safe_str(note.get("description") or note.get("notes")),
            "completed": True,
            "org_id": TARGET_ORG_ID or None,
            "_nowcerts_id": safe_str(note.get("databaseId")),
        }
        result.append(record)

    logger.info("Transformed %d activities", len(result))
    return result
