#!/bin/bash
# IPPOC Entrypoint - Cloud Run Startup Script

set -e

echo "🚀 IPPOC Starting on Cloud Run..."
echo "📦 Instance: ${INSTANCE:-local}"
echo "🌐 Port: ${PORT:-8080}"

# ==============================================================================
# Environment Validation
# ==============================================================================

# Check required environment variables
if [ -z "$IPPOC_API_KEY" ]; then
    echo "⚠️  IPPOC_API_KEY not set - generating temporary key"
    export IPPOC_API_KEY=$(openssl rand -hex 32)
fi

# ==============================================================================
# Service Health Checks
# ==============================================================================

# Wait for dependencies if URLS are provided
wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=1

    echo "⏳ Waiting for $name at $url..."

    while [ $attempt -le $max_attempts ]; do
        if curl -sf "$url/health" > /dev/null 2>&1; then
            echo "✅ $name is ready"
            return 0
        fi
        echo "   Attempt $attempt/$max_attempts..."
        sleep 2
        attempt=$((attempt + 1))
    done

    echo "⚠️  $name not available - continuing anyway"
    return 1
}

# Wait for Cloud SQL if connection string is provided
if [ -n "$CLOUD_SQL_CONNECTION_NAME" ]; then
    echo "🗄️  Waiting for Cloud SQL proxy..."
    # Cloud SQL proxy should be running as sidecar in Cloud Run
    until nc -z $(echo $CLOUD_SQL_CONNECTION_NAME | cut -d: -f1) 5432 2>/dev/null || true
    do
        echo "   Waiting for Cloud SQL..."
        sleep 2
    done
    echo "✅ Cloud SQL connected"
fi

# ==============================================================================
# Database Migration
# ==============================================================================

run_migrations() {
    echo "🗄️  Running database migrations..."
    if [ -f "/app/scripts/migrate.sh" ]; then
        chmod +x /app/scripts/migrate.sh
        /app/scripts/migrate.sh || echo "⚠️  Migration completed with warnings"
    else
        echo "ℹ️  No migrations to run"
    fi
}

# ==============================================================================
# Service Startup
# ==============================================================================

start_service() {
    local service=$1
    shift
    local args="$@"

    echo "🔧 Starting $service..."
    echo "   Command: $args"

    exec $args
}

# ==============================================================================
# Main Startup Logic
# ==============================================================================

case "${SERVICE_MODE:-unified}" in
    soma)
        echo "🧠 Starting Soma (Identity Core)..."
        exec python -m ippoc.soma.server --port ${PORT:-8081}
        ;;
    cortex)
        echo "🧠 Starting Cortex (Cognition Engine)..."
        exec python -m ippoc.cortex.server --port ${PORT:-8000}
        ;;
    memory)
        echo "🧠 Starting Mnemosyne (Memory Service)..."
        exec python -m ippoc.mnemosyne.server --port ${PORT:-8003}
        ;;
    unified|*)
        echo "🎯 Starting IPPOC Unified Service..."
        run_migrations
        exec python -m ippoc.cli.main run --mode cloud
        ;;
esac
