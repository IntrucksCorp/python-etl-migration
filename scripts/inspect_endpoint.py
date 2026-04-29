"""
Inspects one or more Nowcerts endpoints and prints field names, types, and sample values.
Useful to verify field names before running the full migration.

Usage:
  python scripts/inspect_endpoint.py InsuredList
  python scripts/inspect_endpoint.py InsuredList VehicleList DriverList
  python scripts/inspect_endpoint.py --all
"""
from __future__ import annotations

import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from extractors.nowcerts_client import NowcertsClient
from utils.logger import get_logger

logger = get_logger("inspect")

ALL_ENDPOINTS = [
    "InsuredList",
    "InsuredLocationList",
    "VehicleList",
    "DriverList",
    "PolicyDetailList",
    "OpportunitiesList",
    "MotorTruckDetailList",
    "CLCommercialAutoRatingDetailList",
    "NotesList",
    "TasksList",
    "PolicyEndorsementDetailList",
]


def inspect(client: NowcertsClient, endpoint: str, sample_count: int = 2) -> None:
    print(f"\n{'═' * 60}")
    print(f"  ENDPOINT: {endpoint}")
    print(f"{'═' * 60}")

    records: list[dict] = []
    try:
        for i, record in enumerate(client.fetch_all(endpoint)):
            records.append(record)
            if i + 1 >= sample_count:
                break
    except Exception as exc:
        print(f"  ERROR fetching {endpoint}: {exc}")
        return

    if not records:
        print("  No records returned.")
        return

    # Aggregate all keys across sample records
    all_keys: dict[str, set] = {}
    for rec in records:
        for key, val in rec.items():
            all_keys.setdefault(key, set()).add(type(val).__name__)

    print(f"  Total fields: {len(all_keys)}")
    print(f"  Sample size:  {len(records)} record(s)\n")
    print(f"  {'FIELD':<45} {'TYPE(S)':<20} SAMPLE VALUE")
    print(f"  {'-'*45} {'-'*20} {'-'*30}")

    first = records[0]
    for key in sorted(all_keys.keys()):
        types = ", ".join(sorted(all_keys[key]))
        raw_val = first.get(key)
        # Truncate long values for display
        if isinstance(raw_val, (dict, list)):
            sample = json.dumps(raw_val, ensure_ascii=False)[:60]
        else:
            sample = str(raw_val)[:60] if raw_val is not None else "null"
        print(f"  {key:<45} {types:<20} {sample}")

    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect Nowcerts endpoint field structure")
    parser.add_argument(
        "endpoints",
        nargs="*",
        help="Endpoint name(s) to inspect (e.g. InsuredList VehicleList)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Inspect all known migration endpoints",
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=2,
        help="Number of sample records to fetch per endpoint (default: 2)",
    )
    args = parser.parse_args()

    targets = ALL_ENDPOINTS if args.all else args.endpoints
    if not targets:
        parser.print_help()
        sys.exit(1)

    client = NowcertsClient()
    for endpoint in targets:
        inspect(client, endpoint, sample_count=args.sample)

    print("Inspection complete.")


if __name__ == "__main__":
    main()
