#!/bin/bash
set -e

# Base HAL directory
HAL_ROOT="mind/openclaw/src/infra/hal"

echo "🚀 Initializing HAL Directory Structure..."

# Create HAL directories
mkdir -p "$HAL_ROOT/identity"
mkdir -p "$HAL_ROOT/execution"
mkdir -p "$HAL_ROOT/evolution"
mkdir -p "$HAL_ROOT/physiology"
mkdir -p "$HAL_ROOT/cognition"
mkdir -p "$HAL_ROOT/lifecycle"

echo "✅ Created directory structure in $HAL_ROOT"

# Create README
cat <<EOF > "$HAL_ROOT/README.md"
# HAL (Hard Autonomy Layer)

HAL is the sovereign constitutional layer that mediates between the IPPOC Brain (Mind) and the OpenClaw/Legacy Runtime (Body).

## Organs
- **Identity**: Sovereign Handshake & Trust
- **Execution**: Capability Tokens & Isolation
- **Physiology**: Health, Pain, & Local Models
- **Evolution**: Canon Scan & Semantic Merge
- **Cognition**: Founder Intelligence
EOF

echo "✅ Created HAL README.md"

# Install dependencies if not present
echo "📦 Checking and installing dependencies..."
cd mind/openclaw
if ! npm list @noble/ed25519 > /dev/null 2>&1; then
    echo "Installing @noble/ed25519..."
    npm install @noble/ed25519
else
    echo "@noble/ed25519 already installed."
fi

# Go back to root
cd ../..

echo "🎉 HAL Phase 1 Scaffolding Complete!"
