from __future__ import annotations

from extractors.nowcerts_client import NowcertsClient
from extractors.notes_extractor import extract_notes
from transformers.activities_transformer import transform_activities
from loaders.supabase_loader import insert_activities
from utils.logger import get_logger

logger = get_logger(__name__)


def run(client: NowcertsClient, profile_id_map: dict[str, str]) -> None:
    logger.info("=== PIPELINE: activities ===")
    raw = extract_notes(client)
    transformed = transform_activities(raw, profile_id_map)
    insert_activities(transformed)
    logger.info("activities pipeline done")
