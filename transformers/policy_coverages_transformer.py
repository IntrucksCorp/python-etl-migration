"""
Maps Nowcerts PolicyDetailList + CLCommercialAutoRatingDetailList
→ Supabase `policy_coverages` table.

Verified field names from inspection:
  PolicyDetailList.databaseId        → _nowcerts_policy_id
  PolicyDetailList.lineOfBusinesses  → coverage_type (array of objects)
  PolicyDetailList.number            → policy_number
  PolicyDetailList.effectiveDate, expirationDate → direct

  CLCommercialAutoRatingDetailList provides detailed limits per coverage type:
    autoLiabilityLimit, motorTruckCargoLimit, etc.
"""
from __future__ import annotations

import json
from typing import Any

from config.settings import TARGET_ORG_ID
from utils.helpers import safe_str, safe_int, parse_date
from utils.logger import get_logger

logger = get_logger(__name__)

# Maps CL auto rating boolean+limit pairs to coverage type names
_CL_COVERAGE_FIELDS = [
    ("autoLiability", "autoLiabilityLimit", "Auto Liability"),
    ("motorTruckCargo", "motorTruckCargoLimit", "Motor Truck Cargo"),
    ("nonTruckingLiability", "nonTruckingLiabilityLimit", "Non-Trucking Liability"),
    ("truckersGeneralLiability", "truckersGeneralLiabilityLimit", "Truckers General Liability"),
    ("trailerInterchange", "trailerInterchangeLimit", "Trailer Interchange"),
    ("automobilePhysicalDamage", "automobilePhysicalDamageLimit", "Physical Damage"),
]


def transform_policy_coverages(
    policies: list[dict[str, Any]],
    cl_auto_details: list[dict[str, Any]],
    nowcerts_policy_to_folder_carrier: dict[str, str],
) -> list[dict[str, Any]]:
    # Index CL auto details by insuredDatabaseId (no direct policy FK available)
    cl_by_insured: dict[str, dict] = {}
    for cl in cl_auto_details:
        iid = safe_str(cl.get("insuredDatabaseId"))
        if iid:
            cl_by_insured[iid] = cl

    result: list[dict[str, Any]] = []

    for pol in policies:
        nowcerts_pid = safe_str(pol.get("databaseId"))
        carrier_id = nowcerts_policy_to_folder_carrier.get(nowcerts_pid or "")

        if not carrier_id:
            logger.warning("PolicyCoverages — no carrier record for policy %s, skipping", nowcerts_pid)
            continue

        policy_number = safe_str(pol.get("number"))
        eff = parse_date(pol.get("effectiveDate"))
        exp = parse_date(pol.get("expirationDate"))

        # Extract coverage types from lineOfBusinesses
        lob_raw = pol.get("lineOfBusinesses") or []
        coverage_types: list[str] = []
        if isinstance(lob_raw, list):
            for item in lob_raw:
                if isinstance(item, dict):
                    name = safe_str(item.get("lineOfBusinessName") or item.get("name"))
                    if name:
                        coverage_types.append(name)

        if not coverage_types:
            coverage_types = ["General"]

        # Try to get detailed limits from CL auto rating if available
        insured_id = safe_str(pol.get("insuredDatabaseId"))
        cl = cl_by_insured.get(insured_id or "")

        if cl:
            # Build one coverage record per active CL coverage type
            for bool_field, limit_field, label in _CL_COVERAGE_FIELDS:
                if cl.get(bool_field):
                    limits = {"limit": safe_int(cl.get(limit_field))}
                    result.append({
                        "coverage_type": label,
                        "limits": json.dumps(limits),
                        "policy_number": policy_number,
                        "effective_date": eff,
                        "expiration_date": exp,
                        "status": "active",
                        "org_id": TARGET_ORG_ID or None,
                        "_carrier_record_id": carrier_id,
                        "_nowcerts_policy_id": nowcerts_pid,
                    })
        else:
            # Fall back to lineOfBusinesses list without specific limits
            for ctype in coverage_types:
                result.append({
                    "coverage_type": ctype,
                    "limits": json.dumps({}),
                    "policy_number": policy_number,
                    "effective_date": eff,
                    "expiration_date": exp,
                    "status": "active",
                    "org_id": TARGET_ORG_ID or None,
                    "_carrier_record_id": carrier_id,
                    "_nowcerts_policy_id": nowcerts_pid,
                })

    logger.info("Transformed %d policy_coverages", len(result))
    return result
