"""
Pipeline: InsuredList + InsuredLocationList → profiles

Returns a dict mapping nowcerts_insured_id → supabase_profile_uuid
for downstream pipelines to resolve foreign keys.
"""
from __future__ import annotations

from extractors.nowcerts_client import NowcertsClient
from extractors.insured_extractor import extract_insureds, extract_insured_locations
from transformers.profiles_transformer import transform_profiles
from loaders.supabase_loader import insert_profiles
from utils.helpers import safe_str
from utils.logger import get_logger

logger = get_logger(__name__)


def run(client: NowcertsClient) -> dict[str, str]:
    logger.info("=== PIPELINE: profiles ===")

    insureds = extract_insureds(client)
    locations = extract_insured_locations(client)
    profiles = transform_profiles(insureds, locations)

    inserted = insert_profiles(profiles)

    # Build id mapping: _nowcerts_id → supabase uuid
    id_map: dict[str, str] = {}
    for original, row in zip(profiles, inserted):
        nowcerts_id = original.get("_nowcerts_id")
        supabase_id = row.get("id")
        if nowcerts_id and supabase_id:
            id_map[nowcerts_id] = supabase_id

    logger.info("profiles pipeline done — %d mapped", len(id_map))
    return id_map
