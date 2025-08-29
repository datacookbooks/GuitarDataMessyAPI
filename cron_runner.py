#!/usr/bin/env python3
"""
Simple cron runner for Railway cron jobs
This will be the entry point when Railway runs the cron schedule
"""

from daily_generator import run_daily_generation

if __name__ == "__main__":
    print("Starting daily data generation cron job...")
    run_daily_generation()
    print("Daily data generation completed.")