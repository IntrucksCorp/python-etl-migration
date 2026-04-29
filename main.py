"""
ETL Migration — Nowcerts → Trucker (Supabase)

Execution order (respects foreign key dependencies):
  1. profiles              (InsuredList + InsuredLocationList)
  2. vehicles              (VehicleList)
  3. drivers               (DriverList)
  4. opportunities         (OpportunitiesList)
  5. insurance_folders     (InsuredList + PolicyDetailList)
  6. insurance_folder_carriers (PolicyDetailList)
  7. policy_coverages      (PolicyDetailList + CLCommercialAutoRatingDetailList)
  8. activities            (NotesList)
  9. cases                 (TasksList)

Usage:
  python main.py                   # run all pipelines
  python main.py --only profiles   # run a single pipeline
"""
from __future__ import annotations

import argparse
import sys

from extractors.nowcerts_client import NowcertsClient
import pipelines.profiles_pipeline as profiles_pl
import pipelines.vehicles_pipeline as vehicles_pl
import pipelines.drivers_pipeline as drivers_pl
import pipelines.opportunities_pipeline as opportunities_pl
import pipelines.insurance_folders_pipeline as folders_pl
import pipelines.policy_coverages_pipeline as coverages_pl
import pipelines.activities_pipeline as activities_pl
import pipelines.cases_pipeline as cases_pl

from utils.logger import get_logger

logger = get_logger("main")

PIPELINE_NAMES = [
    "profiles",
    "vehicles",
    "drivers",
    "opportunities",
    "insurance_folders",
    "policy_coverages",
    "activities",
    "cases",
]


def run_all(only: str | None = None) -> None:
    client = NowcertsClient()

    # ── 1. Profiles ────────────────────────────────────────────
    if not only or only == "profiles":
        profile_id_map = profiles_pl.run(client)
    else:
        profile_id_map = {}

    # ── 2. Vehicles ────────────────────────────────────────────
    if not only or only == "vehicles":
        vehicles_pl.run(client, profile_id_map)

    # ── 3. Drivers ─────────────────────────────────────────────
    if not only or only == "drivers":
        drivers_pl.run(client, profile_id_map)

    # ── 4. Opportunities ───────────────────────────────────────
    if not only or only == "opportunities":
        opportunities_pl.run(client, profile_id_map)

    # ── 5 & 6. Insurance Folders + Carriers ────────────────────
    policy_to_carrier: dict[str, str] = {}
    if not only or only == "insurance_folders":
        _, policy_to_carrier = folders_pl.run(client, profile_id_map)

    # ── 7. Policy Coverages ────────────────────────────────────
    if not only or only == "policy_coverages":
        coverages_pl.run(client, policy_to_carrier)

    # ── 8. Activities (Notes) ──────────────────────────────────
    if not only or only == "activities":
        activities_pl.run(client, profile_id_map)

    # ── 9. Cases (Tasks) ───────────────────────────────────────
    if not only or only == "cases":
        cases_pl.run(client, profile_id_map)

    logger.info("=== Migration complete ===")


def main() -> None:
    parser = argparse.ArgumentParser(description="Nowcerts → Supabase ETL migration")
    parser.add_argument(
        "--only",
        choices=PIPELINE_NAMES,
        help="Run only a specific pipeline",
    )
    args = parser.parse_args()
    run_all(only=args.only)


if __name__ == "__main__":
    main()
