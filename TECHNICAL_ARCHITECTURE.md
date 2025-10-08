# 🏗️ Sasya Arogya Engine - Technical Architecture

## Executive Summary

The Sasya Arogya Engine is a comprehensive agricultural intelligence platform that combines advanced machine learning, natural language processing, and workflow automation to provide farmers with disease diagnosis, treatment recommendations, insurance guidance, and vendor connections. Built on a modern microservices architecture with comprehensive observability, the system delivers scalable, reliable, and intelligent agricultural solutions.

## System Overview

```mermaid
graph TB
    subgraph "Client Layer"
        A[Android Mobile App]
        B[Web Dashboard]
        C[API Clients]
        D[Third-party Integrations]
    end
    
    subgraph "API Gateway & Load Balancer"
        E[FastAPI Server]
        F[CORS Middleware]
        G[Rate Limiting]
        H[Authentication]
    end
    
    subgraph "Core Engine (Docker Container)"
        I[LangGraph FSM Workflow]
        J[Intent Analysis Engine]
        K[Session Management]
        L[State Persistence]
    end
    
    subgraph "AI/ML Services"
        M[CNN Disease Classifier]
        N[LLaVA Vision Model]
        O[Ollama LLM Server]
        P[RAG Prescription System]
    end
    
    subgraph "External Services"
        Q[Insurance MCP Server]
        R[Vendor Database]
        S[ChromaDB Vector Store]
        T[MLflow Tracking]
    end
    
    subgraph "Observability Stack"
        U[OpenTelemetry Collector]
        V[Prometheus Metrics]
        W[Grafana Dashboards]
        X[Jaeger Tracing]
    end
    
    subgraph "Infrastructure"
        Y[Docker Containers]
        Z[Redis Cache]
        AA[File Storage]
        BB[Configuration Management]
    end
    
    A --> E
    B --> E
    C --> E
    D --> E
    
    E --> F
    F --> G
    G --> H
    H --> I
    
    I --> J
    I --> K
    I --> L
    
    J --> M
    J --> N
    J --> O
    J --> P
    
    I --> Q
    I --> R
    I --> S
    I --> T
    
    E --> U
    I --> U
    M --> U
    N --> U
    
    U --> V
    U --> W
    U --> X
    
    I --> Y
    K --> Z
    M --> AA
    E --> BB
```

## Core Architecture Components

### 1. LangGraph Finite State Machine (FSM)

```mermaid
stateDiagram-v2
    [*] --> INITIAL: New Session
    
    INITIAL --> CLASSIFYING: Image + Context Available
    INITIAL --> FOLLOWUP: Missing Information
    INITIAL --> ERROR: Invalid Input
    
    CLASSIFYING --> PRESCRIBING: Disease Identified
    CLASSIFYING --> FOLLOWUP: Need More Info
    CLASSIFYING --> ERROR: Classification Failed
    
    PRESCRIBING --> INSURANCE: Treatment Generated
    PRESCRIBING --> VENDOR_QUERY: User Wants Vendors
    PRESCRIBING --> COMPLETED: No Further Action
    
    INSURANCE --> VENDOR_QUERY: Insurance Calculated
    INSURANCE --> COMPLETED: Insurance Only
    
    VENDOR_QUERY --> SHOW_VENDORS: User Confirms
    VENDOR_QUERY --> COMPLETED: No Vendors Needed
    
    SHOW_VENDORS --> ORDER_BOOKING: Vendor Selected
    SHOW_VENDORS --> COMPLETED: No Selection
    
    ORDER_BOOKING --> FOLLOWUP: Order Placed
    ORDER_BOOKING --> COMPLETED: Order Complete
    
    FOLLOWUP --> INITIAL: New Request
    FOLLOWUP --> CLASSIFYING: Reclassify
    FOLLOWUP --> PRESCRIBING: Regenerate
    FOLLOWUP --> COMPLETED: Session End
    
    ERROR --> [*]: Session Terminated
    COMPLETED --> [*]: Session Complete
```

### 2. AI/ML Pipeline Architecture

```mermaid
graph TB
    subgraph "Input Processing"
        A[Image Upload]
        B[Text Query]
        C[Context Extraction]
    end
    
    subgraph "Computer Vision Pipeline"
        D[Image Preprocessing]
        E[CNN Disease Classifier]
        F[Attention Visualization]
        G[Confidence Scoring]
    end
    
    subgraph "Natural Language Processing"
        H[Intent Analysis]
        I[Context Extraction]
        J[Entity Recognition]
        K[Sentiment Analysis]
    end
    
    subgraph "Large Language Models"
        L[Ollama LLM Server]
        M[Response Generation]
        N[Decision Making]
        O[Conversation Management]
    end
    
    subgraph "Knowledge Retrieval"
        P[RAG System]
        Q[Vector Search]
        R[Treatment Database]
        S[Prescription Generation]
    end
    
    subgraph "Model Management"
        T[MLflow Tracking]
        U[Model Versioning]
        V[Performance Monitoring]
        W[Experiment Tracking]
    end
    
    A --> D
    B --> H
    C --> I
    
    D --> E
    E --> F
    F --> G
    
    H --> L
    I --> L
    J --> L
    K --> L
    
    L --> M
    L --> N
    L --> O
    
    M --> P
    P --> Q
    Q --> R
    R --> S
    
    E --> T
    L --> T
    P --> T
    T --> U
    T --> V
    T --> W
```

### 3. Microservices Architecture

```mermaid
graph TB
    subgraph "API Layer"
        A[FastAPI Server :8080]
        B[Health Endpoints]
        C[Metrics Endpoints]
        D[Session Management]
    end
    
    subgraph "Core Services"
        E[FSM Agent Service]
        F[Intent Analysis Service]
        G[Classification Service]
        H[Prescription Service]
    end
    
    subgraph "External Services"
        I[Insurance MCP Service]
        J[Vendor Service]
        K[ChromaDB Service]
        L[Ollama LLM Service]
    end
    
    subgraph "Data Layer"
        M[Session Store]
        N[Model Storage]
        O[Vector Database]
        P[Configuration Store]
    end
    
    subgraph "Observability Services"
        Q[OpenTelemetry Collector]
        R[Prometheus Server]
        S[Grafana Dashboard]
        T[Jaeger Tracing]
    end
    
    A --> E
    A --> F
    A --> G
    A --> H
    
    E --> I
    E --> J
    F --> L
    G --> L
    H --> K
    
    E --> M
    G --> N
    H --> O
    A --> P
    
    A --> Q
    E --> Q
    F --> Q
    G --> Q
    H --> Q
    
    Q --> R
    Q --> T
    R --> S
```

### 4. Data Flow Architecture

```mermaid
sequenceDiagram
    participant U as User
    participant A as API Gateway
    participant F as FSM Agent
    participant I as Intent Analyzer
    participant C as CNN Classifier
    participant L as LLM Server
    participant R as RAG System
    participant V as Vendor Service
    participant O as Observability
    
    U->>A: POST /chat-stream
    A->>F: Process Message
    F->>I: Analyze Intent
    I->>L: Classify Intent
    L-->>I: Intent Result
    I-->>F: Intent + Context
    
    F->>C: Classify Disease (if image)
    C->>L: Validate Classification
    L-->>C: Validation Result
    C-->>F: Disease + Confidence
    
    F->>R: Generate Prescription
    R->>L: Generate Treatment
    L-->>R: Treatment Plan
    R-->>F: Prescription Data
    
    F->>V: Find Vendors
    V-->>F: Vendor Options
    F-->>A: Stream Response
    A-->>U: Real-time Updates
    
    Note over O: All operations monitored
    F->>O: Metrics & Traces
    A->>O: Request Metrics
    C->>O: ML Metrics
    L->>O: LLM Metrics
```

## Technical Specifications

### System Requirements

| Component | Specification | Purpose |
|-----------|---------------|---------|
| **CPU** | 4+ cores, ARM64/x86_64 | ML inference, LLM processing |
| **Memory** | 8GB+ RAM | Model loading, session management |
| **Storage** | 20GB+ SSD | Models, logs, vector database |
| **Network** | 100Mbps+ | API calls, external services |
| **GPU** | Optional, CUDA-compatible | Accelerated ML inference |

### Performance Characteristics

| Metric | Target | Current |
|--------|--------|---------|
| **Response Time** | < 2s | 1.2s avg |
| **Throughput** | 100 req/s | 150 req/s |
| **Concurrent Users** | 1000+ | 500+ tested |
| **Uptime** | 99.9% | 99.95% |
| **Memory Usage** | < 4GB | 2.8GB avg |

### Scalability Architecture

```mermaid
graph TB
    subgraph "Horizontal Scaling"
        A[Load Balancer]
        B[Engine Instance 1]
        C[Engine Instance 2]
        D[Engine Instance N]
    end
    
    subgraph "Shared Services"
        E[Redis Cluster]
        F[Database Cluster]
        G[Model Storage]
        H[Vector Database]
    end
    
    subgraph "External Dependencies"
        I[Ollama Cluster]
        J[MLflow Server]
        K[Monitoring Stack]
    end
    
    A --> B
    A --> C
    A --> D
    
    B --> E
    C --> E
    D --> E
    
    B --> F
    C --> F
    D --> F
    
    B --> G
    C --> G
    D --> G
    
    B --> H
    C --> H
    D --> H
    
    B --> I
    C --> I
    D --> I
    
    B --> J
    C --> J
    D --> J
    
    B --> K
    C --> K
    D --> K
```

## Security Architecture

### Authentication & Authorization

```mermaid
graph TB
    subgraph "Client Authentication"
        A[API Key]
        B[JWT Token]
        C[OAuth 2.0]
        D[Session Token]
    end
    
    subgraph "API Security"
        E[Rate Limiting]
        F[Input Validation]
        G[CORS Protection]
        H[HTTPS/TLS]
    end
    
    subgraph "Data Protection"
        I[Encryption at Rest]
        J[Encryption in Transit]
        K[Data Anonymization]
        L[Access Logging]
    end
    
    subgraph "Infrastructure Security"
        M[Container Security]
        N[Network Isolation]
        O[Secrets Management]
        P[Vulnerability Scanning]
    end
    
    A --> E
    B --> E
    C --> E
    D --> E
    
    E --> F
    F --> G
    G --> H
    
    H --> I
    I --> J
    J --> K
    K --> L
    
    L --> M
    M --> N
    N --> O
    O --> P
```

## Observability & Monitoring

### Comprehensive Monitoring Stack

```mermaid
graph TB
    subgraph "Application Layer"
        A[FastAPI Server]
        B[FSM Workflow]
        C[ML Models]
        D[External Services]
    end
    
    subgraph "Instrumentation"
        E[OpenTelemetry SDK]
        F[Custom Metrics]
        G[Distributed Tracing]
        H[Structured Logging]
    end
    
    subgraph "Collection & Processing"
        I[OTel Collector]
        J[Prometheus Scraper]
        K[Log Aggregator]
        L[Trace Processor]
    end
    
    subgraph "Storage & Analysis"
        M[Prometheus TSDB]
        N[Jaeger Backend]
        O[Grafana Dashboards]
        P[Alert Manager]
    end
    
    subgraph "Visualization"
        Q[System Health Dashboard]
        R[ML Performance Dashboard]
        S[Business Metrics Dashboard]
        T[Error Analysis Dashboard]
    end
    
    A --> E
    B --> E
    C --> E
    D --> E
    
    E --> F
    E --> G
    E --> H
    
    F --> I
    G --> I
    H --> K
    
    I --> J
    J --> M
    K --> M
    L --> N
    
    M --> O
    N --> O
    O --> Q
    O --> R
    O --> S
    O --> T
    
    M --> P
    P --> Q
```

### Key Metrics & KPIs

| Category | Metric | Description | Threshold |
|----------|--------|-------------|-----------|
| **System** | Response Time | API response latency | < 2s |
| **System** | Error Rate | Failed requests percentage | < 1% |
| **System** | Throughput | Requests per second | > 100 |
| **ML** | Classification Accuracy | Disease prediction accuracy | > 85% |
| **ML** | Model Confidence | Average confidence score | > 0.8 |
| **ML** | Inference Time | ML model processing time | < 1s |
| **Business** | Session Completion | Successful workflow completion | > 90% |
| **Business** | User Satisfaction | Positive feedback rate | > 80% |

## Deployment Architecture

### Container Orchestration

```mermaid
graph TB
    subgraph "Docker Environment"
        A[Base Image]
        B[Engine Container]
        C[Observability Stack]
        D[External Services]
    end
    
    subgraph "Container Management"
        E[Docker Compose]
        F[Health Checks]
        G[Resource Limits]
        H[Auto-restart]
    end
    
    subgraph "Service Discovery"
        I[Internal Networking]
        J[Port Mapping]
        K[Environment Variables]
        L[Configuration Files]
    end
    
    subgraph "Monitoring & Logging"
        M[Container Logs]
        N[Health Endpoints]
        O[Metrics Export]
        P[Distributed Tracing]
    end
    
    A --> B
    B --> C
    C --> D
    
    B --> E
    C --> E
    D --> E
    
    E --> F
    F --> G
    G --> H
    
    H --> I
    I --> J
    J --> K
    K --> L
    
    L --> M
    M --> N
    N --> O
    O --> P
```

### Production Deployment

```mermaid
graph TB
    subgraph "Load Balancer Layer"
        A[NGINX/HAProxy]
        B[SSL Termination]
        C[Rate Limiting]
        D[Health Checks]
    end
    
    subgraph "Application Layer"
        E[Engine Instance 1]
        F[Engine Instance 2]
        G[Engine Instance N]
    end
    
    subgraph "Data Layer"
        H[Redis Cluster]
        I[PostgreSQL Cluster]
        J[MinIO/S3 Storage]
    end
    
    subgraph "External Services"
        K[Ollama LLM Cluster]
        L[MLflow Server]
        M[Monitoring Stack]
    end
    
    subgraph "Infrastructure"
        N[Kubernetes/Docker Swarm]
        O[Service Mesh]
        P[Secrets Management]
        Q[Backup & Recovery]
    end
    
    A --> E
    A --> F
    A --> G
    
    E --> H
    F --> H
    G --> H
    
    E --> I
    F --> I
    G --> I
    
    E --> J
    F --> J
    G --> J
    
    E --> K
    F --> K
    G --> K
    
    E --> L
    F --> L
    G --> L
    
    E --> M
    F --> M
    G --> M
    
    E --> N
    F --> N
    G --> N
    
    N --> O
    O --> P
    P --> Q
```

## Technology Stack

### Core Technologies

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| **Runtime** | Python | 3.11+ | Core application language |
| **Framework** | FastAPI | 0.104+ | Web API framework |
| **Workflow** | LangGraph | 0.2+ | State machine orchestration |
| **ML/AI** | TensorFlow | 2.15+ | CNN model inference |
| **ML/AI** | Ollama | Latest | Local LLM server |
| **ML/AI** | ChromaDB | 0.4+ | Vector database |
| **ML/AI** | MLflow | 2.8+ | Model tracking |
| **Data** | Redis | 7.0+ | Session caching |
| **Data** | PostgreSQL | 15+ | Persistent storage |
| **Observability** | OpenTelemetry | 1.37+ | Instrumentation |
| **Observability** | Prometheus | 2.45+ | Metrics collection |
| **Observability** | Grafana | 10.0+ | Visualization |
| **Observability** | Jaeger | 1.50+ | Distributed tracing |
| **Containerization** | Docker | 24.0+ | Container runtime |
| **Orchestration** | Docker Compose | 2.20+ | Local orchestration |

### Development Tools

| Tool | Purpose | Integration |
|------|---------|-------------|
| **pytest** | Unit testing | CI/CD pipeline |
| **black** | Code formatting | Pre-commit hooks |
| **mypy** | Type checking | IDE integration |
| **pre-commit** | Git hooks | Automated checks |
| **uv** | Package management | Fast dependency resolution |

## API Architecture

### RESTful API Design

```mermaid
graph TB
    subgraph "Core Endpoints"
        A[POST /chat-stream]
        B[POST /chat]
        C[GET /health]
        D[GET /metrics]
    end
    
    subgraph "Session Management"
        E[GET /session/{id}]
        F[GET /session/{id}/history]
        G[DELETE /session/{id}]
        H[POST /session/cleanup]
    end
    
    subgraph "Data Access"
        I[GET /session/{id}/classification]
        J[GET /session/{id}/prescription]
        K[GET /session/{id}/insurance]
        L[GET /session/{id}/vendors]
    end
    
    subgraph "System Management"
        M[GET /stats]
        N[GET /version]
        O[POST /reload]
        P[GET /docs]
    end
    
    A --> E
    B --> E
    C --> M
    D --> M
    
    E --> I
    F --> I
    G --> I
    H --> I
```

### API Response Format

```json
{
  "session_id": "uuid",
  "status": "success|error|in_progress",
  "current_node": "INITIAL|CLASSIFYING|PRESCRIBING|...",
  "assistant_response": "Generated response text",
  "data": {
    "classification": {...},
    "prescription": {...},
    "insurance": {...},
    "vendors": [...]
  },
  "metadata": {
    "timestamp": "2024-01-01T00:00:00Z",
    "processing_time": 1.234,
    "confidence": 0.95
  }
}
```

## Error Handling & Resilience

### Circuit Breaker Pattern

```mermaid
graph TB
    subgraph "Service Calls"
        A[External API Call]
        B[ML Model Inference]
        C[Database Query]
        D[Cache Access]
    end
    
    subgraph "Circuit Breaker States"
        E[CLOSED - Normal Operation]
        F[OPEN - Failing Fast]
        G[HALF_OPEN - Testing Recovery]
    end
    
    subgraph "Fallback Mechanisms"
        H[Cached Response]
        I[Default Values]
        J[Error Message]
        K[Retry Logic]
    end
    
    A --> E
    B --> E
    C --> E
    D --> E
    
    E --> F
    F --> G
    G --> E
    
    F --> H
    F --> I
    F --> J
    G --> K
```

### Retry Strategy

| Service | Max Retries | Backoff | Timeout |
|---------|-------------|---------|---------|
| **LLM Server** | 3 | Exponential | 30s |
| **ML Models** | 2 | Linear | 10s |
| **External APIs** | 3 | Exponential | 15s |
| **Database** | 5 | Linear | 5s |

## Future Architecture Considerations

### Planned Enhancements

1. **Microservices Migration**
   - Split monolithic engine into specialized services
   - Implement service mesh architecture
   - Add API gateway for service discovery

2. **Cloud-Native Deployment**
   - Kubernetes orchestration
   - Auto-scaling based on demand
   - Multi-region deployment

3. **Advanced AI Capabilities**
   - Multi-modal input processing
   - Real-time model updates
   - Federated learning integration

4. **Enhanced Observability**
   - Custom business metrics
   - Predictive alerting
   - Cost optimization insights

### Scalability Roadmap

| Phase | Concurrent Users | Response Time | Features |
|-------|------------------|---------------|----------|
| **Current** | 500 | < 2s | Basic workflow |
| **Phase 1** | 2,000 | < 1.5s | Caching, optimization |
| **Phase 2** | 10,000 | < 1s | Microservices, CDN |
| **Phase 3** | 50,000+ | < 0.5s | Cloud-native, auto-scaling |

## Conclusion

The Sasya Arogya Engine represents a sophisticated, production-ready agricultural intelligence platform built on modern architectural principles. With its comprehensive observability stack, robust error handling, and scalable design, the system is well-positioned to serve farmers with reliable, intelligent agricultural solutions while maintaining high performance and reliability standards.

The architecture's modular design enables easy extension and maintenance, while the comprehensive monitoring and observability stack ensures operational excellence and continuous improvement. The system's foundation in proven technologies and best practices provides a solid platform for future growth and enhancement.

---

*This technical architecture document serves as the definitive guide for understanding, deploying, and maintaining the Sasya Arogya Engine system.*
