from __future__ import annotations

from extractors.nowcerts_client import NowcertsClient
from extractors.tasks_extractor import extract_tasks
from transformers.cases_transformer import transform_cases
from loaders.supabase_loader import insert_cases
from utils.logger import get_logger

logger = get_logger(__name__)


def run(client: NowcertsClient, profile_id_map: dict[str, str]) -> None:
    logger.info("=== PIPELINE: cases ===")
    raw = extract_tasks(client)
    transformed = transform_cases(raw, profile_id_map)
    insert_cases(transformed)
    logger.info("cases pipeline done")
