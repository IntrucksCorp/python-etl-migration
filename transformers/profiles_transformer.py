"""
Maps Nowcerts InsuredList + InsuredLocationList → Supabase `profiles` table.

Field mapping (Nowcerts → profiles):
  InsuredList.dmv                    → dmv                (custom field)
  InsuredList.referralSourceCompanyName → current_insurance
  InsuredList.yearBusinessStarted    → years_in_business  (calculated)
  InsuredList.typeOfBusiness         → operation_type
  InsuredList.preferredLanguage      → language_preference
  InsuredList.phone                  → phone
  InsuredList.email                  → email
  InsuredList.companyName            → company_name
  InsuredLocationList (garaging)     → parking_address    (jsonb)
  InsuredLocationList (mailing)      → mailing_address    (jsonb)
  InsuredList.firstName+lastName     → full_name
"""
from __future__ import annotations

import json
from typing import Any

from config.settings import TARGET_ORG_ID
from utils.helpers import safe_str, safe_int, years_since
from utils.logger import get_logger

logger = get_logger(__name__)

# InsuredLocationList locationType values observed in Nowcerts
_GARAGING_TYPES = {"garaging", "garage", "location"}
_MAILING_TYPES = {"mailing", "mail"}


def _build_address(loc: dict) -> dict:
    return {
        "address": safe_str(loc.get("addressLine1")),
        "city": safe_str(loc.get("city")),
        "state": safe_str(loc.get("state")),
        "zip": safe_str(loc.get("zipCode")),
        "county": safe_str(loc.get("county")),
    }


def transform_profiles(
    insureds: list[dict[str, Any]],
    locations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    # Index locations by insuredDatabaseId
    garaging: dict[str, dict] = {}
    mailing: dict[str, dict] = {}

    for loc in locations:
        insured_id = safe_str(loc.get("insuredDatabaseId"))
        if not insured_id:
            continue
        loc_type = safe_str(loc.get("locationType") or "").lower()
        if loc_type in _GARAGING_TYPES:
            garaging[insured_id] = loc
        elif loc_type in _MAILING_TYPES:
            mailing[insured_id] = loc

    profiles: list[dict[str, Any]] = []

    for ins in insureds:
        nowcerts_id = safe_str(ins.get("databaseId") or ins.get("id"))

        first = safe_str(ins.get("firstName") or "")
        last = safe_str(ins.get("lastName") or "")
        full_name = " ".join(filter(None, [first, last])) or None

        yib_raw = ins.get("yearBusinessStarted")
        years_in_biz = years_since(yib_raw)

        garaging_loc = garaging.get(nowcerts_id or "")
        mailing_loc = mailing.get(nowcerts_id or "")

        profile: dict[str, Any] = {
            # identity
            "full_name": full_name,
            "email": safe_str(ins.get("email")),
            "phone": safe_str(ins.get("phone")),
            "company_name": safe_str(ins.get("companyName")),
            # regulatory
            "dmv": safe_str(ins.get("dmv")),
            # business
            "years_in_business": years_in_biz,
            "operation_type": safe_str(ins.get("typeOfBusiness")),
            "current_insurance": safe_str(ins.get("referralSourceCompanyName")),
            "language_preference": safe_str(ins.get("preferredLanguage")),
            # addresses
            "parking_address": json.dumps(_build_address(garaging_loc)) if garaging_loc else None,
            "mailing_address": json.dumps(_build_address(mailing_loc)) if mailing_loc else None,
            # meta
            "crm_role": "client",
            "org_id": TARGET_ORG_ID or None,
            # keep original id for cross-reference during migration
            "_nowcerts_id": nowcerts_id,
        }

        profiles.append(profile)

    logger.info("Transformed %d profiles", len(profiles))
    return profiles
