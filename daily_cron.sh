#!/bin/bash
# Daily data generation script
# Add this to your crontab with: 0 1 * * * /path/to/daily_cron.sh

cd "$(dirname "$0")"
python daily_generator.py >> daily_generation.log 2>&1
