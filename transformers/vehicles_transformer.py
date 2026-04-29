"""
Maps Nowcerts VehicleList → Supabase `vehicles` table.

Important: In Nowcerts, trucks AND trailers are stored together in VehicleList.
The `vehicleType` field is used to separate them.
Trucker (new CRM) stores them in different sections but the same `vehicles` table
using the `type` column.

Field mapping:
  VehicleList.year          → year        (int)
  VehicleList.vehicleType   → type        (string)
  VehicleList.make          → make
  VehicleList.model         → model
  VehicleList.vin           → vin
  VehicleList.vehicleWeight → gvw         (numeric)
  VehicleList.value         → value       (numeric)
  VehicleList.vin           → vin
  status                    → 'active'    (hardcoded — Nowcerts lacks this field)
  titularidad               → NULL        (no equivalent in Nowcerts)
"""
from __future__ import annotations

from typing import Any

from config.settings import TARGET_ORG_ID
from utils.helpers import safe_str, safe_int, safe_float
from utils.logger import get_logger

logger = get_logger(__name__)

# Vehicle types considered trailers in Nowcerts
_TRAILER_KEYWORDS = {"trailer", "semi-trailer", "flatbed trailer", "reefer trailer", "dry van trailer"}


def _is_trailer(vehicle_type: str | None) -> bool:
    if not vehicle_type:
        return False
    return any(kw in vehicle_type.lower() for kw in _TRAILER_KEYWORDS)


def transform_vehicles(
    vehicles: list[dict[str, Any]],
    nowcerts_to_supabase_profile: dict[str, str],
) -> list[dict[str, Any]]:
    """
    nowcerts_to_supabase_profile: mapping {nowcerts_insured_id → supabase profile UUID}
    Vehicles without a matching profile are skipped with a warning.
    """
    result: list[dict[str, Any]] = []

    for v in vehicles:
        insured_id = safe_str(v.get("insuredDatabaseId"))
        profile_id = nowcerts_to_supabase_profile.get(insured_id or "")

        if not profile_id:
            logger.warning("Vehicle %s — no matching profile for insuredId=%s, skipping", v.get("databaseId"), insured_id)
            continue

        vtype = safe_str(v.get("vehicleType"))

        record: dict[str, Any] = {
            "year": safe_int(v.get("year")),
            "type": vtype,
            "make": safe_str(v.get("make")),
            "model": safe_str(v.get("model")),
            "vin": safe_str(v.get("vin")),
            "gvw": safe_float(v.get("vehicleWeight")),
            "value": safe_float(v.get("value")),
            "status": "active",
            # titularidad → NULL (no field in Nowcerts)
            "org_id": TARGET_ORG_ID or None,
            # relationships
            "_profile_id": profile_id,
            "_nowcerts_id": safe_str(v.get("databaseId")),
            "_is_trailer": _is_trailer(vtype),
        }
        result.append(record)

    logger.info("Transformed %d vehicles (%d trailers)", len(result), sum(1 for r in result if r["_is_trailer"]))
    return result
