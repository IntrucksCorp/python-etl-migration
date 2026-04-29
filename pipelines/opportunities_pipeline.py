from __future__ import annotations

from extractors.nowcerts_client import NowcertsClient
from extractors.opportunity_extractor import extract_opportunities
from transformers.opportunities_transformer import transform_opportunities
from loaders.supabase_loader import insert_opportunities
from utils.logger import get_logger

logger = get_logger(__name__)


def run(client: NowcertsClient, profile_id_map: dict[str, str]) -> None:
    logger.info("=== PIPELINE: opportunities ===")
    raw = extract_opportunities(client)
    transformed = transform_opportunities(raw, profile_id_map)
    insert_opportunities(transformed)
    logger.info("opportunities pipeline done")
