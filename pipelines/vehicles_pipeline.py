from __future__ import annotations

from extractors.nowcerts_client import NowcertsClient
from extractors.vehicle_extractor import extract_vehicles
from transformers.vehicles_transformer import transform_vehicles
from loaders.supabase_loader import insert_vehicles
from utils.logger import get_logger

logger = get_logger(__name__)


def run(client: NowcertsClient, profile_id_map: dict[str, str]) -> None:
    logger.info("=== PIPELINE: vehicles ===")
    raw = extract_vehicles(client)
    transformed = transform_vehicles(raw, profile_id_map)
    insert_vehicles(transformed)
    logger.info("vehicles pipeline done")
