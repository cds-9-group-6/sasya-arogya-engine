#!/bin/bash

# Sasya Arogya Engine - Observability Stack Startup Script
# This script starts the OpenTelemetry, Prometheus, and Grafana stack

set -e

echo "🚀 Starting Sasya Arogya Engine Observability Stack"
echo "=============================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose > /dev/null 2>&1 && ! command -v docker > /dev/null 2>&1; then
    echo "❌ Neither docker-compose nor docker compose is available."
    exit 1
fi

# Determine which compose command to use
if command -v docker-compose > /dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
else
    COMPOSE_CMD="docker compose"
fi

echo "📦 Using: $COMPOSE_CMD"

# Navigate to the observability directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "📍 Working directory: $SCRIPT_DIR"

# Create necessary directories for persistence
echo "📁 Creating data directories..."
mkdir -p data/prometheus data/grafana data/redis

# Set permissions for Grafana
echo "🔐 Setting up permissions..."
chmod 777 data/grafana 2>/dev/null || true

# Start the observability stack
echo "🏗️ Starting observability containers..."

$COMPOSE_CMD up -d --build

echo ""
echo "✅ Observability stack started successfully!"
echo ""
echo "🌐 Access URLs:"
echo "   📊 Grafana Dashboard:    http://localhost:3000"
echo "       Username: admin"
echo "       Password: sasya-admin"
echo ""
echo "   📈 Prometheus:           http://localhost:9090"
echo "   🔍 Jaeger (Tracing):     http://localhost:16686"
echo "   📡 OTel Collector:       http://localhost:13133/health"
echo ""
echo "🔧 Configuration:"
echo "   📊 Metrics Endpoint:     http://localhost:8080/metrics (once app is running)"
echo "   📡 OTLP gRPC:            localhost:4317"
echo "   📡 OTLP HTTP:            localhost:4318"
echo ""

# Wait for services to be healthy
echo "🏥 Checking service health..."
sleep 5

# Check Prometheus
if curl -s http://localhost:9090/-/healthy > /dev/null; then
    echo "   ✅ Prometheus is healthy"
else
    echo "   ⚠️  Prometheus is not responding yet"
fi

# Check Grafana
if curl -s http://localhost:3000/api/health > /dev/null; then
    echo "   ✅ Grafana is healthy"
else
    echo "   ⚠️  Grafana is not responding yet"
fi

# Check OTel Collector
if curl -s http://localhost:13133 > /dev/null; then
    echo "   ✅ OpenTelemetry Collector is healthy"
else
    echo "   ⚠️  OpenTelemetry Collector is not responding yet"
fi

echo ""
echo "📋 Next Steps:"
echo "   1. Install OpenTelemetry dependencies:"
echo "      pip install -r observability/otel_requirements.txt"
echo ""
echo "   2. Start your Sasya Engine application:"
echo "      python fsm_agent/run_fsm_server.py"
echo ""
echo "   3. Visit Grafana at http://localhost:3000 to view dashboards"
echo ""
echo "📖 To view logs: $COMPOSE_CMD logs -f"
echo "🛑 To stop:      $COMPOSE_CMD down"
echo "🗑️  To clean:     $COMPOSE_CMD down -v"
echo ""
echo "Happy monitoring! 🎉"
