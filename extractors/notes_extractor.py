from __future__ import annotations

from typing import Any

from extractors.nowcerts_client import NowcertsClient
from utils.logger import get_logger

logger = get_logger(__name__)


def extract_notes(client: NowcertsClient) -> list[dict[str, Any]]:
    """NotesList → activities table (subject + description)."""
    logger.info("Extracting NotesList…")
    return list(client.fetch_all("NotesList"))
