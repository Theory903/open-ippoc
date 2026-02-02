#!/bin/bash
export NODE_ID=${NODE_ID:-"ippoc-local"}
export IPPOC_API_KEY=${IPPOC_API_KEY:-"ippoc-secret-key"}

echo "🧠 Booting IPPOC Brain Node: $NODE_ID"
echo "🔑 Auth Enabled"

# Use uvicorn with asyncio loop to allow nest_asyncio patching (required for Tools)
uvicorn brain.cortex.server:app \
    --host 0.0.0.0 \
    --port 8001 \
    --loop asyncio \
    --reload
