# 🚀 Deployment Guide - Sasya Arogya Engine

Complete deployment instructions for development, staging, and production environments.

## 📋 Prerequisites

### System Requirements
- **CPU**: 4+ cores (8+ recommended for production)
- **RAM**: 8GB minimum (16GB+ recommended)
- **Storage**: 50GB+ SSD
- **GPU**: Optional (for faster ML inference)
- **OS**: Linux (Ubuntu 20.04+), macOS, Windows with WSL2

### Software Dependencies
- **Python**: 3.11+
- **Docker/Podman**: Latest stable
- **UV**: Python package manager
- **Git**: Version control

## 🔧 Development Setup

### 1. Clone Repositories
```bash
# Main engine
git clone <sasya-arogya-engine-repo>
cd sasya-arogya-engine

# MCP server (in separate terminal/directory)
git clone <sasya-arogya-mcp-repo>
cd sasya-arogya-mcp
```

### 2. Environment Setup
```bash
# Engine setup
cd sasya-arogya-engine
uv init
source .venv/bin/activate

# Install dependencies
uv add fastapi uvicorn python-multipart
uv pip install -r requirements.txt

# MCP server setup  
cd ../sasya-arogya-mcp
pip install -r requirements.txt
```

### 3. Configuration Files

#### `.env` for Engine
```env
# LLM Services
OLLAMA_BASE_URL=http://localhost:11434
PRESCRIPTION_ENGINE_URL=http://localhost:8081

# Insurance Services
SASYA_AROGYA_MCP_URL=http://localhost:8001

# ML Services
MLFLOW_TRACKING_URI=http://localhost:5000

# Debug/Development
DEBUG=true
LOG_LEVEL=INFO
```

#### `.env` for MCP Server
```env
# Server Configuration
PORT=8001
HOST=0.0.0.0

# Insurance Data
INSURANCE_DB_PATH=./data/insurance.db
COMPANIES_DATA_PATH=./data/companies.json

# Debug/Development  
DEBUG=true
LOG_LEVEL=INFO
```

### 4. Start Services

#### Terminal 1: Start Ollama
```bash
# Install Ollama (if not installed)
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama server
ollama serve

# Pull required models (new terminal)
ollama pull llama3.1:8b
ollama pull codellama:7b
```

#### Terminal 2: Start MCP Server
```bash
cd sasya-arogya-mcp
python mcp_http_server.py --port 8001
```

#### Terminal 3: Start Prescription RAG (if available)
```bash
cd prescription-rag
# Follow prescription-rag README instructions
python app.py --port 8081
```

#### Terminal 4: Start MLflow (optional)
```bash
mlflow server --host 127.0.0.1 --port 5000
```

#### Terminal 5: Start Main Engine
```bash
cd sasya-arogya-engine
source .venv/bin/activate
uvicorn api.agent_api:app --host 0.0.0.0 --port 8080 --reload
```

### 5. Verify Setup
```bash
# Check engine health
curl http://localhost:8080/health

# Check MCP server  
curl http://localhost:8001/health

# Check Ollama
curl http://localhost:11434/api/tags

# Test full workflow
curl -X POST http://localhost:8080/chat-stream \
  -H "Content-Type: application/json" \
  -d '{"message": "I need crop insurance for my wheat farm", "session_id": "test-123"}'
```

## 🐳 Container Deployment

### 1. Build Images

#### Engine Container
```bash
# Build engine image
cd sasya-arogya-engine
docker build -f docker/Dockerfile.engine -t sasya-engine:latest .

# Or use provided script
./compile-and-create-image.sh
```

#### MCP Server Container  
```bash
cd sasya-arogya-mcp
docker build -t sasya-mcp:latest .
```

### 2. Docker Compose Setup

#### `docker-compose.yml`
```yaml
version: '3.8'

services:
  ollama:
    image: ollama/ollama:latest
    container_name: sasya-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0
    
  mcp-server:
    image: sasya-mcp:latest
    container_name: sasya-mcp
    ports:
      - "8001:8001"
    environment:
      - PORT=8001
      - HOST=0.0.0.0
    volumes:
      - ./mcp-data:/app/data
    depends_on:
      - ollama
      
  prescription-rag:
    image: prescription-rag:latest  # If available
    container_name: sasya-prescription
    ports:
      - "8081:8081"
    environment:
      - CHROMA_HOST=chroma
      - OLLAMA_HOST=ollama:11434
    depends_on:
      - ollama
      - chroma
      
  chroma:
    image: chromadb/chroma:latest
    container_name: sasya-chroma
    ports:
      - "8000:8000"
    volumes:
      - chroma_data:/chroma/chroma
      
  mlflow:
    image: python:3.11-slim
    container_name: sasya-mlflow
    ports:
      - "5000:5000"
    command: |
      bash -c "pip install mlflow && 
               mlflow server --host 0.0.0.0 --port 5000 --backend-store-uri sqlite:///mlflow.db"
    volumes:
      - mlflow_data:/mlflow
      
  engine:
    image: sasya-engine:latest
    container_name: sasya-engine
    ports:
      - "8080:8080"
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
      - SASYA_AROGYA_MCP_URL=http://mcp-server:8001
      - PRESCRIPTION_ENGINE_URL=http://prescription-rag:8081
      - MLFLOW_TRACKING_URI=http://mlflow:5000
    depends_on:
      - ollama
      - mcp-server
      - prescription-rag
      - mlflow
    volumes:
      - ./logs:/app/logs

volumes:
  ollama_data:
  chroma_data:
  mlflow_data:
```

#### Start Full Stack
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f engine

# Scale services (if needed)
docker-compose up -d --scale engine=3
```

### 3. Container Health Checks
```bash
# Check all services
docker-compose ps

# Individual service health
docker exec sasya-engine curl http://localhost:8080/health
docker exec sasya-mcp curl http://localhost:8001/health
```

## ☸️ Kubernetes Deployment

### 1. Kubernetes Manifests

#### `k8s/namespace.yaml`
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: sasya-arogya
```

#### `k8s/configmap.yaml`
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: sasya-config
  namespace: sasya-arogya
data:
  OLLAMA_BASE_URL: "http://ollama-service:11434"
  SASYA_AROGYA_MCP_URL: "http://mcp-service:8001"
  PRESCRIPTION_ENGINE_URL: "http://prescription-service:8081"
  MLFLOW_TRACKING_URI: "http://mlflow-service:5000"
```

#### `k8s/engine-deployment.yaml`
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sasya-engine
  namespace: sasya-arogya
spec:
  replicas: 3
  selector:
    matchLabels:
      app: sasya-engine
  template:
    metadata:
      labels:
        app: sasya-engine
    spec:
      containers:
      - name: engine
        image: sasya-engine:latest
        ports:
        - containerPort: 8080
        envFrom:
        - configMapRef:
            name: sasya-config
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: engine-service
  namespace: sasya-arogya
spec:
  selector:
    app: sasya-engine
  ports:
  - port: 8080
    targetPort: 8080
  type: LoadBalancer
```

#### `k8s/mcp-deployment.yaml`
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sasya-mcp
  namespace: sasya-arogya
spec:
  replicas: 2
  selector:
    matchLabels:
      app: sasya-mcp
  template:
    metadata:
      labels:
        app: sasya-mcp
    spec:
      containers:
      - name: mcp
        image: sasya-mcp:latest
        ports:
        - containerPort: 8001
        env:
        - name: PORT
          value: "8001"
        - name: HOST
          value: "0.0.0.0"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: mcp-service
  namespace: sasya-arogya
spec:
  selector:
    app: sasya-mcp
  ports:
  - port: 8001
    targetPort: 8001
```

### 2. Deploy to Kubernetes
```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Apply configurations
kubectl apply -f k8s/configmap.yaml

# Deploy services
kubectl apply -f k8s/mcp-deployment.yaml
kubectl apply -f k8s/engine-deployment.yaml

# Check deployments
kubectl get pods -n sasya-arogya
kubectl get services -n sasya-arogya

# View logs
kubectl logs -f deployment/sasya-engine -n sasya-arogya
```

### 3. Production Considerations

#### Ingress Configuration
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: sasya-ingress
  namespace: sasya-arogya
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - api.sasyaarogya.com
    secretName: sasya-tls
  rules:
  - host: api.sasyaarogya.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: engine-service
            port:
              number: 8080
```

#### Horizontal Pod Autoscaler
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: sasya-engine-hpa
  namespace: sasya-arogya
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: sasya-engine
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## 🔍 Monitoring & Observability

### 1. Health Check Endpoints
```bash
# Engine health
GET /health
GET /status

# MCP server health
GET /health

# Ollama health
GET /api/tags
```

### 2. Metrics Collection

#### Prometheus Configuration
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'sasya-engine'
    static_configs:
      - targets: ['engine-service:8080']
    metrics_path: '/metrics'
    
  - job_name: 'sasya-mcp'
    static_configs:
      - targets: ['mcp-service:8001']
    metrics_path: '/metrics'
```

#### Grafana Dashboard
- **Request Rate**: Requests per second
- **Response Time**: 95th percentile latency  
- **Error Rate**: 4xx and 5xx responses
- **System Metrics**: CPU, memory, disk usage
- **Business Metrics**: Insurance conversions, session duration

### 3. Logging

#### Structured Logging Format
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "logger": "fsm_agent.core.nodes.insurance_node",
  "message": "Insurance request processed successfully",
  "session_id": "abc123",
  "user_id": "user456", 
  "service": "insurance",
  "response_time_ms": 1250,
  "context": {
    "crop": "wheat",
    "area_hectare": 5.0,
    "state": "Punjab"
  }
}
```

#### Log Aggregation Stack
```bash
# ELK Stack with Docker Compose
version: '3.8'
services:
  elasticsearch:
    image: elasticsearch:7.14.0
    environment:
      - discovery.type=single-node
    ports:
      - "9200:9200"
      
  kibana:
    image: kibana:7.14.0
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch
      
  logstash:
    image: logstash:7.14.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    depends_on:
      - elasticsearch
```

## 🔒 Security & Production Hardening

### 1. Environment Security
```bash
# Use secrets management
kubectl create secret generic sasya-secrets \
  --from-literal=database-password=secretpass \
  --from-literal=api-key=secretkey

# Apply network policies
kubectl apply -f k8s/network-policy.yaml
```

### 2. API Security
- **Rate Limiting**: 100 requests/minute per IP
- **CORS**: Configured for allowed origins
- **Input Validation**: Comprehensive request validation
- **Authentication**: API key or JWT tokens
- **HTTPS**: TLS encryption for all endpoints

### 3. Data Security  
- **Encryption at Rest**: Database and file storage
- **Encryption in Transit**: HTTPS/TLS for all communications
- **Data Retention**: Automatic cleanup of old sessions
- **Privacy**: No PII stored without consent

## 📊 Performance Tuning

### 1. Application Optimization
```python
# FastAPI configuration
app = FastAPI(
    title="Sasya Arogya Engine",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Connection pooling
from sqlalchemy import create_engine
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True
)

# Caching
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_cached_response(query_hash):
    return process_query(query_hash)
```

### 2. Infrastructure Optimization
- **Load Balancing**: Multiple engine replicas
- **Caching**: Redis for session data
- **CDN**: Static asset delivery
- **Database**: Connection pooling and read replicas

### 3. ML Model Optimization
- **Model Quantization**: Reduce model size
- **Batch Processing**: Process multiple requests together  
- **GPU Acceleration**: For faster inference
- **Model Caching**: Keep models in memory

## 🚨 Troubleshooting Guide

### Common Issues

#### 1. Engine Won't Start
```bash
# Check dependencies
docker-compose logs engine

# Verify environment variables
kubectl describe pod sasya-engine-xxx -n sasya-arogya

# Test connectivity
curl -v http://localhost:8080/health
```

#### 2. MCP Server Connection Failed
```bash
# Check MCP server status  
curl http://localhost:8001/health

# Verify network connectivity
kubectl exec -it sasya-engine-xxx -- curl http://mcp-service:8001/health

# Check firewall rules
netstat -tlnp | grep 8001
```

#### 3. Ollama Model Issues
```bash
# Pull required models
ollama pull llama3.1:8b

# Check model status
ollama list

# Test model inference
curl http://localhost:11434/api/generate -d '{"model": "llama3.1:8b", "prompt": "test"}'
```

#### 4. High Memory Usage
```bash
# Check resource usage
kubectl top pods -n sasya-arogya

# Increase memory limits
kubectl patch deployment sasya-engine -n sasya-arogya \
  -p '{"spec":{"template":{"spec":{"containers":[{"name":"engine","resources":{"limits":{"memory":"4Gi"}}}]}}}}'

# Clear caches
kubectl exec -it sasya-engine-xxx -- python -c "import gc; gc.collect()"
```

### Monitoring Commands
```bash
# Resource monitoring
kubectl top nodes
kubectl top pods -n sasya-arogya

# Log monitoring  
kubectl logs -f deployment/sasya-engine -n sasya-arogya | grep ERROR

# Network monitoring
kubectl exec -it sasya-engine-xxx -- netstat -tlnp

# Performance testing
ab -n 1000 -c 10 http://localhost:8080/health
```

This deployment guide provides comprehensive instructions for setting up Sasya Arogya Engine in various environments, from local development to production Kubernetes clusters.
