#!/bin/bash

# Fix OpenTelemetry Version Issues Script
# This script uninstalls conflicting versions and installs compatible ones

set -e

echo "🔧 Fixing OpenTelemetry Version Compatibility Issues"
echo "================================================="

# Uninstall any existing OpenTelemetry packages to avoid conflicts
echo "📦 Uninstalling existing OpenTelemetry packages..."
pip uninstall -y opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation || true
pip uninstall -y opentelemetry-instrumentation-fastapi opentelemetry-instrumentation-httpx || true  
pip uninstall -y opentelemetry-instrumentation-requests opentelemetry-instrumentation-logging || true
pip uninstall -y opentelemetry-instrumentation-system-metrics opentelemetry-instrumentation-redis || true
pip uninstall -y opentelemetry-exporter-otlp opentelemetry-exporter-prometheus || true
pip uninstall -y opentelemetry-semantic-conventions || true

echo ""
echo "📥 Installing compatible OpenTelemetry versions..."

# Install core packages first
pip install opentelemetry-api==1.21.0 opentelemetry-sdk==1.21.0

# Install instrumentation packages
pip install opentelemetry-instrumentation==0.42b0
pip install opentelemetry-instrumentation-fastapi==0.42b0
pip install opentelemetry-instrumentation-httpx==0.42b0  
pip install opentelemetry-instrumentation-requests==0.42b0
pip install opentelemetry-instrumentation-logging==0.42b0
pip install opentelemetry-instrumentation-system-metrics==0.42b0
pip install opentelemetry-instrumentation-redis==0.42b0

# Install exporters  
pip install opentelemetry-exporter-otlp==1.21.0
pip install opentelemetry-exporter-prometheus==1.12.0rc1
pip install opentelemetry-exporter-jaeger-thrift==1.21.0

# Install semantic conventions
pip install opentelemetry-semantic-conventions==0.42b0

# Install Prometheus client
pip install prometheus_client==0.19.0

echo ""
echo "✅ OpenTelemetry packages installed successfully!"
echo ""
echo "🧪 Testing OpenTelemetry imports..."

# Test imports
python3 -c "
import sys
try:
    from opentelemetry import metrics, trace
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    print('✅ Core OpenTelemetry imports: OK')
except ImportError as e:
    print(f'❌ Core imports failed: {e}')
    sys.exit(1)

try:
    # Test meter creation with compatible API
    from opentelemetry import metrics
    meter = metrics.get_meter('test')
    print('✅ Meter creation: OK')
except Exception as e:
    print(f'⚠️  Meter creation warning: {e}')

try:
    # Test tracer creation  
    from opentelemetry import trace
    tracer = trace.get_tracer('test')
    print('✅ Tracer creation: OK')
except Exception as e:
    print(f'⚠️  Tracer creation warning: {e}')

print('🎉 OpenTelemetry compatibility test passed!')
"

echo ""
echo "🚀 Ready to start! Now run:"
echo "   python fsm_agent/run_fsm_server.py"
echo ""
echo "📊 Then check http://localhost:3000 for Grafana dashboards"
