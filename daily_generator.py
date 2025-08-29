import sqlite3
import numpy as np
from datetime import datetime, timedelta
import random
from data_utils import make_messy_id, make_messy_vendor_id

class DailyDataGenerator:
    def __init__(self, db_path='business_data.db'):
        self.db_path = db_path
        # Fixed endpoint values (from your trend analysis)
        self.final_trends = {
            'orders': {
                'standard_prob': 0.4,  # Fixed at endpoint
                'premium_prob': 0.5,   # Increased to final level
                'boutique_prob': 0.1,  # Decreased to final level
                'age_mean': 36,        # Final age trend
                'regional_probs': [0.25, 0.15, 0.225, 0.2, 0.175]  # Final regional distribution
            },
            'vendor_bids': {
                'vendor_1_maple_adjustment': 0.85,    # 15% cheaper final
                'vendor_1_mahogany_adjustment': 0.85,  # 15% cheaper final
                'vendor_2_maple_adjustment': 1.20,     # 20% more expensive final
                'vendor_2_rosewood_adjustment': 1.20,  # 20% more expensive final
                'vendor_2_mahogany_missing_prob': 0.30, # 30% missing final
                'vendor_3_rosewood_adjustment': 0.88   # 12% cheaper final
            }
        }
    
    def generate_daily_orders(self, target_date=None):
        """Generate orders for a specific date using fixed endpoint trends"""
        if target_date is None:
            target_date = datetime.now().date()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get last customer ID
        cursor.execute('SELECT MAX(id_customer) FROM orders')
        result = cursor.fetchone()
        customer_id_counter = (result[0] + 1) if result[0] else 100000000
        
        # Fixed number of orders per day (endpoint trend)
        num_orders = random.randint(5, 7)  # Final range
        
        trends = self.final_trends['orders']
        
        for _ in range(num_orders):
            # Use fixed endpoint probabilities
            category_choice = np.random.choice(['standard', 'premium', 'boutique'],
                                             p=[trends['standard_prob'], trends['premium_prob'], trends['boutique_prob']])
            
            # Select model based on category
            if category_choice == 'standard':
                id_model = np.random.choice([1, 2, 3])
            elif category_choice == 'premium':
                id_model = np.random.choice([4, 5, 6])
            else:  # boutique
                id_model = np.random.choice([7, 8, 9])
            
            # Select distributor using fixed regional probabilities
            id_distributor = np.random.choice([1, 2, 3, 4, 5], p=trends['regional_probs'])
            
            # Make IDs messy (reuse your functions)
            messy_id_model = make_messy_id(id_model, is_distributor=False)
            messy_id_distributor = make_messy_id(id_distributor, is_distributor=True)
            
            # Generate timestamp for the day
            random_hour = np.random.randint(0, 24)
            random_minute = np.random.randint(0, 60)
            random_second = np.random.randint(0, 60)
            
            order_datetime = datetime.combine(target_date, datetime.min.time()).replace(
                hour=random_hour, minute=random_minute, second=random_second)
            unix_timestamp = str(int(order_datetime.timestamp()))
            
            # Use fixed age trend endpoint
            age = max(18, int(np.random.normal(trends['age_mean'], 6)))
            gender = 'M' if np.random.random() < 0.65 else 'F'
            
            # Insert into database
            cursor.execute('''
                INSERT INTO orders (id_customer, id_model, id_distributor, time_order, date, age, gender)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (customer_id_counter, messy_id_model, messy_id_distributor, unix_timestamp, 
                  target_date.strftime('%Y-%m-%d'), age, gender))
            
            customer_id_counter += 1
        
        # Small chance of duplicates (maintain original behavior)
        if np.random.random() < 0.05:
            # Add 1-2 duplicate orders
            pass  # Implement if needed
        
        conn.commit()
        conn.close()
        
        return num_orders
    
    def generate_daily_vendor_bids(self, target_date=None):
        """Generate vendor bids for a specific date using fixed endpoint trends"""
        if target_date is None:
            target_date = datetime.now().date()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        base_prices = {
            'mahogany': 12.50,
            'maple': 6.25,
            'rosewood': 70.00
        }
        
        vendors = [1, 2, 3]
        wood_types = ['mahogany', 'maple', 'rosewood']
        trends = self.final_trends['vendor_bids']
        
        for vendor in vendors:
            for wood_type in wood_types:
                base_price = base_prices[wood_type]
                
                # Apply fixed endpoint adjustments
                price_adjustment = 1.0
                
                if vendor == 1:
                    if wood_type in ['maple', 'mahogany']:
                        price_adjustment = trends[f'vendor_1_{wood_type}_adjustment']
                
                elif vendor == 2:
                    if wood_type in ['maple', 'rosewood']:
                        price_adjustment = trends[f'vendor_2_{wood_type}_adjustment']
                    
                    # Fixed missing probability for mahogany
                    if wood_type == 'mahogany':
                        if np.random.random() < trends['vendor_2_mahogany_missing_prob']:
                            messy_vendor_id = make_messy_vendor_id(vendor)
                            cursor.execute('''
                                INSERT INTO vendor_bids (date, id_vendor, type_wood, price_wood_PerBF)
                                VALUES (?, ?, ?, ?)
                            ''', (target_date.strftime('%Y-%m-%d'), messy_vendor_id, wood_type, None))
                            continue
                
                elif vendor == 3:
                    if wood_type == 'rosewood':
                        price_adjustment = trends['vendor_3_rosewood_adjustment']
                
                # General missing probability
                if np.random.random() < 0.02:
                    messy_vendor_id = make_messy_vendor_id(vendor)
                    cursor.execute('''
                        INSERT INTO vendor_bids (date, id_vendor, type_wood, price_wood_PerBF)
                        VALUES (?, ?, ?, ?)
                    ''', (target_date.strftime('%Y-%m-%d'), messy_vendor_id, wood_type, None))
                    continue
                
                # Calculate price with fixed adjustment
                base_std = base_price * (0.15 if vendor == 2 else 0.08)
                adjusted_mean = base_price * price_adjustment
                price = max(np.random.normal(adjusted_mean, base_std), base_price * 0.3)
                price = round(price, 2)
                
                messy_vendor_id = make_messy_vendor_id(vendor)
                cursor.execute('''
                    INSERT INTO vendor_bids (date, id_vendor, type_wood, price_wood_PerBF)
                    VALUES (?, ?, ?, ?)
                ''', (target_date.strftime('%Y-%m-%d'), messy_vendor_id, wood_type, price))
        
        conn.commit()
        conn.close()

# Daily cron job function
def run_daily_generation():
    """Function to be called by cron job daily"""
    generator = DailyDataGenerator()
    
    today = datetime.now().date()
    
    # Check if data already exists for today
    conn = sqlite3.connect('business_data.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM orders WHERE date = ?', (today.strftime('%Y-%m-%d'),))
    orders_exist = cursor.fetchone()[0] > 0
    
    cursor.execute('SELECT COUNT(*) FROM vendor_bids WHERE date = ?', (today.strftime('%Y-%m-%d'),))
    bids_exist = cursor.fetchone()[0] > 0
    
    conn.close()
    
    if not orders_exist:
        orders_count = generator.generate_daily_orders(today)
        print(f"Generated {orders_count} orders for {today}")
    
    if not bids_exist:
        generator.generate_daily_vendor_bids(today)
        print(f"Generated vendor bids for {today}")

if __name__ == "__main__":
    run_daily_generation()