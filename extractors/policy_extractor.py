from __future__ import annotations

from typing import Any

from extractors.nowcerts_client import NowcertsClient
from utils.logger import get_logger

logger = get_logger(__name__)


def extract_policies(client: NowcertsClient) -> list[dict[str, Any]]:
    logger.info("Extracting PolicyDetailList…")
    return list(client.fetch_all("PolicyDetailList"))


def extract_motor_truck_details(client: NowcertsClient) -> list[dict[str, Any]]:
    """Commodities Hauled & Revenue % — stored in MotorTruckDetailList."""
    logger.info("Extracting MotorTruckDetailList…")
    return list(client.fetch_all("MotorTruckDetailList"))


def extract_cl_commercial_auto(client: NowcertsClient) -> list[dict[str, Any]]:
    """Commercial auto coverage limits detail."""
    logger.info("Extracting CLCommercialAutoRatingDetailList…")
    return list(client.fetch_all("CLCommercialAutoRatingDetailList"))


def extract_endorsement_details(client: NowcertsClient) -> list[dict[str, Any]]:
    logger.info("Extracting PolicyEndorsementDetailList…")
    return list(client.fetch_all("PolicyEndorsementDetailList"))
