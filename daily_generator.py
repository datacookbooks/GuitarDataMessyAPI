import numpy as np

from datetime import date, datetime, timedelta, timezone

from data_utils import make_messy_id, make_messy_vendor_id
from db_config import get_db_connection


def normalize_date(value):
    if value is None:
        return datetime.now(timezone.utc).date()

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    if isinstance(value, str):
        return datetime.strptime(
            value,
            "%Y-%m-%d"
        ).date()

    raise TypeError(
        "Date must be a date, datetime, YYYY-MM-DD string, or None."
    )


class DailyDataGenerator:

    def __init__(self):

        self.final_trends = {
            "orders": {
                "standard_prob": 0.4,
                "premium_prob": 0.5,
                "boutique_prob": 0.1,
                "age_mean": 36,
                "regional_probs": [
                    0.25,
                    0.15,
                    0.225,
                    0.20,
                    0.175,
                ],
            },

            "vendor_bids": {
                "vendor_1_maple_adjustment": 0.85,
                "vendor_1_mahogany_adjustment": 0.85,
                "vendor_2_maple_adjustment": 1.20,
                "vendor_2_rosewood_adjustment": 1.20,
                "vendor_2_mahogany_missing_prob": 0.30,
                "vendor_3_rosewood_adjustment": 0.88,
            },
        }


    def orders_exist_for_date(self, target_date):

        target_date = normalize_date(target_date)

        conn = get_db_connection()

        result = conn.execute(
            """
            SELECT 1
            FROM orders
            WHERE date = ?
            LIMIT 1
            """,
            (target_date.isoformat(),)
        ).fetchone()

        conn.close()

        return result is not None


    def vendor_bids_exist_for_date(self, target_date):

        target_date = normalize_date(target_date)

        conn = get_db_connection()

        result = conn.execute(
            """
            SELECT 1
            FROM vendor_bids
            WHERE date = ?
            LIMIT 1
            """,
            (target_date.isoformat(),)
        ).fetchone()

        conn.close()

        return result is not None


    def generate_daily_orders(self, target_date=None):

        target_date = normalize_date(target_date)

        if self.orders_exist_for_date(target_date):
            print(
                f"Orders already exist for {target_date}; skipping."
            )
            return 0

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT MAX(id_customer) FROM orders"
        )

        result = cursor.fetchone()[0]

        customer_id_counter = (
            result + 1
            if result is not None
            else 100000000
        )

        # Preserve original ongoing-data behavior.
        num_orders = int(np.random.randint(5, 8))

        trends = self.final_trends["orders"]

        for _ in range(num_orders):

            category = np.random.choice(
                ["standard", "premium", "boutique"],
                p=[
                    trends["standard_prob"],
                    trends["premium_prob"],
                    trends["boutique_prob"],
                ],
            )

            if category == "standard":
                id_model = np.random.choice([1, 2, 3])

            elif category == "premium":
                id_model = np.random.choice([4, 5, 6])

            else:
                id_model = np.random.choice([7, 8, 9])

            id_distributor = np.random.choice(
                [1, 2, 3, 4, 5],
                p=trends["regional_probs"],
            )

            messy_model = make_messy_id(
                id_model,
                is_distributor=False
            )

            messy_distributor = make_messy_id(
                id_distributor,
                is_distributor=True
            )

            random_hour = int(np.random.randint(0, 24))
            random_minute = int(np.random.randint(0, 60))
            random_second = int(np.random.randint(0, 60))

            order_datetime = datetime(
                target_date.year,
                target_date.month,
                target_date.day,
                random_hour,
                random_minute,
                random_second,
                tzinfo=timezone.utc,
            )

            unix_timestamp = str(
                int(order_datetime.timestamp())
            )

            age = max(
                18,
                int(
                    np.random.normal(
                        trends["age_mean"],
                        6
                    )
                ),
            )

            gender = (
                "M"
                if np.random.random() < 0.65
                else "F"
            )

            cursor.execute("""
                INSERT INTO orders (
                    id_customer,
                    id_model,
                    id_distributor,
                    time_order,
                    date,
                    age,
                    gender
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                customer_id_counter,
                messy_model,
                messy_distributor,
                unix_timestamp,
                target_date.isoformat(),
                age,
                gender,
            ))

            customer_id_counter += 1

        conn.commit()
        conn.close()

        print(
            f"Generated {num_orders} orders for {target_date}."
        )

        return num_orders


    def generate_daily_vendor_bids(self, target_date=None):

        target_date = normalize_date(target_date)

        if self.vendor_bids_exist_for_date(target_date):
            print(
                f"Vendor bids already exist for "
                f"{target_date}; skipping."
            )
            return 0

        conn = get_db_connection()
        cursor = conn.cursor()

        base_prices = {
            "mahogany": 12.50,
            "maple": 6.25,
            "rosewood": 70.00,
        }

        vendors = [1, 2, 3]

        wood_types = [
            "mahogany",
            "maple",
            "rosewood",
        ]

        trends = self.final_trends["vendor_bids"]

        records_added = 0

        for vendor in vendors:

            for wood_type in wood_types:

                base_price = base_prices[wood_type]

                adjustment = 1.0

                if vendor == 1:

                    if wood_type == "maple":
                        adjustment = (
                            trends[
                                "vendor_1_maple_adjustment"
                            ]
                        )

                    elif wood_type == "mahogany":
                        adjustment = (
                            trends[
                                "vendor_1_mahogany_adjustment"
                            ]
                        )

                elif vendor == 2:

                    if wood_type == "maple":
                        adjustment = (
                            trends[
                                "vendor_2_maple_adjustment"
                            ]
                        )

                    elif wood_type == "rosewood":
                        adjustment = (
                            trends[
                                "vendor_2_rosewood_adjustment"
                            ]
                        )

                    if (
                        wood_type == "mahogany"
                        and np.random.random()
                        < trends[
                            "vendor_2_mahogany_missing_prob"
                        ]
                    ):
                        price = None

                        cursor.execute("""
                            INSERT INTO vendor_bids (
                                date,
                                id_vendor,
                                type_wood,
                                price_wood_PerBF
                            )
                            VALUES (?, ?, ?, ?)
                        """, (
                            target_date.isoformat(),
                            make_messy_vendor_id(vendor),
                            wood_type,
                            price,
                        ))

                        records_added += 1
                        continue

                elif (
                    vendor == 3
                    and wood_type == "rosewood"
                ):
                    adjustment = (
                        trends[
                            "vendor_3_rosewood_adjustment"
                        ]
                    )

                # Preserve general missing-data behavior.
                if np.random.random() < 0.02:
                    price = None

                else:
                    standard_deviation = (
                        base_price *
                        (0.15 if vendor == 2 else 0.08)
                    )

                    mean_price = (
                        base_price * adjustment
                    )

                    price = max(
                        np.random.normal(
                            mean_price,
                            standard_deviation
                        ),
                        base_price * 0.3,
                    )

                    price = round(
                        float(price),
                        2
                    )

                cursor.execute("""
                    INSERT INTO vendor_bids (
                        date,
                        id_vendor,
                        type_wood,
                        price_wood_PerBF
                    )
                    VALUES (?, ?, ?, ?)
                """, (
                    target_date.isoformat(),
                    make_messy_vendor_id(vendor),
                    wood_type,
                    price,
                ))

                records_added += 1

        conn.commit()
        conn.close()

        print(
            f"Generated {records_added} vendor bids "
            f"for {target_date}."
        )

        return records_added


    def generate_for_date(self, target_date):

        target_date = normalize_date(target_date)

        orders = self.generate_daily_orders(
            target_date
        )

        bids = self.generate_daily_vendor_bids(
            target_date
        )

        return {
            "date": target_date.isoformat(),
            "orders_added": orders,
            "vendor_bids_added": bids,
        }


    def backfill(self, start_date, end_date):

        start_date = normalize_date(start_date)
        end_date = normalize_date(end_date)

        if start_date > end_date:
            raise ValueError(
                "start_date cannot be after end_date"
            )

        current = start_date

        total_orders = 0
        total_bids = 0
        dates_changed = 0

        while current <= end_date:

            result = self.generate_for_date(current)

            total_orders += result["orders_added"]
            total_bids += result["vendor_bids_added"]

            if (
                result["orders_added"]
                or result["vendor_bids_added"]
            ):
                dates_changed += 1

            current += timedelta(days=1)

        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "dates_changed": dates_changed,
            "orders_added": total_orders,
            "vendor_bids_added": total_bids,
        }


    def backfill_through_today(self):

        conn = get_db_connection()

        latest_order = conn.execute(
            "SELECT MAX(date) FROM orders"
        ).fetchone()[0]

        latest_bid = conn.execute(
            "SELECT MAX(date) FROM vendor_bids"
        ).fetchone()[0]

        conn.close()

        existing_dates = [
            normalize_date(value)
            for value in [latest_order, latest_bid]
            if value is not None
        ]

        if not existing_dates:
            raise RuntimeError(
                "Historical database is empty."
            )

        # Start one day after whichever table is furthest behind.
        start_date = min(existing_dates) + timedelta(days=1)

        today = datetime.now(timezone.utc).date()

        if start_date > today:
            return {
                "start_date": start_date.isoformat(),
                "end_date": today.isoformat(),
                "dates_changed": 0,
                "orders_added": 0,
                "vendor_bids_added": 0,
            }

        return self.backfill(
            start_date,
            today
        )


def run_daily_generation():

    generator = DailyDataGenerator()

    today = datetime.now(timezone.utc).date()

    return generator.generate_for_date(today)


if __name__ == "__main__":
    print(run_daily_generation())
