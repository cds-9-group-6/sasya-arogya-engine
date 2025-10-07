# Diagram Descriptions for Technical Reports

## Diagram 01 - System Overview Architecture

The System Overview Architecture diagram presents the complete technical architecture of the Sasya Arogya Engine, showcasing a seven-layer stack from client applications to infrastructure components. The visualization demonstrates clear data flow through the API Gateway Layer, Core Engine, AI/ML Services, and External Services, with dedicated Observability and Infrastructure layers providing monitoring and deployment support. Each layer is color-coded and properly spaced to ensure readability, with straight arrows indicating primary data flow paths and dotted lines showing observability and infrastructure connections. This diagram serves as the foundational reference for understanding the system's component relationships and data movement patterns.

## Diagram 02 - LangGraph Workflow State Machine

The LangGraph Workflow State Machine diagram illustrates the complete finite state machine implementation that orchestrates user interactions through the agricultural intelligence platform. The visualization shows 12 distinct states including START, INITIAL, CLASSIFYING, PRESCRIBING, INSURANCE, VENDOR_QUERY, SHOW_VENDORS, ORDER_BOOKING, FOLLOWUP, COMPLETED, ERROR, and END states, with 24 labeled transitions between them. The diagram uses different colors to distinguish state types (process, service, error, terminal) and employs curved arrows with clear labels to show the decision flow from user input through disease classification, treatment prescription, insurance calculation, and vendor selection. This state machine ensures robust conversation management and prevents infinite loops while providing multiple pathways for user interaction completion.

## Diagram 03 - AI/ML Pipeline Architecture

The AI/ML Pipeline Architecture diagram details the machine learning workflow from input processing through model inference to response generation. The visualization shows the complete pipeline including image preprocessing, CNN disease classification with attention mechanisms, LLaVA vision model processing, Ollama LLM server integration, and RAG-based prescription generation. Each component is connected with clear data flow arrows showing how plant images and text queries are processed through computer vision models, natural language processing systems, and knowledge retrieval mechanisms. The diagram emphasizes the integration between different AI models and the MLflow tracking system for experiment management and model versioning.

## Diagram 04 - Microservices Architecture

The Microservices Architecture diagram presents the service-oriented design of the Sasya Arogya Engine, illustrating how different functional components are organized as independent, loosely-coupled services. The visualization shows service boundaries between the FastAPI server, FSM Agent Service, Intent Analysis Service, Classification Service, and Prescription Service, with clear communication patterns between them. External services including the Insurance MCP Service, Vendor Service, ChromaDB Service, and Ollama LLM Service are depicted as separate microservices with defined interfaces. The diagram demonstrates how this architecture enables scalability, maintainability, and independent deployment of individual service components.

## Diagram 05 - Data Flow Sequence

The Data Flow Sequence diagram provides a comprehensive view of how data moves through the entire system from user input to response delivery. The visualization shows the complete request lifecycle starting from client applications through the API Gateway, Core Engine processing, AI/ML service calls, external service integrations, and response streaming back to the user. The diagram uses sequence notation to clearly show the temporal flow of operations, including parallel processing of different AI models and the integration of observability metrics collection throughout the process. This diagram is essential for understanding system performance characteristics and identifying potential bottlenecks in the data processing pipeline.

## Diagram 06 - Observability & Monitoring Stack

The Observability & Monitoring Stack diagram illustrates the comprehensive monitoring and observability infrastructure that provides real-time insights into system performance and health. The visualization shows the integration of OpenTelemetry Collector for metrics and trace collection, Prometheus for time-series data storage, Grafana for visualization and dashboards, and Jaeger for distributed tracing. The diagram demonstrates how observability data flows from application components through the collection layer to storage and visualization systems, enabling proactive monitoring, performance optimization, and troubleshooting capabilities. This observability stack ensures operational excellence and provides the foundation for data-driven system improvements.

## Diagram 07 - Deployment Architecture

The Deployment Architecture diagram presents the production deployment strategy for the Sasya Arogya Engine, showing how the system is designed for scalability, reliability, and high availability. The visualization illustrates the load balancer layer with NGINX/HAProxy, multiple application instances for horizontal scaling, data layer with Redis clusters and PostgreSQL databases, and external service integrations. The diagram shows container orchestration using Docker and Kubernetes, with proper service mesh configuration and secrets management. This deployment architecture ensures the system can handle production workloads while maintaining performance, security, and operational efficiency across different environments.

## Diagram 08 - Security Architecture

The Security Architecture diagram outlines the multi-layered security implementation that protects the Sasya Arogya Engine and its data. The visualization shows client authentication mechanisms including API keys, JWT tokens, OAuth 2.0, and session tokens, integrated with API security features like rate limiting, input validation, CORS protection, and HTTPS/TLS encryption. The diagram illustrates data protection measures including encryption at rest and in transit, data anonymization, and comprehensive access logging. Infrastructure security components include container security, network isolation, secrets management, and vulnerability scanning, ensuring end-to-end security coverage across all system layers.

## Diagram 09 - Performance Metrics Dashboard

The Performance Metrics Dashboard diagram presents the key performance indicators and monitoring metrics that track system health and operational efficiency. The visualization shows system performance metrics including response time targets (< 2s), throughput capabilities (> 100 req/s), concurrent user support (> 1000), and uptime requirements (> 99.9%). The diagram illustrates ML performance metrics covering classification accuracy (> 85%), model confidence scores (> 0.8), and inference timing (< 1s), along with business metrics tracking session completion rates (> 90%) and user satisfaction (> 80%). Infrastructure metrics monitor memory usage (< 4GB), CPU utilization (< 80%), disk usage (< 20GB), and network latency (< 100ms) to ensure optimal resource utilization.

## Diagram 10 - Technology Stack Overview

The Technology Stack Overview diagram provides a comprehensive view of all technologies, frameworks, and tools used in the Sasya Arogya Engine implementation. The visualization organizes technologies into logical categories including frontend technologies (Android, Web, API Clients), backend technologies (Python 3.11+, FastAPI, LangGraph, LangChain), AI/ML technologies (TensorFlow 2.15+, Ollama, ChromaDB, MLflow), data technologies (Redis, PostgreSQL, MinIO/S3), observability technologies (OpenTelemetry, Prometheus, Grafana, Jaeger), and infrastructure technologies (Docker, Kubernetes, NGINX, Helm). The diagram shows how these technologies integrate to form a cohesive, modern technology stack that supports the platform's requirements for scalability, maintainability, and performance.

---

## Usage Instructions

These descriptions are designed to be:

- **Concise**: 4-5 lines each for easy integration into reports
- **Technical**: Appropriate for technical documentation
- **Professional**: Suitable for business and academic reports
- **Comprehensive**: Cover all key aspects of each diagram
- **Consistent**: Follow the same format and style

### How to Use in Reports:

1. **Copy the relevant description** for each diagram you include
2. **Place before or after** the diagram in your report
3. **Reference the diagram** using the description (e.g., "As shown in Diagram 01...")
4. **Customize as needed** for your specific report context
5. **Maintain consistency** in formatting and style

### Example Integration:

```
## 3.1 System Architecture

As shown in Diagram 01, the System Overview Architecture presents the complete technical architecture of the Sasya Arogya Engine, showcasing a seven-layer stack from client applications to infrastructure components. The visualization demonstrates clear data flow through the API Gateway Layer, Core Engine, AI/ML Services, and External Services, with dedicated Observability and Infrastructure layers providing monitoring and deployment support. Each layer is color-coded and properly spaced to ensure readability, with straight arrows indicating primary data flow paths and dotted lines showing observability and infrastructure connections. This diagram serves as the foundational reference for understanding the system's component relationships and data movement patterns.

[Insert Diagram 01 here]
```
