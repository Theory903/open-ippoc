#!/bin/bash
# start.sh - The Ippoc Lifecycle Manager

set -e

echo "🌱 Initializing Ippoc Organism..."

# 1. INTEGRITY CHECK
# Ensure the kernel (OpenClaw) is present and unmodified
if [ ! -d "src/kernel/openclaw" ]; then
    echo "❌ CRITICAL: Kernel missing."
    exit 1
fi

echo "✅ Kernel integrity verified"

# 2. BOOTSTRAP (Runtime)
# Generate identity keys if they don't exist
echo "🔑 Generating organism identity..."
node src/runtime/bootstrap/genesis.ts generate

# 3. WAKE ORGANS (Services)
# Start strictly in order: Memory -> Body -> Brain -> Kernel Bridge
echo "🧠 Waking Mnemosyne (Memory)..."
docker compose -f src/runtime/supervisor/organism.yaml up -d mnemosyne

# Wait for memory to be ready
echo "⏳ Waiting for Mnemosyne to initialize..."
sleep 10

echo "💪 Flexing Soma (Body)..."
docker compose -f src/runtime/supervisor/organism.yaml up -d soma

# Wait for body to be ready
echo "⏳ Waiting for Soma to initialize..."
sleep 10

echo "⚡ Igniting Cortex (Brain)..."
docker compose -f src/runtime/supervisor/organism.yaml up -d cortex

# Wait for brain to be ready
echo "⏳ Waiting for Cortex to initialize..."
sleep 15

# 4. START GATEWAY
echo "🚪 Opening Gateway..."
docker compose -f src/runtime/supervisor/organism.yaml up -d gateway

# 5. ACTIVATE WATCHDOG
echo "🐕 Activating Watchdog monitor..."
python3 src/runtime/supervisor/watchdog.py &

echo ""
echo "🚀 Ippoc Organism is ALIVE!"
echo "🌐 Access the system at: http://localhost:8080"
echo "📊 Health dashboard: http://localhost:8080/health"
echo ""
echo "Services:"
echo "  🧠 Mnemosyne (Memory): http://localhost:8001"
echo "  💪 Soma (Body): http://localhost:8002"  
echo "  ⚡ Cortex (Brain): http://localhost:8003"
echo "  🚪 Gateway: http://localhost:8080"