from fastapi import FastAPI, HTTPException, Query
import sqlite3
import pandas as pd
from typing import Optional, List
from datetime import datetime, timedelta
import os
from daily_generator import run_daily_generation

app = FastAPI(
    title="Business Data API",
    description="API for orders and vendor bids data",
    version="1.0.0"
)

DATABASE_PATH = "business_data.db"

def get_db_connection():
    """Get database connection"""
    if not os.path.exists(DATABASE_PATH):
        raise HTTPException(status_code=500, detail="Database not found")
    return sqlite3.connect(DATABASE_PATH)

@app.get("/")
def read_root():
    return {"message": "Business Data API", "version": "1.0.0"}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        return {"status": "healthy"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/orders")
def get_orders(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: Optional[int] = Query(None, description="Maximum number of records")
):
    """Get orders data with optional date filtering"""
    try:
        conn = get_db_connection()
        
        # Build query
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
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY date DESC, time_order DESC"
        
        if limit:
            query += f" LIMIT {limit}"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        return {
            "data": df.to_dict(orient="records"),
            "count": len(df),
            "message": "Orders retrieved successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving orders: {str(e)}")

@app.get("/vendor-bids")
def get_vendor_bids(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    vendor_id: Optional[str] = Query(None, description="Vendor ID filter"),
    wood_type: Optional[str] = Query(None, description="Wood type filter"),
    limit: Optional[int] = Query(None, description="Maximum number of records")
):
    """Get vendor bids data with optional filtering"""
    try:
        conn = get_db_connection()
        
        # Build query
        query = "SELECT * FROM vendor_bids"
        params = []
        conditions = []
        
        if start_date:
            conditions.append("date >= ?")
            params.append(start_date)
        
        if end_date:
            conditions.append("date <= ?")
            params.append(end_date)
            
        if vendor_id:
            conditions.append("id_vendor = ?")
            params.append(vendor_id)
            
        if wood_type:
            conditions.append("type_wood = ?")
            params.append(wood_type)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY date DESC"
        
        if limit:
            query += f" LIMIT {limit}"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        return {
            "data": df.to_dict(orient="records"),
            "count": len(df),
            "message": "Vendor bids retrieved successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving vendor bids: {str(e)}")

@app.get("/summary")
def get_summary():
    """Get summary statistics"""
    try:
        conn = get_db_connection()
        
        # Orders summary
        orders_summary = pd.read_sql_query("""
            SELECT 
                COUNT(*) as total_orders,
                MIN(date) as earliest_order,
                MAX(date) as latest_order,
                AVG(age) as avg_age,
                COUNT(DISTINCT id_customer) as unique_customers
            FROM orders
        """, conn)
        
        # Vendor bids summary
        bids_summary = pd.read_sql_query("""
            SELECT 
                COUNT(*) as total_bids,
                MIN(date) as earliest_bid,
                MAX(date) as latest_bid,
                AVG(price_wood_PerBF) as avg_price,
                COUNT(DISTINCT id_vendor) as unique_vendors,
                COUNT(DISTINCT type_wood) as wood_types
            FROM vendor_bids
            WHERE price_wood_PerBF IS NOT NULL
        """, conn)
        
        conn.close()
        
        return {
            "orders": orders_summary.to_dict(orient="records")[0],
            "vendor_bids": bids_summary.to_dict(orient="records")[0],
            "message": "Summary retrieved successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving summary: {str(e)}")

@app.post("/generate-daily-data")
def trigger_daily_generation():
    """Manually trigger daily data generation (for testing)"""
    try:
        run_daily_generation()
        return {"message": "Daily data generation completed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating daily data: {str(e)}")

@app.get("/latest-data")
def get_latest_data():
    """Get the most recent data from both tables"""
    try:
        conn = get_db_connection()
        
        # Get latest orders (last 7 days)
        latest_orders = pd.read_sql_query("""
            SELECT * FROM orders 
            WHERE date >= date('now', '-7 days')
            ORDER BY date DESC, time_order DESC
            LIMIT 50
        """, conn)
        
        # Get latest vendor bids (last 7 days)
        latest_bids = pd.read_sql_query("""
            SELECT * FROM vendor_bids 
            WHERE date >= date('now', '-7 days')
            ORDER BY date DESC
            LIMIT 50
        """, conn)
        
        conn.close()
        
        return {
            "orders": latest_orders.to_dict(orient="records"),
            "vendor_bids": latest_bids.to_dict(orient="records"),
            "message": "Latest data retrieved successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving latest data: {str(e)}")

# Add CORS middleware if needed for Power BI
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)