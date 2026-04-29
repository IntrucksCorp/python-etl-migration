"""
Maps Nowcerts PolicyDetailList → Supabase `insurance_folder_carriers` table.

Verified field names from inspection:
  databaseId         → _nowcerts_policy_id
  insuredDatabaseId  → FK to insurance_folder
  carrierName        → carrier_name
  mgaName            → mga              (not mga)
  number             → policy_number    (not policyNumber)
  lineOfBusinesses   → coverages (array of objects: [{lineOfBusinessName, ...}])
  totalPremium       → premium          (not premium)
  totalNonPremium    → policy_fee_taxes (not taxesAndFees)
  totalAgencyCommission → agency_fees   (not agencyFees)
  effectiveDate, expirationDate, bindDate → direct
"""
from __future__ import annotations

from typing import Any

from config.settings import TARGET_ORG_ID
from utils.helpers import safe_str, safe_float, parse_date
from utils.logger import get_logger

logger = get_logger(__name__)


def transform_insurance_folder_carriers(
    policies: list[dict[str, Any]],
    nowcerts_insured_to_folder: dict[str, str],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []

    for pol in policies:
        insured_id = safe_str(pol.get("insuredDatabaseId"))
        folder_id = nowcerts_insured_to_folder.get(insured_id or "")

        if not folder_id:
            logger.warning("Policy %s — no insurance_folder for insuredId=%s, skipping", pol.get("databaseId"), insured_id)
            continue

        # lineOfBusinesses is a list of objects with lineOfBusinessName key
        lob_raw = pol.get("lineOfBusinesses") or []
        coverages: list[str] = []
        if isinstance(lob_raw, list):
            for item in lob_raw:
                if isinstance(item, dict):
                    name = safe_str(item.get("lineOfBusinessName") or item.get("name"))
                    if name:
                        coverages.append(name)
                elif isinstance(item, str) and item.strip():
                    coverages.append(item.strip())

        policy_number = safe_str(pol.get("number"))  # not policyNumber

        record: dict[str, Any] = {
            "folder_id": folder_id,
            "carrier_name": safe_str(pol.get("carrierName")),
            "mga": safe_str(pol.get("mgaName")),              # not mga
            "policy_number": policy_number,
            "quote_id": policy_number,                         # per spec: quote_id = policy_number
            "coverages": coverages if coverages else None,
            "premium": safe_float(pol.get("totalPremium")),
            "policy_fee_taxes": safe_float(pol.get("totalNonPremium")),
            "agency_fees": safe_float(pol.get("totalAgencyCommission")),
            "effective_date": parse_date(pol.get("effectiveDate")),
            "expiration_date": parse_date(pol.get("expirationDate")),
            "binder_date": parse_date(pol.get("bindDate")),
            "status": "active",
            "org_id": TARGET_ORG_ID or None,
            "_nowcerts_policy_id": safe_str(pol.get("databaseId")),
        }
        result.append(record)

    logger.info("Transformed %d insurance_folder_carriers", len(result))
    return result
