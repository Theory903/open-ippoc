FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY brain/requirements.txt ./brain/requirements.txt
RUN pip install --no-cache-dir -r brain/requirements.txt

# Copy source code
COPY brain/cortex/ ./brain/cortex/
COPY .env ./ .env

# Expose Cortex port
EXPOSE 8001

CMD ["python", "brain/cortex/server.py"]
