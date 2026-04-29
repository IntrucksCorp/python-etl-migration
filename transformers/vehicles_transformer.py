"""
Maps Nowcerts VehicleList → Supabase `vehicles` table.

Verified field names from inspection:
  id                → _nowcerts_id
  insuredDatabaseId → FK to profile
  type              → vehicle type code (e.g. "TKTR")
  typeDescription   → human label (e.g. "Truck Tractor")
  make, model, vin, year, value → direct mapping
  vehicleWeight     → NOT in endpoint; gvw left null
  status            → hardcoded 'active' (no field in Nowcerts)

Trailer detection: typeDescription contains "Trailer" or type starts with "TRL".
"""
from __future__ import annotations

from typing import Any

from config.settings import TARGET_ORG_ID
from utils.helpers import safe_str, safe_int, safe_float
from utils.logger import get_logger

logger = get_logger(__name__)


def _is_trailer(type_code: str | None, type_desc: str | None) -> bool:
    if type_desc and "trailer" in type_desc.lower():
        return True
    if type_code and type_code.upper().startswith("TRL"):
        return True
    return False


def transform_vehicles(
    vehicles: list[dict[str, Any]],
    nowcerts_to_supabase_profile: dict[str, str],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []

    for v in vehicles:
        insured_id = safe_str(v.get("insuredDatabaseId"))
        profile_id = nowcerts_to_supabase_profile.get(insured_id or "")

        if not profile_id:
            logger.warning("Vehicle %s — no matching profile for insuredId=%s, skipping", v.get("id"), insured_id)
            continue

        type_code = safe_str(v.get("type"))
        type_desc = safe_str(v.get("typeDescription"))

        # value comes as string ("15000") in the API
        value_raw = v.get("value")
        value = safe_float(value_raw)

        record: dict[str, Any] = {
            "year": safe_int(v.get("year")),
            "type": type_desc or type_code,  # prefer human-readable description
            "make": safe_str(v.get("make")),
            "model": safe_str(v.get("model")),
            "vin": safe_str(v.get("vin")),
            "gvw": None,  # vehicleWeight not available in VehicleList endpoint
            "value": value,
            "status": "active",
            "org_id": TARGET_ORG_ID or None,
            "_profile_id": profile_id,
            "_nowcerts_id": safe_str(v.get("id")),
            "_is_trailer": _is_trailer(type_code, type_desc),
        }
        result.append(record)

    logger.info("Transformed %d vehicles (%d trailers)", len(result), sum(1 for r in result if r["_is_trailer"]))
    return result
