# IPPOC Cloud Run Dockerfile
# Used by Google Cloud Build for automatic deployment to Cloud Run

# Build stage - install dependencies
FROM python:3.11-slim as builder

WORKDIR /app

# Copy requirements if available
COPY src/ippoc/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code (maintain structure for imports)
COPY src/ippoc/ ./src/ippoc/

# Create __init__.py files to make packages importable
RUN find src/ippoc -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Expose the port Cloud Run will use
ENV PORT=8080
EXPOSE 8080

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

# Run the main application using Python module path
CMD ["python", "-m", "uvicorn", "src.ippoc.mnemosyne.api.server:app", "--host", "0.0.0.0", "--port", "8080"]
