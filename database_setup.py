import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from data_utils import make_messy_id, make_messy_vendor_id

def setup_database():
    """Initialize database and populate with historical data from CSV files"""
    conn = sqlite3.connect('business_data.db')
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
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
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vendor_bids (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            id_vendor TEXT,
            type_wood TEXT,
            price_wood_PerBF REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Load data from CSV files
    load_orders_from_csv(cursor)
    load_vendor_bids_from_csv(cursor)
    
    conn.commit()
    conn.close()

def load_orders_from_csv(cursor):
    """Load orders data from CSV file"""
    try:
        print("Loading orders data from df_orders_messy.csv...")
        df_orders = pd.read_csv('df_orders_messy.csv')
        
        # Insert data into database
        for _, row in df_orders.iterrows():
            cursor.execute('''
                INSERT INTO orders (id_customer, id_model, id_distributor, time_order, date, age, gender)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                row['id_customer'],
                row['id_model'], 
                row['id_distributor'],
                row['time_order'],
                row['date'],
                row['age'],
                row['gender']
            ))
        
        print(f"SUCCESS: Loaded {len(df_orders)} orders from CSV")
        
    except FileNotFoundError:
        print("ERROR: df_orders_messy.csv not found. Make sure the file is in the same directory.")
        raise
    except Exception as e:
        print(f"ERROR: Error loading orders CSV: {e}")
        raise

def load_vendor_bids_from_csv(cursor):
    """Load vendor bids data from CSV file"""
    try:
        print("Loading vendor bids data from df_vendor_bids_messy.csv...")
        df_vendor_bids = pd.read_csv('df_vendor_bids_messy.csv')
        
        # Insert data into database
        for _, row in df_vendor_bids.iterrows():
            # Handle NaN values in price_wood_PerBF
            price = row['price_wood_PerBF'] if pd.notna(row['price_wood_PerBF']) else None
            
            cursor.execute('''
                INSERT INTO vendor_bids (date, id_vendor, type_wood, price_wood_PerBF)
                VALUES (?, ?, ?, ?)
            ''', (
                row['date'],
                row['id_vendor'],
                row['type_wood'],
                price
            ))
        
        print(f"SUCCESS: Loaded {len(df_vendor_bids)} vendor bids from CSV")
        
    except FileNotFoundError:
        print("ERROR: df_vendor_bids_messy.csv not found. Make sure the file is in the same directory.")
        raise
    except Exception as e:
        print(f"ERROR: Error loading vendor bids CSV: {e}")
        raise

if __name__ == "__main__":
    setup_database()
    print("Database initialized successfully!")