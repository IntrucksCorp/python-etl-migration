"""
Maps Nowcerts OpportunitiesList → Supabase `opportunities` table.

Field mapping:
  isRenewal          → is_renewal       (bool; if no renewal checkbox → new sale)
  neededByDate       → needed_by_date   (date)
  opportunityStage   → status           (mapped to enum)
  agencyCommission   → commission_estimate (float)
  assignedTo         → assigned_agent_id  (lookup needed post-migration)
  description        → notes             (vigencia de la póliza)
  lineOfBusiness     → line_of_business  (array strings)
"""
from __future__ import annotations

from typing import Any

from config.settings import TARGET_ORG_ID
from utils.helpers import safe_str, safe_bool, safe_float, parse_date
from utils.logger import get_logger

logger = get_logger(__name__)

# Map Nowcerts opportunity stage → Trucker status enum
_STAGE_MAP: dict[str, str] = {
    "new": "prospect",
    "contacted": "open",
    "documentation": "documentation",
    "qualification": "qualification",
    "submit for quote": "submit_for_quote",
    "waiting for quote": "waiting_for_quote",
    "in negotiation": "in_negotiation",
    "closed": "closed",
    "closed won": "closed_won",
    "won": "closed_won",
    "closed lost": "closed_lost",
    "lost": "closed_lost",
}

_DEFAULT_STATUS = "open"


def _map_stage(stage: str | None) -> str:
    if not stage:
        return _DEFAULT_STATUS
    return _STAGE_MAP.get(stage.strip().lower(), _DEFAULT_STATUS)


def transform_opportunities(
    opportunities: list[dict[str, Any]],
    nowcerts_to_supabase_profile: dict[str, str],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []

    for opp in opportunities:
        insured_id = safe_str(opp.get("insuredDatabaseId"))
        profile_id = nowcerts_to_supabase_profile.get(insured_id or "")

        if not profile_id:
            logger.warning("Opportunity %s — no matching profile, skipping", opp.get("databaseId"))
            continue

        is_renewal = safe_bool(opp.get("isRenewal"))

        lob_raw = opp.get("lineOfBusiness")
        line_of_business: list[str] = []
        if isinstance(lob_raw, list):
            line_of_business = [safe_str(x) for x in lob_raw if x]
        elif isinstance(lob_raw, str) and lob_raw.strip():
            line_of_business = [lob_raw.strip()]

        record: dict[str, Any] = {
            "is_renewal": is_renewal if is_renewal is not None else False,
            "needed_by_date": parse_date(opp.get("neededByDate") or opp.get("effectiveDate")),
            "status": _map_stage(opp.get("opportunityStage")),
            "commission_estimate": safe_float(opp.get("agencyCommission")),
            "line_of_business": line_of_business if line_of_business else None,
            "notes": safe_str(opp.get("description")),
            "org_id": TARGET_ORG_ID or None,
            # relationships
            "_profile_id": profile_id,
            "_nowcerts_id": safe_str(opp.get("databaseId")),
            # assigned_agent_id requires a separate agent lookup — left null for now
            "assigned_agent_id": None,
        }
        result.append(record)

    logger.info("Transformed %d opportunities", len(result))
    return result
