"""
Maps Nowcerts DriverList → Supabase `drivers` table.

Verified field names from inspection:
  id                → _nowcerts_id
  insuredDatabaseId → FK to profile
  firstName, lastName → name
  licenseNumber     → license_number  (not dlNumber)
  licenseState      → license_state   (not dlState)
  driverLicenseClass → license_type   (not licenseClass)
  dateOfBirth       → date_of_birth
  hireDate          → hire_date
  excluded          → owner (bool)
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
            logger.warning("Driver %s — no matching profile for insuredId=%s, skipping", d.get("id"), insured_id)
            continue

        first = safe_str(d.get("firstName") or "")
        last = safe_str(d.get("lastName") or "")
        name = " ".join(filter(None, [first, last])) or None

        record: dict[str, Any] = {
            "name": name,
            "license_number": safe_str(d.get("licenseNumber")),       # not dlNumber
            "license_state": safe_str(d.get("licenseState")),         # not dlState
            "license_type": safe_str(d.get("driverLicenseClass")),    # not licenseClass
            "date_of_birth": parse_date(d.get("dateOfBirth")),
            "hire_date": parse_date(d.get("hireDate")),
            "owner": safe_bool(d.get("excluded")),
            "status": "active",
            "org_id": TARGET_ORG_ID or None,
            "_profile_id": profile_id,
            "_nowcerts_id": safe_str(d.get("id")),
        }
        result.append(record)

    logger.info("Transformed %d drivers", len(result))
    return result
