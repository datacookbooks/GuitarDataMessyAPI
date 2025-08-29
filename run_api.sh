#!/bin/bash
# Simple script to run the API locally

echo "Starting Business Data API..."
echo "API will be available at: http://localhost:8000"
echo "API docs will be available at: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
