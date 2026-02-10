# IPPOC Ollama API Service (Cloud Version)
# Uses Ollama Cloud API with kimi-k2.5:cloud model

FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements-ollama.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy API wrapper
COPY ollama_api.py ./

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8086/health')" || exit 1

EXPOSE 8086

# Environment variables
ENV OLLAMA_HOST=https://api.ollama.com
ENV OLLAMA_MODEL=kimi-k2.5:cloud
ENV PORT=8086

# Run the API server
CMD ["python", "ollama_api.py"]
