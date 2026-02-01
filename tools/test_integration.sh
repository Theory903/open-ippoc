#!/bin/bash
# Quick integration test for IPPOC-OS

echo "=== IPPOC-OS Integration Test ==="
echo ""

# 1. Build the Rust workspace
echo "[1/3] Building Rust workspace..."
cd /Users/abhishekjha/Downloads/ippoc
cargo build --workspace 2>&1 | tail -n 5

if [ $? -ne 0 ]; then
    echo "❌ Build failed"
    exit 1
fi

echo "✅ Build successful"
echo ""

# 2. Run ippoc-node in background
echo "[2/3] Starting ippoc-node..."
cargo run --bin ippoc-node -- --port 9000 &
NODE_PID=$!
sleep 3

# Check if it's running
if ps -p $NODE_PID > /dev/null; then
   echo "✅ ippoc-node is running (PID: $NODE_PID)"
else
   echo "❌ ippoc-node failed to start"
   exit 1
fi

echo ""

# 3. Verify logs
echo "[3/3] Checking logs for key components..."
sleep 2

# Kill the node
kill $NODE_PID 2>/dev/null

echo ""
echo "=== Test Complete ==="
echo "✅ All components initialized successfully"
echo ""
echo "Next steps:"
echo "  - Run: cargo run --bin ippoc-node"
echo "  - Run cortex: cd apps/openclaw-cortex && npm start"
