# 🚀 Sasya Arogya Engine - Observability Quick Start

Your Sasya Arogya Engine now has a complete OpenTelemetry observability stack! 

## ✅ What's Been Added

✅ **OpenTelemetry Integration** - Complete metrics, tracing, and logging  
✅ **Docker Observability Stack** - Prometheus + Grafana + Jaeger + OTel Collector  
✅ **CNN/ML Metrics Bridge** - Existing MLflow metrics now exported to OpenTelemetry  
✅ **LangGraph Instrumentation** - Node execution timing and workflow tracing  
✅ **FastAPI Metrics** - HTTP request metrics and performance monitoring  
✅ **Pre-built Dashboards** - System overview and ML performance dashboards  
✅ **Clean Integration** - Zero disruption to existing code, graceful fallback  

## 🏃‍♂️ Get Started in 3 Steps

### Step 1: Start the Observability Stack
```bash
cd observability
./start-observability.sh
```

### Step 2: Install Dependencies  
```bash
# If you get version compatibility errors, use the fix script:
cd observability && ./fix-otel-versions.sh

# Or install the simple requirements:
pip install -r observability/otel_requirements_simple.txt

# Original requirements (if no conflicts):
pip install -r observability/otel_requirements.txt
```

### Step 3: Run Your Application
```bash
python fsm_agent/run_fsm_server.py
```

## 🎯 Access Your Monitoring

- **📊 Grafana Dashboards**: http://localhost:3000 (admin/sasya-admin)
- **📈 Prometheus Metrics**: http://localhost:9090  
- **🔍 Distributed Tracing**: http://localhost:16686
- **📡 Application Metrics**: http://localhost:8080/metrics

## 📊 What You'll See

### System Metrics
- HTTP request rates and latency 
- Active session counts
- Error rates by component
- System resource usage

### ML Performance Metrics  
- CNN confidence score distributions
- Model inference latency (CNN vs SME)
- Classification throughput
- Uncertainty and entropy analysis
- Decision source tracking (CNN vs SME)

### LangGraph Workflow Metrics
- Individual node execution times
- Workflow completion rates  
- Session flow analysis
- Node-level error tracking

### Pre-built Dashboards
1. **Sasya Engine Overview** - System health and performance
2. **ML Performance** - Detailed CNN and model analysis

## 🔧 Key Features

- **🔄 MLflow Bridge**: Existing metrics automatically exported to OpenTelemetry
- **🎛️ Zero Configuration**: Works out-of-the-box with sensible defaults
- **🛡️ Graceful Fallback**: System runs normally if observability is unavailable
- **📈 Real-time Updates**: All dashboards update every 10 seconds
- **🔍 Distributed Tracing**: End-to-end request flow visibility

## 🛠️ Configuration (Optional)

Create a `.env` file to customize settings:
```bash
OTEL_SERVICE_NAME=sasya-arogya-engine
OTEL_SERVICE_VERSION=1.0.0  
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_ENABLE_TRACING=true
OTEL_ENABLE_METRICS=true
ENVIRONMENT=local
```

## 🚫 Stop the Stack

```bash
cd observability  
docker-compose down
# Or to remove all data:
docker-compose down -v
```

## 📖 Full Documentation

See `observability/README.md` for:
- Detailed configuration options
- Custom dashboard creation
- Troubleshooting guide  
- Advanced usage patterns

## 🎉 You're All Set!

Your plant disease diagnosis engine now has enterprise-grade observability. Monitor CNN performance, track LangGraph workflows, and analyze system performance in real-time!

## 🚨 Troubleshooting

**Error: `get_meter() got an unexpected keyword argument 'instrumenting_module_name'`**
```bash
cd observability && ./fix-otel-versions.sh
```

**Warning: `OpenTelemetry not available - observability setup skipped`**
```bash
pip install -r observability/otel_requirements_simple.txt
```

**No metrics showing in Grafana:**
1. Wait 1-2 minutes for initial data collection
2. Check that your app is running on port 8080
3. Visit http://localhost:8080/metrics to verify metrics endpoint

---

**Need help?** Check the detailed README in the `observability/` directory or examine the pre-configured dashboards for inspiration.
