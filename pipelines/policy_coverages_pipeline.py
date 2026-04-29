from __future__ import annotations

from extractors.nowcerts_client import NowcertsClient
from extractors.policy_extractor import extract_policies, extract_cl_commercial_auto
from transformers.policy_coverages_transformer import transform_policy_coverages
from loaders.supabase_loader import insert_policy_coverages
from utils.logger import get_logger

logger = get_logger(__name__)


def run(
    client: NowcertsClient,
    nowcerts_policy_to_carrier: dict[str, str],
) -> None:
    logger.info("=== PIPELINE: policy_coverages ===")
    policies = extract_policies(client)
    cl_auto = extract_cl_commercial_auto(client)
    transformed = transform_policy_coverages(policies, cl_auto, nowcerts_policy_to_carrier)
    insert_policy_coverages(transformed)
    logger.info("policy_coverages pipeline done")
