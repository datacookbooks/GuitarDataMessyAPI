"""One-time repair for generated order history on Railway.

This script preserves the historical seed through 2025-08-28, deletes only
orders after that date, and regenerates those dates with the current
DailyDataGenerator.generate_daily_orders() logic.

It deliberately does NOT regenerate or modify vendor_bids.

Safe default: without --apply, it performs a dry run only.
"""

from __future__ import annotations

import argparse
import csv
import sqlite3
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np

from db_config import DATABASE_PATH, get_db_connection
from daily_generator import DailyDataGenerator


DEFAULT_SEED_END = date(2025, 8, 28)
DEFAULT_RANDOM_SEED = 20260807
ROOT_DIR = Path(__file__).resolve().parent
ORDERS_CSV = ROOT_DIR / "df_orders_messy.csv"


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table' AND name = ?
        LIMIT 1
        """,
        (table_name,),
    ).fetchone()
    return row is not None


def csv_max_date(csv_path: Path) -> date | None:
    if not csv_path.exists():
        return None

    latest: date | None = None

    with csv_path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)

        if not reader.fieldnames or "date" not in reader.fieldnames:
            raise RuntimeError(
                f"Expected a 'date' column in {csv_path}, but it was not found."
            )

        for row in reader:
            raw_date = (row.get("date") or "").strip()
            if not raw_date:
                continue

            current = parse_date(raw_date)
            if latest is None or current > latest:
                latest = current

    return latest


def collect_stats(conn: sqlite3.Connection, seed_end: date) -> dict:
    cutoff = seed_end.isoformat()

    order_stats = conn.execute(
        """
        SELECT
            COUNT(*) AS total_rows,
            SUM(CASE WHEN date <= ? THEN 1 ELSE 0 END) AS seed_rows,
            SUM(CASE WHEN date > ? THEN 1 ELSE 0 END) AS generated_rows,
            MIN(date) AS min_date,
            MAX(date) AS max_date,
            COUNT(DISTINCT date) AS distinct_dates
        FROM orders
        """,
        (cutoff, cutoff),
    ).fetchone()

    bid_stats = conn.execute(
        """
        SELECT
            COUNT(*) AS total_rows,
            MIN(date) AS min_date,
            MAX(date) AS max_date
        FROM vendor_bids
        """
    ).fetchone()

    return {
        "orders_total": int(order_stats["total_rows"] or 0),
        "orders_seed": int(order_stats["seed_rows"] or 0),
        "orders_generated": int(order_stats["generated_rows"] or 0),
        "orders_min_date": order_stats["min_date"],
        "orders_max_date": order_stats["max_date"],
        "orders_distinct_dates": int(order_stats["distinct_dates"] or 0),
        "vendor_bids_total": int(bid_stats["total_rows"] or 0),
        "vendor_bids_min_date": bid_stats["min_date"],
        "vendor_bids_max_date": bid_stats["max_date"],
    }


def create_backup(database_path: Path) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = database_path.with_name(
        f"{database_path.stem}_before_order_regen_{timestamp}{database_path.suffix}"
    )

    source = sqlite3.connect(str(database_path), timeout=30)
    destination = sqlite3.connect(str(backup_path), timeout=30)

    try:
        source.backup(destination)
    finally:
        destination.close()
        source.close()

    return backup_path


def print_stats(title: str, stats: dict) -> None:
    print(f"\n{title}")
    print("-" * len(title))
    print(f"Orders total rows:        {stats['orders_total']}")
    print(f"Seed rows preserved:      {stats['orders_seed']}")
    print(f"Post-seed order rows:     {stats['orders_generated']}")
    print(f"Orders date range:        {stats['orders_min_date']} -> {stats['orders_max_date']}")
    print(f"Order dates represented:  {stats['orders_distinct_dates']}")
    print(f"Vendor-bid rows:          {stats['vendor_bids_total']}")
    print(f"Vendor-bid date range:    {stats['vendor_bids_min_date']} -> {stats['vendor_bids_max_date']}")


def validate_database(seed_end: date) -> dict:
    if not DATABASE_PATH.exists():
        raise RuntimeError(
            "Database file does not exist at the configured path:\n"
            f"  {DATABASE_PATH}\n"
            "Aborting rather than creating a new empty database."
        )

    conn = get_db_connection()

    try:
        if not table_exists(conn, "orders"):
            raise RuntimeError("The configured database does not contain an 'orders' table.")

        if not table_exists(conn, "vendor_bids"):
            raise RuntimeError(
                "The configured database does not contain a 'vendor_bids' table."
            )

        stats = collect_stats(conn, seed_end)
    finally:
        conn.close()

    if stats["orders_seed"] <= 0:
        raise RuntimeError(
            "No order rows exist on or before the seed cutoff. "
            "Refusing to continue because the historical seed may be missing."
        )

    return stats


def verify_regeneration(seed_end: date, today: date, vendor_bids_before: int) -> dict:
    conn = get_db_connection()

    try:
        stats = collect_stats(conn, seed_end)

        date_stats = conn.execute(
            """
            SELECT
                COUNT(DISTINCT date) AS distinct_dates,
                MIN(date) AS min_date,
                MAX(date) AS max_date
            FROM orders
            WHERE date > ? AND date <= ?
            """,
            (seed_end.isoformat(), today.isoformat()),
        ).fetchone()
    finally:
        conn.close()

    expected_dates = (today - seed_end).days
    actual_dates = int(date_stats["distinct_dates"] or 0)

    if actual_dates != expected_dates:
        raise RuntimeError(
            "Regeneration finished, but the regenerated date count is unexpected: "
            f"expected {expected_dates}, found {actual_dates}."
        )

    if date_stats["max_date"] != today.isoformat():
        raise RuntimeError(
            "Regeneration did not reach today. "
            f"Latest regenerated date: {date_stats['max_date']}"
        )

    if stats["vendor_bids_total"] != vendor_bids_before:
        raise RuntimeError(
            "Vendor-bid row count changed unexpectedly. "
            "The regeneration script is designed not to modify vendor_bids."
        )

    return stats


def regenerate_orders(seed_end: date, random_seed: int) -> dict:
    today = datetime.now(timezone.utc).date()
    regen_start = seed_end + timedelta(days=1)

    if regen_start > today:
        raise RuntimeError(
            f"Regeneration start {regen_start} is after today {today}."
        )

    np.random.seed(random_seed)

    conn = get_db_connection()
    try:
        cursor = conn.execute(
            "DELETE FROM orders WHERE date > ?",
            (seed_end.isoformat(),),
        )
        deleted_rows = cursor.rowcount
        conn.commit()
    finally:
        conn.close()

    print(f"\nDeleted {deleted_rows} post-seed order rows.")
    print(
        f"Regenerating orders from {regen_start.isoformat()} "
        f"through {today.isoformat()}...\n"
    )

    generator = DailyDataGenerator()
    current = regen_start
    unique_orders_added = 0
    dates_generated = 0

    while current <= today:
        added = generator.generate_daily_orders(current)
        unique_orders_added += added
        dates_generated += 1
        current += timedelta(days=1)

    return {
        "deleted_rows": deleted_rows,
        "dates_generated": dates_generated,
        "unique_orders_added": unique_orders_added,
        "start_date": regen_start.isoformat(),
        "end_date": today.isoformat(),
        "today": today,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Safely regenerate only post-seed orders using the current "
            "daily_generator.py logic. Dry-run by default."
        )
    )

    parser.add_argument(
        "--seed-end",
        default=DEFAULT_SEED_END.isoformat(),
        help=(
            "Last date belonging to the historical seed. "
            f"Default: {DEFAULT_SEED_END.isoformat()}"
        ),
    )

    parser.add_argument(
        "--random-seed",
        type=int,
        default=DEFAULT_RANDOM_SEED,
        help=(
            "NumPy random seed for reproducible one-time regeneration. "
            f"Default: {DEFAULT_RANDOM_SEED}"
        ),
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually delete and regenerate post-seed orders.",
    )

    args = parser.parse_args()
    seed_end = parse_date(args.seed_end)

    print("Order-history regeneration")
    print("==========================")
    print(f"Configured database:      {DATABASE_PATH}")
    print(f"Historical seed cutoff:   {seed_end.isoformat()}")
    print(f"Random seed:              {args.random_seed}")

    csv_end = csv_max_date(ORDERS_CSV)
    if csv_end is not None:
        print(f"Seed CSV latest date:      {csv_end.isoformat()}")
        if csv_end != seed_end:
            raise RuntimeError(
                "The seed CSV's latest date does not match --seed-end. "
                "Refusing to continue until the cutoff is verified."
            )
    else:
        print(
            "Seed CSV latest date:      unavailable "
            "(CSV not found; database checks will still run)"
        )

    before = validate_database(seed_end)
    print_stats("Current database state", before)

    if before["orders_generated"] == 0:
        print(
            "\nThere are no post-seed orders to replace. "
            "No regeneration is necessary."
        )
        return

    if not args.apply:
        print(
            "\nDRY RUN ONLY — nothing was changed.\n"
            f"Running with --apply would preserve every order through "
            f"{seed_end.isoformat()}, delete {before['orders_generated']} "
            "post-seed order rows, create a full SQLite backup, and then "
            "regenerate orders through today using the current "
            "daily_generator.py. Vendor bids would not be modified."
        )
        return

    backup_path = create_backup(DATABASE_PATH)
    print(f"\nBackup created: {backup_path}")

    vendor_bids_before = before["vendor_bids_total"]

    result = regenerate_orders(
        seed_end=seed_end,
        random_seed=args.random_seed,
    )

    after = verify_regeneration(
        seed_end=seed_end,
        today=result["today"],
        vendor_bids_before=vendor_bids_before,
    )

    print_stats("Database state after regeneration", after)

    print("\nRegeneration complete")
    print("---------------------")
    print(f"Deleted raw order rows:    {result['deleted_rows']}")
    print(f"Dates regenerated:         {result['dates_generated']}")
    print(f"Unique orders generated:   {result['unique_orders_added']}")
    print(f"Regenerated range:         {result['start_date']} -> {result['end_date']}")
    print(f"Vendor-bid rows unchanged: {vendor_bids_before}")
    print(f"Backup retained at:        {backup_path}")


if __name__ == "__main__":
    main()
