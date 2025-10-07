# 🏗️ Sasya Arogya Engine - Architecture Diagrams

This document contains comprehensive visual diagrams of the Sasya Arogya Engine architecture, suitable for technical presentations, project reports, and documentation.

## System Overview Architecture

```mermaid
graph TB
    subgraph "Client Applications"
        A[📱 Android Mobile App]
        B[💻 Web Dashboard]
        C[🔌 API Clients]
        D[🤖 Third-party Integrations]
    end
    
    subgraph "API Gateway Layer"
        E[🌐 FastAPI Server :8080]
        F[🔒 CORS & Security]
        G[⚡ Rate Limiting]
        H[🔑 Authentication]
    end
    
    subgraph "Core Engine (Docker Container)"
        I[🔄 LangGraph FSM Workflow]
        J[🧠 Intent Analysis Engine]
        K[💾 Session Management]
        L[📊 State Persistence]
    end
    
    subgraph "AI/ML Services"
        M[🔍 CNN Disease Classifier]
        N[👁️ LLaVA Vision Model]
        O[🤖 Ollama LLM Server]
        P[📚 RAG Prescription System]
    end
    
    subgraph "External Services"
        Q[🛡️ Insurance MCP Server]
        R[🏪 Vendor Database]
        S[🗃️ ChromaDB Vector Store]
        T[📈 MLflow Tracking]
    end
    
    subgraph "Observability Stack"
        U[📊 OpenTelemetry Collector]
        V[📈 Prometheus Metrics]
        W[📊 Grafana Dashboards]
        X[🔍 Jaeger Tracing]
    end
    
    subgraph "Infrastructure"
        Y[🐳 Docker Containers]
        Z[⚡ Redis Cache]
        AA[💾 File Storage]
        BB[⚙️ Configuration Management]
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
    
    classDef clientLayer fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef apiLayer fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef coreLayer fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef mlLayer fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef externalLayer fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    classDef observabilityLayer fill:#f1f8e9,stroke:#33691e,stroke-width:2px
    classDef infrastructureLayer fill:#fff8e1,stroke:#f57f17,stroke-width:2px
    
    class A,B,C,D clientLayer
    class E,F,G,H apiLayer
    class I,J,K,L coreLayer
    class M,N,O,P mlLayer
    class Q,R,S,T externalLayer
    class U,V,W,X observabilityLayer
    class Y,Z,AA,BB infrastructureLayer
```

## LangGraph Workflow State Machine

```mermaid
stateDiagram-v2
    [*] --> INITIAL: 🚀 New Session
    
    INITIAL --> CLASSIFYING: 📸 Image + Context Available
    INITIAL --> FOLLOWUP: ❓ Missing Information
    INITIAL --> ERROR: ❌ Invalid Input
    
    CLASSIFYING --> PRESCRIBING: ✅ Disease Identified
    CLASSIFYING --> FOLLOWUP: 🔍 Need More Info
    CLASSIFYING --> ERROR: 💥 Classification Failed
    
    PRESCRIBING --> INSURANCE: 💊 Treatment Generated
    PRESCRIBING --> VENDOR_QUERY: 🏪 User Wants Vendors
    PRESCRIBING --> COMPLETED: ✅ No Further Action
    
    INSURANCE --> VENDOR_QUERY: 🛡️ Insurance Calculated
    INSURANCE --> COMPLETED: 🛡️ Insurance Only
    
    VENDOR_QUERY --> SHOW_VENDORS: 👍 User Confirms
    VENDOR_QUERY --> COMPLETED: ❌ No Vendors Needed
    
    SHOW_VENDORS --> ORDER_BOOKING: 🛒 Vendor Selected
    SHOW_VENDORS --> COMPLETED: ❌ No Selection
    
    ORDER_BOOKING --> FOLLOWUP: 📝 Order Placed
    ORDER_BOOKING --> COMPLETED: ✅ Order Complete
    
    FOLLOWUP --> INITIAL: 🔄 New Request
    FOLLOWUP --> CLASSIFYING: 🔍 Reclassify
    FOLLOWUP --> PRESCRIBING: 💊 Regenerate
    FOLLOWUP --> COMPLETED: 🏁 Session End
    
    ERROR --> [*]: 💀 Session Terminated
    COMPLETED --> [*]: ✅ Session Complete
    
    note right of INITIAL: Entry point with context extraction
    note right of CLASSIFYING: CNN disease classification
    note right of PRESCRIBING: RAG-based recommendations
    note right of INSURANCE: Premium calculation & comparison
    note right of VENDOR_QUERY: Ask user about vendor preferences
    note right of SHOW_VENDORS: Display local vendors & pricing
    note right of ORDER_BOOKING: Process order with selected vendor
    note right of FOLLOWUP: Handle additional questions & navigation
    note right of COMPLETED: Terminal state with contextual follow-ups
    note right of ERROR: Error handling and recovery
```

## AI/ML Pipeline Architecture

```mermaid
graph TB
    subgraph "Input Processing Layer"
        A[📸 Image Upload]
        B[💬 Text Query]
        C[🔍 Context Extraction]
    end
    
    subgraph "Computer Vision Pipeline"
        D[🖼️ Image Preprocessing]
        E[🧠 CNN Disease Classifier]
        F[👁️ Attention Visualization]
        G[📊 Confidence Scoring]
    end
    
    subgraph "Natural Language Processing"
        H[🎯 Intent Analysis]
        I[🔍 Context Extraction]
        J[🏷️ Entity Recognition]
        K[😊 Sentiment Analysis]
    end
    
    subgraph "Large Language Models"
        L[🤖 Ollama LLM Server]
        M[💭 Response Generation]
        N[🤔 Decision Making]
        O[💬 Conversation Management]
    end
    
    subgraph "Knowledge Retrieval"
        P[📚 RAG System]
        Q[🔍 Vector Search]
        R[💊 Treatment Database]
        S[📋 Prescription Generation]
    end
    
    subgraph "Model Management"
        T[📈 MLflow Tracking]
        U[🏷️ Model Versioning]
        V[📊 Performance Monitoring]
        W[🧪 Experiment Tracking]
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
    
    classDef inputLayer fill:#e3f2fd,stroke:#0277bd,stroke-width:2px
    classDef visionLayer fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef nlpLayer fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    classDef llmLayer fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef knowledgeLayer fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    classDef managementLayer fill:#f1f8e9,stroke:#689f38,stroke-width:2px
    
    class A,B,C inputLayer
    class D,E,F,G visionLayer
    class H,I,J,K nlpLayer
    class L,M,N,O llmLayer
    class P,Q,R,S knowledgeLayer
    class T,U,V,W managementLayer
```

## Microservices Architecture

```mermaid
graph TB
    subgraph "API Gateway Layer"
        A[🌐 FastAPI Server :8080]
        B[❤️ Health Endpoints]
        C[📊 Metrics Endpoints]
        D[💾 Session Management]
    end
    
    subgraph "Core Services"
        E[🔄 FSM Agent Service]
        F[🧠 Intent Analysis Service]
        G[🔍 Classification Service]
        H[💊 Prescription Service]
    end
    
    subgraph "External Services"
        I[🛡️ Insurance MCP Service]
        J[🏪 Vendor Service]
        K[🗃️ ChromaDB Service]
        L[🤖 Ollama LLM Service]
    end
    
    subgraph "Data Layer"
        M[💾 Session Store]
        N[🧠 Model Storage]
        O[🔍 Vector Database]
        P[⚙️ Configuration Store]
    end
    
    subgraph "Observability Services"
        Q[📊 OpenTelemetry Collector]
        R[📈 Prometheus Server]
        S[📊 Grafana Dashboard]
        T[🔍 Jaeger Tracing]
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
    
    classDef apiLayer fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef coreLayer fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef externalLayer fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    classDef dataLayer fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef observabilityLayer fill:#f1f8e9,stroke:#33691e,stroke-width:2px
    
    class A,B,C,D apiLayer
    class E,F,G,H coreLayer
    class I,J,K,L externalLayer
    class M,N,O,P dataLayer
    class Q,R,S,T observabilityLayer
```

## Data Flow Sequence

```mermaid
sequenceDiagram
    participant U as 👤 User
    participant A as 🌐 API Gateway
    participant F as 🔄 FSM Agent
    participant I as 🧠 Intent Analyzer
    participant C as 🔍 CNN Classifier
    participant L as 🤖 LLM Server
    participant R as 📚 RAG System
    participant V as 🏪 Vendor Service
    participant O as 📊 Observability
    
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

## Observability & Monitoring Stack

```mermaid
graph TB
    subgraph "Application Layer"
        A[🌐 FastAPI Server]
        B[🔄 FSM Workflow]
        C[🧠 ML Models]
        D[🔌 External Services]
    end
    
    subgraph "Instrumentation Layer"
        E[📊 OpenTelemetry SDK]
        F[📈 Custom Metrics]
        G[🔍 Distributed Tracing]
        H[📝 Structured Logging]
    end
    
    subgraph "Collection & Processing"
        I[📊 OTel Collector]
        J[📈 Prometheus Scraper]
        K[📝 Log Aggregator]
        L[🔍 Trace Processor]
    end
    
    subgraph "Storage & Analysis"
        M[📈 Prometheus TSDB]
        N[🔍 Jaeger Backend]
        O[📊 Grafana Dashboards]
        P[🚨 Alert Manager]
    end
    
    subgraph "Visualization Layer"
        Q[📊 System Health Dashboard]
        R[🧠 ML Performance Dashboard]
        S[📈 Business Metrics Dashboard]
        T[❌ Error Analysis Dashboard]
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
    
    classDef appLayer fill:#e3f2fd,stroke:#0277bd,stroke-width:2px
    classDef instrumentationLayer fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef collectionLayer fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    classDef storageLayer fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef visualizationLayer fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    
    class A,B,C,D appLayer
    class E,F,G,H instrumentationLayer
    class I,J,K,L collectionLayer
    class M,N,O,P storageLayer
    class Q,R,S,T visualizationLayer
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Load Balancer Layer"
        A[⚖️ NGINX/HAProxy]
        B[🔒 SSL Termination]
        C[⚡ Rate Limiting]
        D[❤️ Health Checks]
    end
    
    subgraph "Application Layer"
        E[🔄 Engine Instance 1]
        F[🔄 Engine Instance 2]
        G[🔄 Engine Instance N]
    end
    
    subgraph "Data Layer"
        H[⚡ Redis Cluster]
        I[🗄️ PostgreSQL Cluster]
        J[💾 MinIO/S3 Storage]
    end
    
    subgraph "External Services"
        K[🤖 Ollama LLM Cluster]
        L[📈 MLflow Server]
        M[📊 Monitoring Stack]
    end
    
    subgraph "Infrastructure"
        N[☸️ Kubernetes/Docker Swarm]
        O[🕸️ Service Mesh]
        P[🔐 Secrets Management]
        Q[💾 Backup & Recovery]
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
    
    classDef lbLayer fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef appLayer fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef dataLayer fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef externalLayer fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    classDef infraLayer fill:#f1f8e9,stroke:#33691e,stroke-width:2px
    
    class A,B,C,D lbLayer
    class E,F,G appLayer
    class H,I,J dataLayer
    class K,L,M externalLayer
    class N,O,P,Q infraLayer
```

## Security Architecture

```mermaid
graph TB
    subgraph "Client Authentication"
        A[🔑 API Key]
        B[🎫 JWT Token]
        C[🔐 OAuth 2.0]
        D[💳 Session Token]
    end
    
    subgraph "API Security"
        E[⚡ Rate Limiting]
        F[✅ Input Validation]
        G[🌐 CORS Protection]
        H[🔒 HTTPS/TLS]
    end
    
    subgraph "Data Protection"
        I[🔐 Encryption at Rest]
        J[🔒 Encryption in Transit]
        K[👤 Data Anonymization]
        L[📝 Access Logging]
    end
    
    subgraph "Infrastructure Security"
        M[🐳 Container Security]
        N[🔒 Network Isolation]
        O[🔐 Secrets Management]
        P[🔍 Vulnerability Scanning]
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
    
    classDef authLayer fill:#e3f2fd,stroke:#0277bd,stroke-width:2px
    classDef apiSecurityLayer fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef dataProtectionLayer fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    classDef infraSecurityLayer fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    
    class A,B,C,D authLayer
    class E,F,G,H apiSecurityLayer
    class I,J,K,L dataProtectionLayer
    class M,N,O,P infraSecurityLayer
```

## Performance Metrics Dashboard

```mermaid
graph TB
    subgraph "System Performance"
        A[📊 Response Time < 2s]
        B[⚡ Throughput > 100 req/s]
        C[👥 Concurrent Users > 1000]
        D[📈 Uptime > 99.9%]
    end
    
    subgraph "ML Performance"
        E[🎯 Classification Accuracy > 85%]
        F[📊 Model Confidence > 0.8]
        G[⚡ Inference Time < 1s]
        H[🔄 Model Update Frequency]
    end
    
    subgraph "Business Metrics"
        I[✅ Session Completion > 90%]
        J[😊 User Satisfaction > 80%]
        K[💊 Prescription Success Rate]
        L[🏪 Vendor Conversion Rate]
    end
    
    subgraph "Infrastructure Metrics"
        M[💾 Memory Usage < 4GB]
        N[🖥️ CPU Utilization < 80%]
        O[💿 Disk Usage < 20GB]
        P[🌐 Network Latency < 100ms]
    end
    
    A --> E
    B --> F
    C --> G
    D --> H
    
    E --> I
    F --> J
    G --> K
    H --> L
    
    I --> M
    J --> N
    K --> O
    L --> P
    
    classDef systemPerf fill:#e3f2fd,stroke:#0277bd,stroke-width:2px
    classDef mlPerf fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef businessMetrics fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    classDef infraMetrics fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    
    class A,B,C,D systemPerf
    class E,F,G,H mlPerf
    class I,J,K,L businessMetrics
    class M,N,O,P infraMetrics
```

## Technology Stack Overview

```mermaid
graph TB
    subgraph "Frontend Technologies"
        A[📱 Android (Kotlin/Java)]
        B[💻 Web (React/Vue.js)]
        C[🔌 REST API Clients]
    end
    
    subgraph "Backend Technologies"
        D[🐍 Python 3.11+]
        E[⚡ FastAPI Framework]
        F[🔄 LangGraph Workflow]
        G[🧠 LangChain Tools]
    end
    
    subgraph "AI/ML Technologies"
        H[🧠 TensorFlow 2.15+]
        I[🤖 Ollama LLM Server]
        J[🔍 ChromaDB Vector DB]
        K[📈 MLflow Tracking]
    end
    
    subgraph "Data Technologies"
        L[⚡ Redis Cache]
        M[🗄️ PostgreSQL Database]
        N[💾 MinIO/S3 Storage]
        O[📊 Time Series DB]
    end
    
    subgraph "Observability Technologies"
        P[📊 OpenTelemetry]
        Q[📈 Prometheus]
        R[📊 Grafana]
        S[🔍 Jaeger Tracing]
    end
    
    subgraph "Infrastructure Technologies"
        T[🐳 Docker Containers]
        U[☸️ Kubernetes]
        V[🌐 NGINX Load Balancer]
        W[🔧 Helm Charts]
    end
    
    A --> D
    B --> D
    C --> D
    
    D --> E
    E --> F
    F --> G
    
    G --> H
    G --> I
    G --> J
    G --> K
    
    E --> L
    E --> M
    E --> N
    E --> O
    
    D --> P
    E --> P
    F --> P
    G --> P
    
    P --> Q
    P --> R
    P --> S
    
    D --> T
    E --> T
    F --> T
    G --> T
    
    T --> U
    U --> V
    V --> W
    
    classDef frontendTech fill:#e3f2fd,stroke:#0277bd,stroke-width:2px
    classDef backendTech fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef mlTech fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef dataTech fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    classDef observabilityTech fill:#f1f8e9,stroke:#33691e,stroke-width:2px
    classDef infraTech fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    
    class A,B,C frontendTech
    class D,E,F,G backendTech
    class H,I,J,K mlTech
    class L,M,N,O dataTech
    class P,Q,R,S observabilityTech
    class T,U,V,W infraTech
```

---

## Usage Instructions

These diagrams can be used in various ways:

1. **Technical Presentations**: Use individual diagrams to explain specific aspects of the architecture
2. **Project Reports**: Include relevant diagrams to illustrate system design and components
3. **Documentation**: Reference diagrams in technical documentation and README files
4. **Code Reviews**: Use diagrams to understand system interactions and data flow
5. **Onboarding**: Help new team members understand the system architecture

## Diagram Formats

- **Mermaid**: Native support in GitHub, GitLab, and many documentation platforms
- **PNG/SVG**: Export from Mermaid Live Editor or VS Code Mermaid extension
- **PDF**: Convert for formal documentation and presentations

## Customization

To customize these diagrams:

1. Copy the Mermaid code to [Mermaid Live Editor](https://mermaid.live/)
2. Modify colors, shapes, and connections as needed
3. Export in your preferred format
4. Update the source files with your changes

---

*These architecture diagrams provide a comprehensive visual representation of the Sasya Arogya Engine system, suitable for technical documentation, presentations, and project reports.*
