from __future__ import annotations

from extractors.nowcerts_client import NowcertsClient
from extractors.driver_extractor import extract_drivers
from transformers.drivers_transformer import transform_drivers
from loaders.supabase_loader import insert_drivers
from utils.logger import get_logger

logger = get_logger(__name__)


def run(client: NowcertsClient, profile_id_map: dict[str, str]) -> None:
    logger.info("=== PIPELINE: drivers ===")
    raw = extract_drivers(client)
    transformed = transform_drivers(raw, profile_id_map)
    insert_drivers(transformed)
    logger.info("drivers pipeline done")
