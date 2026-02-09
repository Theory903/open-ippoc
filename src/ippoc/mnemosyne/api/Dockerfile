FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for PGVector and building C extensions
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY memory/requirements.txt ./memory/requirements.txt
RUN pip install --no-cache-dir -r memory/requirements.txt

# Copy source code
COPY memory/ ./memory/
COPY .env ./ .env

# Expose Memory port
EXPOSE 8000

CMD ["python", "-m", "uvicorn", "memory.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
