"""
Maps Nowcerts InsuredList + InsuredLocationList → Supabase `profiles` table.

Verified field names from inspection:
  InsuredList.id                     → _nowcerts_id
  InsuredList.commercialName / dba   → company_name
  InsuredList.eMail                  → email
  InsuredList.cellPhone              → phone
  InsuredList.yearBusinessStarted    → years_in_business (calculated)
  InsuredList.typeOfBusiness         → operation_type
  InsuredList.preferredLanguage      → language_preference
  InsuredList.referralSourceCompanyName → current_insurance
  InsuredLocationList.insuredDatabaseId → FK to link
  InsuredLocationList.type           → "Garage" = garaging, "Mailing" = mailing
  InsuredLocationList.stateName      → state (not .state)
"""
from __future__ import annotations

import json
from typing import Any

from config.settings import TARGET_ORG_ID
from utils.helpers import safe_str, years_since
from utils.logger import get_logger

logger = get_logger(__name__)

_GARAGING_TYPES = {"garage", "garaging", "garagin address", "location"}
_MAILING_TYPES = {"mailing", "mail"}


def _build_address(loc: dict) -> dict:
    return {
        "address": safe_str(loc.get("addressLine1")),
        "city": safe_str(loc.get("city")),
        "state": safe_str(loc.get("stateName")),  # stateName not state
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
        loc_type = safe_str(loc.get("type") or loc.get("locationName") or "").lower()
        if any(t in loc_type for t in _GARAGING_TYPES):
            garaging[insured_id] = loc
        elif any(t in loc_type for t in _MAILING_TYPES):
            mailing[insured_id] = loc
        else:
            # Default unmapped location to garaging
            garaging.setdefault(insured_id, loc)

    profiles: list[dict[str, Any]] = []

    for ins in insureds:
        nowcerts_id = safe_str(ins.get("id"))

        # Commercial clients use commercialName; dba as fallback
        company_name = safe_str(ins.get("commercialName")) or safe_str(ins.get("dba"))

        # Individual clients may have firstName/lastName
        first = safe_str(ins.get("firstName") or "")
        last = safe_str(ins.get("lastName") or "")
        full_name = company_name or " ".join(filter(None, [first, last])) or None

        yib_raw = ins.get("yearBusinessStarted")
        years_in_biz = years_since(yib_raw)

        garaging_loc = garaging.get(nowcerts_id or "")
        mailing_loc = mailing.get(nowcerts_id or "")

        profile: dict[str, Any] = {
            "full_name": full_name,
            "email": safe_str(ins.get("eMail")),         # eMail not email
            "phone": safe_str(ins.get("cellPhone")),     # cellPhone not phone
            "company_name": company_name,
            "years_in_business": years_in_biz,
            "operation_type": safe_str(ins.get("typeOfBusiness")),
            "current_insurance": safe_str(ins.get("referralSourceCompanyName")),
            "language_preference": safe_str(ins.get("preferredLanguage")),
            "parking_address": json.dumps(_build_address(garaging_loc)) if garaging_loc else None,
            "mailing_address": json.dumps(_build_address(mailing_loc)) if mailing_loc else None,
            "crm_role": "client",
            "org_id": TARGET_ORG_ID or None,
            "_nowcerts_id": nowcerts_id,
        }

        profiles.append(profile)

    logger.info("Transformed %d profiles", len(profiles))
    return profiles
