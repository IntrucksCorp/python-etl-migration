"""
HTTP client for the Nowcerts OData API.

Authentication:
  - POST /api/Token  (grant_type=password) → access_token (Bearer)
  - Token is renewed automatically on 401.
  - Alternatively set NOWCERTS_ACCESS_TOKEN in .env to skip login.

Pagination:
  GET /<endpoint>?$top=<PAGE_SIZE>&$skip=<offset>&$orderby=changeDate
"""
from __future__ import annotations

import os
import time
from datetime import datetime, timedelta
from typing import Any, Generator, Optional

import requests

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
        self._base = NOWCERTS_API_BASE_URL.rstrip("/")
        self._username = NOWCERTS_USERNAME
        self._password = NOWCERTS_PASSWORD
        self._token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        self._session = requests.Session()
        self._session.headers.update({"Accept": "application/json"})

        # Allow injecting a pre-generated token via env (skips login)
        manual_token = os.getenv("NOWCERTS_ACCESS_TOKEN")
        if manual_token:
            self._token = manual_token
            self._token_expiry = datetime.now() + timedelta(days=365)
            self._session.headers.update({"Authorization": f"Bearer {self._token}"})
            logger.info("Using manual NOWCERTS_ACCESS_TOKEN from environment")
        else:
            logger.info("No manual token — will authenticate via /api/Token")

    # ── Authentication ────────────────────────────────────────

    def _login(self) -> None:
        login_url = f"{self._base}/Token"
        payload = {
            "grant_type": "password",
            "username": self._username,
            "password": self._password,
        }
        for attempt in range(1, 4):
            logger.info("Login attempt %d/3 → %s", attempt, login_url)
            try:
                resp = requests.post(login_url, data=payload, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    self._token = data["access_token"]
                    expires_in = int(data.get("expires_in", 3600))
                    self._token_expiry = datetime.now() + timedelta(seconds=expires_in - 300)
                    self._session.headers.update({"Authorization": f"Bearer {self._token}"})
                    logger.info("Login successful for %s", self._username)
                    return
                elif resp.status_code == 400:
                    raise ValueError(f"Invalid Nowcerts credentials: {resp.text}")
                else:
                    logger.warning("Login failed (%d): %s", resp.status_code, resp.text)
                    time.sleep(5 * attempt)
            except ValueError:
                raise
            except Exception as exc:
                logger.warning("Login error on attempt %d: %s", attempt, exc)
                time.sleep(5 * attempt)

        raise RuntimeError("Could not authenticate with Nowcerts after 3 attempts")

    def _ensure_token(self) -> None:
        if not self._token or not self._token_expiry or datetime.now() >= self._token_expiry:
            if not self._username or not self._password:
                raise ValueError("No Nowcerts credentials configured and no NOWCERTS_ACCESS_TOKEN set")
            self._login()

    # ── HTTP ──────────────────────────────────────────────────

    def _get(self, endpoint: str, params: dict) -> dict:
        self._ensure_token()
        url = f"{self._base}/{endpoint}"

        for attempt in range(1, 4):
            try:
                resp = self._session.get(url, params=params, timeout=30)

                if resp.status_code == 401:
                    logger.warning("Token expired (401) — re-authenticating")
                    self._login()
                    continue

                if resp.status_code == 429:
                    logger.warning("Rate limited (429) — waiting 60s")
                    time.sleep(60)
                    continue

                resp.raise_for_status()
                return resp.json()

            except requests.exceptions.Timeout:
                wait = attempt * 10
                logger.warning("Timeout on %s (attempt %d) — retrying in %ds", endpoint, attempt, wait)
                time.sleep(wait)

        raise RuntimeError(f"Failed to GET {endpoint} after 3 attempts")

    # ── Pagination ────────────────────────────────────────────

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
