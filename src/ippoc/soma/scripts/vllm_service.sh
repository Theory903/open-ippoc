#!/bin/bash
PORT=$1
MODEL="microsoft/Phi-4-reasoning-plus" // Assuming user has this locally or it auto-downloads

echo "Taking off... Launching vLLM with $MODEL on port $PORT"

# Check if python/vllm is available (simplified)
if ! command -v vllm &> /dev/null; then
    echo "Error: vllm not found in PATH"
    exit 1
fi

# Launch
exec vllm serve $MODEL \
    --port $PORT \
    --trust-remote-code \
    --dtype auto \
    --enable-reasoning \
    --reasoning-parser deepseek_r1
