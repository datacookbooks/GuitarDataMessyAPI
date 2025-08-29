#!/usr/bin/env python3
"""
Setup script to initialize the business data API
Run this once to set up your database and test the system
"""

import os
import subprocess
import sys
from pathlib import Path

def install_requirements():
    """Install required packages from requirements.txt"""
    
    # Check if requirements.txt exists
    if not os.path.exists("requirements.txt"):
        print("ERROR: requirements.txt not found!")
        print("Please make sure requirements.txt is in the same directory as setup.py")
        return False
    
    print("Installing requirements from requirements.txt...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("SUCCESS: Requirements installed successfully from requirements.txt")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install requirements: {e}")
        print("You may need to install them manually:")
        print("pip install -r requirements.txt")
        return False

def initialize_database():
    """Initialize the database with historical data"""
    print("Initializing database with historical data...")
    print("This may take a few minutes...")
    
    try:
        from database_setup import setup_database
        setup_database()
        print("SUCCESS: Database initialized successfully")
    except Exception as e:
        print(f"ERROR: Error initializing database: {e}")
        return False
    
    return True

def test_daily_generation():
    """Test the daily data generation"""
    print("Testing daily data generation...")
    
    try:
        from daily_generator import run_daily_generation
        run_daily_generation()
        print("SUCCESS: Daily data generation test successful")
    except Exception as e:
        print(f"ERROR: Error in daily generation: {e}")
        return False
    
    return True

def test_api():
    """Test the API endpoints"""
    print("Testing API...")
    
    try:
        # Import and test basic functionality
        from main import app
        print("SUCCESS: API imports successful")
        
    except Exception as e:
        print(f"ERROR: Error testing API: {e}")
        return False
    
    return True

def create_run_script():
    """Create a simple run script"""
    run_script = """#!/bin/bash
# Simple script to run the API locally

echo "Starting Business Data API..."
echo "API will be available at: http://localhost:8000"
echo "API docs will be available at: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
"""
    
    with open("run_api.sh", "w") as f:
        f.write(run_script)
    
    # Make it executable on Unix systems
    if os.name != 'nt':  # Not Windows
        os.chmod("run_api.sh", 0o755)
    
    print("SUCCESS: Created run_api.sh script")

def create_cron_script():
    """Create a cron job script for daily data generation"""
    cron_script = """#!/bin/bash
# Daily data generation script
# Add this to your crontab with: 0 1 * * * /path/to/daily_cron.sh

cd "$(dirname "$0")"
python daily_generator.py >> daily_generation.log 2>&1
"""
    
    with open("daily_cron.sh", "w") as f:
        f.write(cron_script)
    
    if os.name != 'nt':  # Not Windows
        os.chmod("daily_cron.sh", 0o755)
    
    print("SUCCESS: Created daily_cron.sh script")

def main():
    print("Setting up Business Data API")
    print("=" * 40)
    
    # Check if we're in the right directory
    required_files = ["data_utils.py", "database_setup.py", "daily_generator.py", "main.py"]
    missing_files = [f for f in required_files if not Path(f).exists()]
    
    if missing_files:
        print(f"ERROR: Missing required files: {missing_files}")
        print("Please make sure all files are in the same directory")
        return
    
    # Install requirements
    if not install_requirements():
        return
    
    # Initialize database
    if not initialize_database():
        return
    
    # Test daily generation
    if not test_daily_generation():
        return
    
    # Test API
    if not test_api():
        return
    
    # Create helper scripts
    create_run_script()
    create_cron_script()
    
    print("\n" + "=" * 40)
    print("Setup complete!")
    print("\nNext steps:")
    print("1. Run the API locally:")
    print("   python -m uvicorn main:app --reload")
    print("   or")
    print("   ./run_api.sh")
    print("\n2. Visit http://localhost:8000/docs to test the API")
    print("\n3. For daily data generation, either:")
    print("   - Set up a cron job using daily_cron.sh")
    print("   - Use your hosting platform's cron feature")
    print("   - Call the /generate-daily-data endpoint manually")
    print("\n4. Update Power BI to use these endpoints:")
    print("   - Orders: http://your-domain.com/orders")
    print("   - Vendor Bids: http://your-domain.com/vendor-bids")
    print("\n5. Deploy to Railway, Render, or Fly.io for production")

if __name__ == "__main__":
    main()

    


