import argparse
from datetime import datetime, timezone

from database_setup import setup_database
from daily_generator import DailyDataGenerator


def main():

    parser = argparse.ArgumentParser(
        description="Backfill missing API data."
    )

    parser.add_argument(
        "--start",
        help="YYYY-MM-DD. If omitted, automatically resume after the latest data."
    )

    parser.add_argument(
        "--end",
        default=datetime.now(
            timezone.utc
        ).date().isoformat(),
        help="YYYY-MM-DD. Defaults to today.",
    )

    args = parser.parse_args()

    setup_database()

    generator = DailyDataGenerator()

    if args.start:

        result = generator.backfill(
            args.start,
            args.end
        )

    else:

        result = generator.backfill_through_today()

    print("\nBackfill complete:")

    for key, value in result.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
