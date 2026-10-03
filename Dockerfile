FROM python:3.12-slim

WORKDIR /app

# Install system dependencies (if any needed for fastapi/uvicorn)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose ports (bot uses polling, webhook uses 8000)
EXPOSE 8000

ENV PYTHONUNBUFFERED=1

# Default command will be overridden in docker‑compose
CMD ["python", "bot.py"]