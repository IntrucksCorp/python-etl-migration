from __future__ import annotations

from typing import Any

from extractors.nowcerts_client import NowcertsClient
from utils.logger import get_logger

logger = get_logger(__name__)


def extract_drivers(client: NowcertsClient) -> list[dict[str, Any]]:
    logger.info("Extracting DriverList…")
    return list(client.fetch_all("DriverList"))
