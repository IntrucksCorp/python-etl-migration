"""
Pipeline for insurance_folders AND insurance_folder_carriers (they depend on each other).

Returns:
  - nowcerts_insured_to_folder: {nowcerts_insured_id → supabase folder UUID}
  - nowcerts_policy_to_carrier: {nowcerts_policy_id → supabase carrier UUID}
"""
from __future__ import annotations

from extractors.nowcerts_client import NowcertsClient
from extractors.insured_extractor import extract_insureds
from extractors.policy_extractor import extract_policies, extract_endorsement_details
from transformers.insurance_folders_transformer import transform_insurance_folders
from transformers.insurance_folder_carriers_transformer import transform_insurance_folder_carriers
from loaders.supabase_loader import insert_insurance_folders, insert_insurance_folder_carriers
from utils.helpers import safe_str
from utils.logger import get_logger

logger = get_logger(__name__)


def run(
    client: NowcertsClient,
    profile_id_map: dict[str, str],
) -> tuple[dict[str, str], dict[str, str]]:
    logger.info("=== PIPELINE: insurance_folders ===")

    insureds = extract_insureds(client)
    policies = extract_policies(client)

    # ── insurance_folders ──────────────────────────────────────
    folders_transformed = transform_insurance_folders(insureds, policies, profile_id_map)
    folders_inserted = insert_insurance_folders(folders_transformed)

    insured_to_folder: dict[str, str] = {}
    for original, row in zip(folders_transformed, folders_inserted):
        nowcerts_insured_id = original.get("_nowcerts_insured_id")
        folder_uuid = row.get("id")
        if nowcerts_insured_id and folder_uuid:
            insured_to_folder[nowcerts_insured_id] = folder_uuid

    # ── insurance_folder_carriers ──────────────────────────────
    logger.info("=== PIPELINE: insurance_folder_carriers ===")
    carriers_transformed = transform_insurance_folder_carriers(policies, insured_to_folder)
    carriers_inserted = insert_insurance_folder_carriers(carriers_transformed)

    policy_to_carrier: dict[str, str] = {}
    for original, row in zip(carriers_transformed, carriers_inserted):
        nowcerts_pid = original.get("_nowcerts_policy_id")
        carrier_uuid = row.get("id")
        if nowcerts_pid and carrier_uuid:
            policy_to_carrier[nowcerts_pid] = carrier_uuid

    logger.info("insurance_folders pipeline done — %d folders, %d carriers", len(insured_to_folder), len(policy_to_carrier))
    return insured_to_folder, policy_to_carrier
