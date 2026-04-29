"""
Maps Nowcerts NotesList → Supabase `activities` table.

Verified field names from inspection:
  databaseId         → _nowcerts_id
  insured            → nested dict: insured.databaseId  (NOT insuredDatabaseId directly)
  subject            → subject + description (content is in subject, no separate description field)
  noteType           → used to set activity_type
"""
from __future__ import annotations

from typing import Any

from config.settings import TARGET_ORG_ID
from utils.helpers import safe_str
from utils.logger import get_logger

logger = get_logger(__name__)

_NOTE_TYPE_MAP = {
    "quote": "note",
    "general": "note",
    "follow up": "follow_up",
    "call": "call",
    "email": "email",
    "meeting": "meeting",
    "task": "task",
}


def transform_activities(
    notes: list[dict[str, Any]],
    nowcerts_to_supabase_profile: dict[str, str],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []

    for note in notes:
        # insuredDatabaseId is nested inside the insured object
        insured_obj = note.get("insured") or {}
        insured_id = safe_str(insured_obj.get("databaseId"))
        profile_id = nowcerts_to_supabase_profile.get(insured_id or "")

        if not profile_id:
            logger.warning("Note %s — no matching profile (insuredId=%s), skipping", note.get("databaseId"), insured_id)
            continue

        note_type = safe_str(note.get("noteType") or "").lower()
        activity_type = _NOTE_TYPE_MAP.get(note_type, "note")

        # In NotesList, content is stored in subject (may contain HTML)
        subject = safe_str(note.get("subject"))

        record: dict[str, Any] = {
            "client_id": profile_id,
            "activity_type": activity_type,
            "subject": subject,
            "description": subject,  # same content — no separate description field
            "completed": True,
            "org_id": TARGET_ORG_ID or None,
            "_nowcerts_id": safe_str(note.get("databaseId")),
        }
        result.append(record)

    logger.info("Transformed %d activities", len(result))
    return result
