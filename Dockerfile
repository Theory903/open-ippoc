# Dockerfile
# @cognitive - IPPOC Reference Organism Runtime

FROM python:3.11-slim-bookworm

# 1. Safety & Efficiency
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    IPPOC_ENV=production

WORKDIR /app

# 2. Dependencies (Frozen Genome)
COPY requirements.lock .
RUN pip install --no-cache-dir -r requirements.lock

# 3. Application Code
COPY . .

# 4. Persistence Setup (Ensure directories exist for mounting)
RUN mkdir -p brain/memory brain/preservation brain/logs

# 5. Non-Root User (Dignity/Security)
RUN useradd -m ippoc && chown -R ippoc:ippoc /app
USER ippoc

# 6. Runtime Interaction
# We invoke via main.py or a shell if needed
CMD ["python", "main.py"]
