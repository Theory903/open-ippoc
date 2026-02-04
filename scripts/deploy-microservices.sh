#!/bin/bash

set -e

echo "🚀 Deploying IPPOC Microservices..."

# Build and deploy
docker-compose -f docker-compose.microservices.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Register services with Consul
echo "📋 Registering services with service discovery..."

curl -X PUT -d '{
  "ID": "memory-service",
  "Name": "memory",
  "Address": "memory-service",
  "Port": 8000,
  "Check": {
    "HTTP": "http://memory-service:8000/health",
    "Interval": "10s"
  }
}' http://localhost:8500/v1/agent/service/register

curl -X PUT -d '{
  "ID": "cortex-service", 
  "Name": "cortex",
  "Address": "cortex-service",
  "Port": 8001,
  "Check": {
    "HTTP": "http://cortex-service:8001/health",
    "Interval": "10s"
  }
}' http://localhost:8500/v1/agent/service/register

curl -X PUT -d '{
  "ID": "openclaw-service",
  "Name": "body",
  "Address": "openclaw-service", 
  "Port": 18789,
  "Check": {
    "HTTP": "http://openclaw-service:18789/health",
    "Interval": "10s"
  }
}' http://localhost:8500/v1/agent/service/register

echo "✅ Microservices deployed successfully!"
echo "🌐 Access points:"
echo "  Gateway: http://localhost:10000"
echo "  Memory: http://localhost:8000"  
echo "  Cortex: http://localhost:8001"
echo "  Body: http://localhost:18789"
echo "  Consul UI: http://localhost:8500"