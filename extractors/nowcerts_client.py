"""
HTTP client for the Nowcerts OData API.

All endpoints use query params:
  $top=<PAGE_SIZE>&$skip=<offset>&$orderby=changeDate
Authentication: HTTP Basic (username / password).
"""
from __future__ import annotations

import time
from typing import Any, Generator

import requests
from requests.auth import HTTPBasicAuth
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import (
    NOWCERTS_API_BASE_URL,
    NOWCERTS_PASSWORD,
    NOWCERTS_USERNAME,
    PAGE_SIZE,
    REQUEST_DELAY,
)
from utils.logger import get_logger

logger = get_logger(__name__)


class NowcertsClient:
    def __init__(self) -> None:
        self._auth = HTTPBasicAuth(NOWCERTS_USERNAME, NOWCERTS_PASSWORD)
        self._base = NOWCERTS_API_BASE_URL.rstrip("/")
        self._session = requests.Session()
        self._session.auth = self._auth
        self._session.headers.update({"Accept": "application/json"})

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _get(self, endpoint: str, params: dict) -> dict:
        url = f"{self._base}/{endpoint}"
        response = self._session.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    def fetch_all(
        self,
        endpoint: str,
        order_by: str = "changeDate",
        extra_params: dict | None = None,
    ) -> Generator[dict[str, Any], None, None]:
        """Paginate through all records of an endpoint, yielding each record."""
        skip = 0
        fetched = 0

        while True:
            params: dict[str, Any] = {
                "$top": PAGE_SIZE,
                "$skip": skip,
                "$orderby": order_by,
            }
            if extra_params:
                params.update(extra_params)

            logger.debug("GET %s  skip=%d  top=%d", endpoint, skip, PAGE_SIZE)
            data = self._get(endpoint, params)

            records: list[dict] = data.get("value", [])
            if not records:
                break

            for record in records:
                yield record

            fetched += len(records)
            logger.info("%s — fetched %d so far", endpoint, fetched)

            if len(records) < PAGE_SIZE:
                break

            skip += PAGE_SIZE
            time.sleep(REQUEST_DELAY)
