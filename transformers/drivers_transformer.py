"""
Maps Nowcerts DriverList → Supabase `drivers` table.

Field mapping:
  firstName + lastName  → name
  dlNumber              → license_number
  dlState               → license_state
  licenseClass          → license_type
  dateOfBirth           → date_of_birth   (date)
  hireDate              → hire_date       (date)
  licenseIssueDate      → (stored in notes for now — no direct field in drivers)
  excluded (checkbox)   → owner           (bool: excluded = owner in Nowcerts)
  dlStatus              → dl_status       (stored in notes)
  radioOperacion        → (stored in notes via custom field)
"""
from __future__ import annotations

from typing import Any

from config.settings import TARGET_ORG_ID
from utils.helpers import safe_str, safe_bool, parse_date
from utils.logger import get_logger

logger = get_logger(__name__)


def transform_drivers(
    drivers: list[dict[str, Any]],
    nowcerts_to_supabase_profile: dict[str, str],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []

    for d in drivers:
        insured_id = safe_str(d.get("insuredDatabaseId"))
        profile_id = nowcerts_to_supabase_profile.get(insured_id or "")

        if not profile_id:
            logger.warning("Driver %s — no matching profile for insuredId=%s, skipping", d.get("databaseId"), insured_id)
            continue

        first = safe_str(d.get("firstName") or "")
        last = safe_str(d.get("lastName") or "")
        name = " ".join(filter(None, [first, last])) or None

        # Excluded checkbox in Nowcerts corresponds to "owner" in Trucker
        is_owner = safe_bool(d.get("excluded"))

        record: dict[str, Any] = {
            "name": name,
            "license_number": safe_str(d.get("dlNumber")),
            "license_state": safe_str(d.get("dlState")),
            "license_type": safe_str(d.get("licenseClass")),
            "date_of_birth": parse_date(d.get("dateOfBirth")),
            "hire_date": parse_date(d.get("hireDate")),
            "owner": is_owner,
            "status": "active",
            "org_id": TARGET_ORG_ID or None,
            # relationships
            "_profile_id": profile_id,
            "_nowcerts_id": safe_str(d.get("databaseId")),
            # extra fields that need notes storage
            "_dl_status": safe_str(d.get("dlStatus")),
            "_license_issue_date": parse_date(d.get("licenseIssueDate")),
            "_radio_operacion": safe_str(d.get("radioOperacion")),
        }
        result.append(record)

    logger.info("Transformed %d drivers", len(result))
    return result
