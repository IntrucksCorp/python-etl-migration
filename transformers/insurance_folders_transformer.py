"""
Maps Nowcerts InsuredList + PolicyDetailList → Supabase `insurance_folders` table.

Verified field names from inspection:
  InsuredList.id             → _nowcerts_insured_id
  InsuredList.commercialName → name
  PolicyDetailList.totalPremium      → total_premium    (not premium)
  PolicyDetailList.totalNonPremium   → policy_fee       (not taxesAndFees)
  PolicyDetailList.totalAgencyCommission → agency_fees  (not agencyFees)
"""
from __future__ import annotations

from typing import Any

from config.settings import TARGET_ORG_ID
from utils.helpers import safe_str, safe_float
from utils.logger import get_logger

logger = get_logger(__name__)


def transform_insurance_folders(
    insureds: list[dict[str, Any]],
    policies: list[dict[str, Any]],
    nowcerts_to_supabase_profile: dict[str, str],
) -> list[dict[str, Any]]:
    # Aggregate policy financials per insured
    policy_totals: dict[str, dict] = {}
    for pol in policies:
        insured_id = safe_str(pol.get("insuredDatabaseId"))
        if not insured_id:
            continue
        totals = policy_totals.setdefault(insured_id, {"premium": 0.0, "policy_fee": 0.0, "agency_fees": 0.0})
        totals["premium"] += safe_float(pol.get("totalPremium")) or 0.0          # not premium
        totals["policy_fee"] += safe_float(pol.get("totalNonPremium")) or 0.0    # not taxesAndFees
        totals["agency_fees"] += safe_float(pol.get("totalAgencyCommission")) or 0.0  # not agencyFees

    result: list[dict[str, Any]] = []

    for ins in insureds:
        nowcerts_id = safe_str(ins.get("id"))
        profile_id = nowcerts_to_supabase_profile.get(nowcerts_id or "")

        if not profile_id:
            continue

        name = safe_str(ins.get("commercialName")) or safe_str(ins.get("dba")) or "Migrated Client"
        totals = policy_totals.get(nowcerts_id or "")

        record: dict[str, Any] = {
            "name": name,
            "total_premium": totals["premium"] if totals else None,
            "policy_fee": totals["policy_fee"] if totals else None,
            "agency_fees": totals["agency_fees"] if totals else None,
            "analyst": None,
            "agent": None,
            "producer_name": None,
            "org_id": TARGET_ORG_ID or None,
            "_profile_id": profile_id,
            "_nowcerts_insured_id": nowcerts_id,
        }
        result.append(record)

    logger.info("Transformed %d insurance_folders", len(result))
    return result
