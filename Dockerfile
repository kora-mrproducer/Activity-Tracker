# Activity Tracker - Docker image
# Use a slim Python base for smaller image size
FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create app directory
WORKDIR /app

# System deps (optional but useful for building wheels or PDF libs if needed)
# Uncomment if you hit build issues with Pillow/ReportLab
# RUN apt-get update \
#     && apt-get install -y --no-install-recommends build-essential \
#     && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (better layer caching)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set production env and bind to all interfaces inside container
ENV FLASK_ENV=production \
    HOST=0.0.0.0 \
    PORT=5000

# Expose port
EXPOSE 5000

# Create writable folders (in case they're missing)
RUN mkdir -p /app/instance /app/logs /app/backups

# Start the server
CMD ["python", "run.py"]
