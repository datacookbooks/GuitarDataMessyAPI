import pandas as pd
from pathlib import Path

from db_config import get_db_connection, DATABASE_PATH


ROOT_DIR = Path(__file__).resolve().parent

ORDERS_CSV = ROOT_DIR / "df_orders_messy.csv"
BIDS_CSV = ROOT_DIR / "df_vendor_bids_messy.csv"


def setup_database():
    """
    Create the database and seed historical data only when
    the relevant table is empty.

    This is safe to run repeatedly.
    """

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_customer INTEGER,
            id_model TEXT,
            id_distributor TEXT,
            time_order TEXT,
            date TEXT,
            age INTEGER,
            gender TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vendor_bids (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            id_vendor TEXT,
            type_wood TEXT,
            price_wood_PerBF REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()

    # --------------------------
    # Seed historical orders
    # --------------------------

    orders_count = cursor.execute(
        "SELECT COUNT(*) FROM orders"
    ).fetchone()[0]

    if orders_count == 0:
        print("Orders table is empty. Loading historical CSV...")

        df_orders = pd.read_csv(ORDERS_CSV)

        rows = [
            (
                row["id_customer"],
                row["id_model"],
                row["id_distributor"],
                row["time_order"],
                row["date"],
                row["age"],
                row["gender"],
            )
            for _, row in df_orders.iterrows()
        ]

        cursor.executemany("""
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
        """, rows)

        print(f"Loaded {len(rows)} historical orders.")

    else:
        print(
            f"Orders table already contains "
            f"{orders_count} rows; historical seed skipped."
        )

    # --------------------------
    # Seed historical vendor bids
    # --------------------------

    bids_count = cursor.execute(
        "SELECT COUNT(*) FROM vendor_bids"
    ).fetchone()[0]

    if bids_count == 0:
        print("Vendor bids table is empty. Loading historical CSV...")

        df_bids = pd.read_csv(BIDS_CSV)

        rows = []

        for _, row in df_bids.iterrows():
            price = (
                row["price_wood_PerBF"]
                if pd.notna(row["price_wood_PerBF"])
                else None
            )

            rows.append(
                (
                    row["date"],
                    row["id_vendor"],
                    row["type_wood"],
                    price,
                )
            )

        cursor.executemany("""
            INSERT INTO vendor_bids (
                date,
                id_vendor,
                type_wood,
                price_wood_PerBF
            )
            VALUES (?, ?, ?, ?)
        """, rows)

        print(f"Loaded {len(rows)} historical vendor bids.")

    else:
        print(
            f"Vendor bids table already contains "
            f"{bids_count} rows; historical seed skipped."
        )

    conn.commit()
    conn.close()

    print(f"Database ready at {DATABASE_PATH}")


if __name__ == "__main__":
    setup_database()
