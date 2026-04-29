"""
Extracts vehicle data from VehicleList.
In Nowcerts, trucks and trailers are stored together;
the transformer is responsible for separating them.
"""
from __future__ import annotations

from typing import Any

from extractors.nowcerts_client import NowcertsClient
from utils.logger import get_logger

logger = get_logger(__name__)


def extract_vehicles(client: NowcertsClient) -> list[dict[str, Any]]:
    logger.info("Extracting VehicleList…")
    return list(client.fetch_all("VehicleList"))
