"""
Maps Nowcerts PolicyDetailList → Supabase `insurance_folder_carriers` table.

One carrier record per policy.

Field mapping:
  carrierName        → carrier_name
  mga                → mga
  policyNumber       → policy_number
  lineOfBusiness     → coverages   (text[])
  premium            → premium
  effectiveDate      → effective_date
  expirationDate     → expiration_date
  bindDate           → binder_date
  taxesAndFees       → policy_fee_taxes
  agencyFees         → agency_fees
  Quote ID (Vendido) → quote_id = policy_number (per spec)
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
    """
    nowcerts_insured_to_folder: {nowcerts_insuredDatabaseId → supabase insurance_folder UUID}
    """
    result: list[dict[str, Any]] = []

    for pol in policies:
        insured_id = safe_str(pol.get("insuredDatabaseId"))
        folder_id = nowcerts_insured_to_folder.get(insured_id or "")

        if not folder_id:
            logger.warning("Policy %s — no insurance_folder for insuredId=%s, skipping", pol.get("databaseId"), insured_id)
            continue

        lob_raw = pol.get("lineOfBusiness")
        coverages: list[str] = []
        if isinstance(lob_raw, list):
            coverages = [safe_str(x) for x in lob_raw if x]
        elif isinstance(lob_raw, str) and lob_raw.strip():
            coverages = [lob_raw.strip()]

        policy_number = safe_str(pol.get("policyNumber"))

        record: dict[str, Any] = {
            "folder_id": folder_id,
            "carrier_name": safe_str(pol.get("carrierName")),
            "mga": safe_str(pol.get("mga")),
            "policy_number": policy_number,
            # quote_id → policy_number per migration spec
            "quote_id": policy_number,
            "coverages": coverages if coverages else None,
            "premium": safe_float(pol.get("premium")),
            "policy_fee_taxes": safe_float(pol.get("taxesAndFees")),
            "agency_fees": safe_float(pol.get("agencyFees")),
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
