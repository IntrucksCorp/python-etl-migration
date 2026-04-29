"""
Extracts insured (client) data from:
  - InsuredList       → main profile fields
  - InsuredLocationList → address fields (linked by insuredDatabaseId)
"""
from __future__ import annotations

from typing import Any

from extractors.nowcerts_client import NowcertsClient
from utils.logger import get_logger

logger = get_logger(__name__)


def extract_insureds(client: NowcertsClient) -> list[dict[str, Any]]:
    logger.info("Extracting InsuredList…")
    return list(client.fetch_all("InsuredList"))


def extract_insured_locations(client: NowcertsClient) -> list[dict[str, Any]]:
    logger.info("Extracting InsuredLocationList…")
    return list(client.fetch_all("InsuredLocationList"))


def extract_insured_details(client: NowcertsClient) -> list[dict[str, Any]]:
    logger.info("Extracting InsuredDetailList…")
    return list(client.fetch_all("InsuredDetailList"))
