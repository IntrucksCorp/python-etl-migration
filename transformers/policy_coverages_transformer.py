"""
Maps Nowcerts PolicyDetailList + CLCommercialAutoRatingDetailList
→ Supabase `policy_coverages` table.

Field mapping:
  lineOfBusiness    → coverage_type
  limit             → limits  (jsonb: {"limit": value})
  deductible        → limits  (jsonb: merged {"limit": ..., "deductible": ...})
  effectiveDate     → effective_date
  expirationDate    → expiration_date
  policyNumber      → policy_number
"""
from __future__ import annotations

import json
from typing import Any

from config.settings import TARGET_ORG_ID
from utils.helpers import safe_str, safe_float, parse_date
from utils.logger import get_logger

logger = get_logger(__name__)


def transform_policy_coverages(
    policies: list[dict[str, Any]],
    cl_auto_details: list[dict[str, Any]],
    nowcerts_policy_to_folder_carrier: dict[str, str],
) -> list[dict[str, Any]]:
    """
    nowcerts_policy_to_folder_carrier: {nowcerts_policy_databaseId → supabase insurance_folder_carriers UUID}
    """
    # Index CL auto details by policyDatabaseId
    cl_by_policy: dict[str, list[dict]] = {}
    for cl in cl_auto_details:
        pid = safe_str(cl.get("policyDatabaseId"))
        if pid:
            cl_by_policy.setdefault(pid, []).append(cl)

    result: list[dict[str, Any]] = []

    for pol in policies:
        nowcerts_pid = safe_str(pol.get("databaseId"))
        carrier_id = nowcerts_policy_to_folder_carrier.get(nowcerts_pid or "")

        if not carrier_id:
            logger.warning("PolicyCoverages — no carrier record for policy %s, skipping", nowcerts_pid)
            continue

        lob_raw = pol.get("lineOfBusiness")
        coverage_types: list[str] = []
        if isinstance(lob_raw, list):
            coverage_types = [safe_str(x) for x in lob_raw if x]
        elif isinstance(lob_raw, str) and lob_raw.strip():
            coverage_types = [lob_raw.strip()]

        if not coverage_types:
            coverage_types = ["General"]

        base_limits = {
            "limit": safe_float(pol.get("limit")),
            "deductible": safe_float(pol.get("deductible")),
        }

        for ctype in coverage_types:
            record: dict[str, Any] = {
                "coverage_type": ctype,
                "limits": json.dumps(base_limits),
                "policy_number": safe_str(pol.get("policyNumber")),
                "effective_date": parse_date(pol.get("effectiveDate")),
                "expiration_date": parse_date(pol.get("expirationDate")),
                "status": "active",
                "org_id": TARGET_ORG_ID or None,
                "_carrier_record_id": carrier_id,
                "_nowcerts_policy_id": nowcerts_pid,
            }
            result.append(record)

    logger.info("Transformed %d policy_coverages", len(result))
    return result
