# # Use Python 3.12 slim image as base
# FROM python:3.12-slim

# # Set working directory in container
# WORKDIR /app

# # Copy requirements file first (for better Docker layer caching)
# COPY requirements.txt .

# # Install Python dependencies
# RUN pip install --no-cache-dir -r requirements.txt

# # Copy all application files to container
# COPY . .

# # Initialize the database with historical data
# RUN python database_setup.py

# # Expose port 8000 (FastAPI default)
# EXPOSE 8000

# # Create a proper startup script
# RUN echo '#!/bin/bash\n\
# if [ "$RAILWAY_CRON_RUN" = "1" ]; then\n\
#   echo "Running cron job"\n\
#   python cron_runner.py\n\
# else\n\
#   echo "Starting web server"\n\
#   uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}\n\
# fi' > start.sh && chmod +x start.sh

# # Use the startup script
# CMD ["bash", "start.sh"]








# # Use Python 3.12 slim image as base
# FROM python:3.12-slim

# # Set working directory in container
# WORKDIR /app

# # Copy requirements file first (for better Docker layer caching)
# COPY requirements.txt .

# # Install Python dependencies
# RUN pip install --no-cache-dir -r requirements.txt

# # Copy all application files to container
# COPY . .

# # Initialize the database with historical data
# RUN python database_setup.py

# # Expose port 8000 (FastAPI default)
# EXPOSE 8000

# # Direct command for now - bypass the startup script
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]





# # Use Python 3.12 slim image as base
# FROM python:3.12-slim

# # Set working directory in container
# WORKDIR /app

# # Copy requirements file first (for better Docker layer caching)
# COPY requirements.txt .

# # Install Python dependencies
# RUN pip install --no-cache-dir -r requirements.txt

# # Copy all application files to container
# COPY . .

# # Skip database initialization during build - do it at runtime instead
# # RUN python database_setup.py

# # Expose port 8000 (FastAPI default)
# EXPOSE 8000

# # Test with a simple Python command first
# CMD ["python", "-c", "print('Container started successfully'); import sys; sys.exit(0)"]




FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create empty database file
RUN touch business_data.db

# Initialize database at runtime, not build time
CMD python database_setup.py && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}