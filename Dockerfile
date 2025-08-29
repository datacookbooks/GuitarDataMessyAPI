# Use Python 3.12 slim image as base
FROM python:3.12-slim

# Set working directory in container
WORKDIR /app

# Copy requirements file first (for better Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application files to container
COPY . .

# Initialize the database with historical data
RUN python database_setup.py

# Expose port 8000 (FastAPI default)
EXPOSE 8000

# Create a startup script that handles both web and cron modes
RUN echo '#!/bin/bash\nif [ "$RAILWAY_CRON_RUN" = "1" ]; then\n  python cron_runner.py\nelse\n  uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}\nfi' > start.sh && chmod +x start.sh

# Use the startup script
CMD ["./start.sh"]