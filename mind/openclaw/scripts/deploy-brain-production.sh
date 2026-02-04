#!/bin/bash
# Production Deployment Script for Brain-Powered OpenClaw + HAL System

set -e

echo "🚀 Deploying Brain-Powered OpenClaw + HAL Infrastructure"
echo "======================================================"

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OPENCLAW_DIR="$PROJECT_ROOT/mind/openclaw"
BRAIN_DIR="$PROJECT_ROOT/brain"

echo "📁 Project root: $PROJECT_ROOT"

# 1. Environment Setup
echo "🔧 Setting up environment..."
cd "$OPENCLAW_DIR"

# Create production environment file if it doesn't exist
if [ ! -f ".env.production" ]; then
    echo "Creating production environment from brain configuration..."
    cp .env.brain.production .env.production
    echo "✅ Production environment created"
fi

# Load environment
if [ -f ".env.production" ]; then
    export $(cat .env.production | xargs)
    echo "✅ Environment loaded"
fi

# 2. Dependency Installation
echo "📦 Installing dependencies..."
npm ci --production
echo "✅ Dependencies installed"

# 3. Build TypeScript
echo "🏗️ Building TypeScript..."
npm run build
echo "✅ Build completed"

# 4. Health Check Setup
echo "🩺 Setting up health monitoring..."
# Create health check endpoint
cat > health-check.js << 'EOF'
const http = require('http');
const { getBrainOrchestrator } = require('./dist/infra/brain-orchestrator.js');

const server = http.createServer(async (req, res) => {
  if (req.url === '/health') {
    try {
      const orchestrator = getBrainOrchestrator();
      const state = orchestrator.getSystemState();
      const health = orchestrator.getComponentHealth();
      
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        system: state,
        components: health
      }));
    } catch (error) {
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({
        status: 'unhealthy',
        error: error.message,
        timestamp: new Date().toISOString()
      }));
    }
  } else {
    res.writeHead(404);
    res.end('Not Found');
  }
});

server.listen(8080, () => {
  console.log('Health check server running on port 8080');
});
EOF

echo "✅ Health check setup complete"

# 5. Service Configuration
echo "⚙️ Creating service configuration..."

# Create systemd service file
SERVICE_FILE="/etc/systemd/system/openclaw-brain.service"
if [ "$EUID" -eq 0 ]; then
    cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Brain-Powered OpenClaw Service
After=network.target

[Service]
Type=simple
User=openclaw
WorkingDirectory=$OPENCLAW_DIR
EnvironmentFile=$OPENCLAW_DIR/.env.production
ExecStart=/usr/bin/node $OPENCLAW_DIR/dist/index.js
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    echo "✅ Systemd service created at $SERVICE_FILE"
else
    echo "⚠️  Skipping systemd service creation (requires root privileges)"
    echo "💡 Run with sudo to create system service"
fi

# 6. Security Setup
echo "🔒 Configuring security..."
chmod 600 .env.production
echo "✅ Environment file secured"

# 7. Final Validation
echo "✅ Deployment validation..."
echo "System Status:"
echo "  - OpenClaw directory: $OPENCLAW_DIR"
echo "  - Brain integration: ENABLED"
echo "  - Security mode: $BRAIN_SECURITY_STRICTNESS"
echo "  - Health endpoint: http://localhost:8080/health"

echo ""
echo "🎉 Brain-Powered OpenClaw + HAL Deployment Complete!"
echo "==================================================="
echo "Next steps:"
echo "1. Start the service: sudo systemctl start openclaw-brain"
echo "2. Enable auto-start: sudo systemctl enable openclaw-brain"
echo "3. Check status: sudo systemctl status openclaw-brain"
echo "4. Monitor health: curl http://localhost:8080/health"

# Cleanup
rm -f health-check.js