from pathlib import Path

import logging
import os
from contextlib import asynccontextmanager

import pandas as pd

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

from database_setup import setup_database
from daily_generator import (
    DailyDataGenerator,
    run_daily_generation
)
from db_config import (
    get_db_connection,
    DATABASE_PATH
)


logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent
REFERENCE_DATA_DIR = ROOT_DIR / "reference_data"

def dataframe_records(df):
    """
    Convert pandas NaN values to JSON-safe None values.
    """

    clean_df = (
        df.astype(object)
        .where(pd.notna(df), None)
    )

    return clean_df.to_dict(
        orient="records"
    )


@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info(
        f"Using database: {DATABASE_PATH}"
    )

    # Creates tables and seeds CSV history only
    # if the database is new/empty.
    setup_database()

    # Automatically recover dates missed while
    # Railway was offline.
    generator = DailyDataGenerator()

    result = generator.backfill_through_today()

    logger.info(
        f"Startup backfill result: {result}"
    )

    yield


app = FastAPI(
    title="Business Data API",
    description="API for messy orders and vendor bids data",
    version="2.0.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():

    return {
        "message": "Business Data API",
        "version": "2.0.0",
        "endpoints": {
            "orders": "/api/orders",
            "vendor_bids": "/api/vendor-bids",
            "models": "/api/models",
            "distributors": "/api/distributors",
            "status": "/api/status",
            "health": "/health",
        },
    }


@app.get("/health")
@app.get("/api/health", include_in_schema=False)
def health_check():

    try:

        conn = get_db_connection()

        conn.execute(
            "SELECT 1 FROM orders LIMIT 1"
        )

        conn.execute(
            "SELECT 1 FROM vendor_bids LIMIT 1"
        )

        conn.close()

        return {
            "status": "healthy"
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )


@app.get("/orders")
@app.get("/api/orders", include_in_schema=False)
def get_orders(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: Optional[int] = Query(None, ge=1),
):

    try:

        conn = get_db_connection()

        query = "SELECT * FROM orders"

        params = []
        conditions = []

        if start_date:
            conditions.append("date >= ?")
            params.append(start_date)

        if end_date:
            conditions.append("date <= ?")
            params.append(end_date)

        if conditions:
            query += (
                " WHERE "
                + " AND ".join(conditions)
            )

        query += (
            " ORDER BY date DESC, "
            "time_order DESC"
        )

        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)

        df = pd.read_sql_query(
            query,
            conn,
            params=params
        )

        conn.close()

        return {
            "data": dataframe_records(df),
            "count": len(df),
            "message":
                "Orders retrieved successfully",
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Error retrieving orders: "
                + str(exc)
            ),
        )


@app.get("/vendor-bids")
@app.get(
    "/api/vendor-bids",
    include_in_schema=False
)
def get_vendor_bids(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    vendor_id: Optional[str] = Query(None),
    wood_type: Optional[str] = Query(None),
    limit: Optional[int] = Query(None, ge=1),
):

    try:

        conn = get_db_connection()

        query = (
            "SELECT * FROM vendor_bids"
        )

        params = []
        conditions = []

        if start_date:
            conditions.append("date >= ?")
            params.append(start_date)

        if end_date:
            conditions.append("date <= ?")
            params.append(end_date)

        if vendor_id:
            conditions.append(
                "id_vendor = ?"
            )
            params.append(vendor_id)

        if wood_type:
            conditions.append(
                "type_wood = ?"
            )
            params.append(wood_type)

        if conditions:
            query += (
                " WHERE "
                + " AND ".join(conditions)
            )

        query += " ORDER BY date DESC"

        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)

        df = pd.read_sql_query(
            query,
            conn,
            params=params
        )

        conn.close()

        return {
            "data": dataframe_records(df),
            "count": len(df),
            "message":
                "Vendor bids retrieved successfully",
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Error retrieving vendor bids: "
                + str(exc)
            ),
        )

@app.get("/models")
@app.get(
    "/api/models",
    include_in_schema=False
)
def get_models():

    try:

        file_path = (
            REFERENCE_DATA_DIR
            / "df_models.csv"
        )

        df = pd.read_csv(file_path)

        return {
            "data": dataframe_records(df),
            "count": len(df),
            "message":
                "Models retrieved successfully",
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Error retrieving models: "
                + str(exc)
            ),
        )

@app.get("/distributors")
@app.get(
    "/api/distributors",
    include_in_schema=False
)
def get_distributors():

    try:

        file_path = (
            REFERENCE_DATA_DIR
            / "df_distributors.csv"
        )

        df = pd.read_csv(file_path)

        return {
            "data": dataframe_records(df),
            "count": len(df),
            "message":
                "Distributors retrieved successfully",
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Error retrieving distributors: "
                + str(exc)
            ),
        )

@app.get("/summary")
@app.get(
    "/api/summary",
    include_in_schema=False
)
def get_summary():

    try:

        conn = get_db_connection()

        orders = pd.read_sql_query("""
            SELECT
                COUNT(*) AS total_orders,
                MIN(date) AS earliest_order,
                MAX(date) AS latest_order,
                AVG(age) AS avg_age,
                COUNT(DISTINCT id_customer)
                    AS unique_customers
            FROM orders
        """, conn)

        bids = pd.read_sql_query("""
            SELECT
                COUNT(*) AS total_bids,
                MIN(date) AS earliest_bid,
                MAX(date) AS latest_bid,
                AVG(price_wood_PerBF)
                    AS avg_price,
                COUNT(DISTINCT id_vendor)
                    AS unique_vendors,
                COUNT(DISTINCT type_wood)
                    AS wood_types
            FROM vendor_bids
            WHERE price_wood_PerBF IS NOT NULL
        """, conn)

        conn.close()

        return {
            "orders":
                dataframe_records(orders)[0],

            "vendor_bids":
                dataframe_records(bids)[0],

            "message":
                "Summary retrieved successfully",
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )


@app.get("/api/status")
def get_status():

    conn = get_db_connection()

    order_stats = conn.execute("""
        SELECT
            COUNT(*) AS rows,
            MIN(date) AS min_date,
            MAX(date) AS max_date
        FROM orders
    """).fetchone()

    bid_stats = conn.execute("""
        SELECT
            COUNT(*) AS rows,
            MIN(date) AS min_date,
            MAX(date) AS max_date
        FROM vendor_bids
    """).fetchone()

    conn.close()

    return {
        "orders": {
            "rows": order_stats["rows"],
            "min_date":
                order_stats["min_date"],
            "max_date":
                order_stats["max_date"],
        },

        "vendor_bids": {
            "rows": bid_stats["rows"],
            "min_date":
                bid_stats["min_date"],
            "max_date":
                bid_stats["max_date"],
        },
    }


@app.post("/generate-daily-data")
@app.post(
    "/api/generate-daily-data",
    include_in_schema=False
)
def trigger_daily_generation(
    request: Request
):

    expected_token = os.environ.get(
        "DAILY_GENERATION_TOKEN"
    )

    if not expected_token:

        raise HTTPException(
            status_code=503,
            detail=(
                "DAILY_GENERATION_TOKEN "
                "is not configured"
            ),
        )

    supplied_token = request.headers.get(
        "Authorization"
    )

    if supplied_token != (
        f"Bearer {expected_token}"
    ):

        raise HTTPException(
            status_code=401,
            detail="Unauthorized"
        )

    try:

        result = run_daily_generation()

        return {
            "success": True,
            **result,
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Error generating daily data: "
                + str(exc)
            ),
        )
