# IPPOC Mnemosyne API - Cloud Run Dockerfile
# Used by Google Cloud Build for automatic deployment

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create requirements file
RUN echo "fastapi>=0.104.0\nuvicorn[standard]>=0.24.0\nhttpx>=0.25.0\npydantic>=2.5.0\npyyaml>=6.0\nstructlog>=23.2.0\nlangchain>=0.1.0\nlangchain-google-genai>=1.0.0\nlangchain-community>=0.0.0\npsycopg2-binary>=2.9.9" > requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ippoc/ ./src/ippoc/

# Create __init__.py files for proper imports
RUN find src/ippoc -type d -exec touch {}/__init__.py \; 2>/dev/null || true

# Expose the port Cloud Run will use
ENV PORT=8080
EXPOSE 8080

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

# Run the application with the correct module path
CMD ["python", "-m", "uvicorn", "ippoc.mnemosyne.api.server:app", "--host", "0.0.0.0", "--port", "8080"]
