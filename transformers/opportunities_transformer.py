"""
Maps Nowcerts OpportunitiesList → Supabase `opportunities` table.

Verified field names from inspection:
  id                    → _nowcerts_id
  insuredDatabaseId     → FK to profile
  createdFromRenewal    → is_renewal   (not isRenewal)
  neededBy              → needed_by_date  (not neededByDate)
  opportunityStageName  → status (mapped to enum)
  agencyCommission      → commission_estimate
  description           → notes
  lineOfBusinessName    → line_of_business (single string, not array)
  assignedTo            → list of strings — no UUID available, left null
"""
from __future__ import annotations

from typing import Any

from config.settings import TARGET_ORG_ID
from utils.helpers import safe_str, safe_bool, safe_float, parse_date
from utils.logger import get_logger

logger = get_logger(__name__)

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
            logger.warning("Opportunity %s — no matching profile, skipping", opp.get("id"))
            continue

        # lineOfBusinessName is a single string in OpportunitiesList
        lob = safe_str(opp.get("lineOfBusinessName"))
        line_of_business = [lob] if lob else None

        record: dict[str, Any] = {
            "is_renewal": safe_bool(opp.get("createdFromRenewal")) or False,
            "needed_by_date": parse_date(opp.get("neededBy")),          # not neededByDate
            "status": _map_stage(opp.get("opportunityStageName")),      # not opportunityStage
            "commission_estimate": safe_float(opp.get("agencyCommission")),
            "line_of_business": line_of_business,
            "notes": safe_str(opp.get("description")),
            "assigned_agent_id": None,  # assignedTo is list of names, no UUID available
            "org_id": TARGET_ORG_ID or None,
            "_profile_id": profile_id,
            "_nowcerts_id": safe_str(opp.get("id")),
        }
        result.append(record)

    logger.info("Transformed %d opportunities", len(result))
    return result
