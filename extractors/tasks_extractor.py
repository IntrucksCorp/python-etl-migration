from __future__ import annotations

from typing import Any

from extractors.nowcerts_client import NowcertsClient
from utils.logger import get_logger

logger = get_logger(__name__)


def extract_tasks(client: NowcertsClient) -> list[dict[str, Any]]:
    """TasksList → cases table."""
    logger.info("Extracting TasksList…")
    return list(client.fetch_all("TasksList"))
