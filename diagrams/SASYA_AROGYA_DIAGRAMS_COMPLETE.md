# 🌾 Sasya Arogya Engine - Complete Diagram Collection

## 🎨 Sasya Arogya Theme Applied

All diagrams have been regenerated using a custom **Sasya Arogya theme** featuring:
- **Primary Green**: #2E7D32 (Deep Forest Green)
- **Secondary Green**: #4CAF50 (Material Green)
- **Accent Green**: #E8F5E8 (Light Green Background)
- **Text Color**: #1B5E20 (Dark Green)
- **Background**: White with green accents

## 📊 Complete Diagram Collection

### 🏗️ **System Architecture Diagrams**

#### 1. **Application Architecture** (`diagram_01_vertical_sasya.png`)
**Description**: Complete system architecture showing the seven-layer stack from client applications to infrastructure components, featuring clean vertical layout with straight arrows for optimal readability.

**Key Components**:
- Client Layer (Android, Web, API Clients)
- API Gateway Layer (FastAPI Server)
- Core Engine (LangGraph FSM, Intent Analyzer)
- AI/ML Services (CNN Models, LLM Integration)
- External Services (MCP Server, ChromaDB, Ollama)
- Observability Layer (OpenTelemetry, Prometheus, Grafana)
- Infrastructure Layer (Docker, Kubernetes, Load Balancer)

#### 2. **LangGraph Workflow State Machine** (`diagram_02_clean_sasya.png`)
**Description**: Complete finite state machine implementation showing 12 workflow states and 24 transitions, with clear state types and decision flow patterns.

**Key States**:
- START → INITIAL → CLASSIFYING → PRESCRIBING → INSURANCE → VENDOR_QUERY
- SHOW_VENDORS → ORDER_BOOKING → FOLLOWUP → COMPLETED → ERROR → END

#### 3. **AI/ML Pipeline Architecture** (`diagram_03_sasya.png`)
**Description**: Machine learning workflow from input processing through model inference to response generation, showing integration between different AI models.

#### 4. **Microservices Architecture** (`diagram_04_sasya.png`)
**Description**: Service-oriented design showing independent, loosely-coupled services with clear communication patterns and service boundaries.

#### 5. **Data Flow Sequence** (`diagram_05_sasya.png`)
**Description**: Complete request lifecycle from user input through processing to response delivery, showing temporal flow and performance characteristics.

#### 6. **Observability & Monitoring Stack** (`diagram_06_sasya.png`)
**Description**: Comprehensive monitoring infrastructure with OpenTelemetry, Prometheus, Grafana, and Jaeger integration for real-time system insights.

#### 7. **Deployment Architecture** (`diagram_07_sasya.png`)
**Description**: Production deployment strategy with load balancing, container orchestration, and high availability configuration.

#### 8. **Security Architecture** (`diagram_08_sasya.png`)
**Description**: Multi-layered security implementation with authentication, encryption, and access control mechanisms.

#### 9. **Performance Metrics Dashboard** (`diagram_09_sasya.png`)
**Description**: Key performance indicators and monitoring metrics for system health and operational efficiency.

#### 10. **Technology Stack Overview** (`diagram_10_fixed_sasya.png`)
**Description**: Complete technology matrix showing all frameworks, tools, and services used in the system implementation.

### 🏦 **MCP Integration Diagrams**

#### 11. **MCP Integration Architecture** (`mcp_integration_architecture.png`)
**Description**: High-level system architecture showing the complete integration between LangGraph FSM and MCP server for crop insurance services.

**Key Integration Points**:
- LangGraph FSM Workflow Engine
- Intent Analysis System (LLM-Powered)
- MCP Server Layer (Premium Calculator, Certificate Generator)
- External Services (Government APIs, Insurance APIs)

#### 12. **Insurance Premium Calculation Flow** (`insurance_premium_flow.png`)
**Description**: Detailed sequence diagram showing the complete premium calculation process from user input through MCP server processing to final response delivery.

**Process Steps**:
1. User requests premium calculation
2. LangGraph FSM processes intent
3. LLM analyzes sub-intent (premium vs purchase)
4. Insurance Tool calls MCP server
5. MCP server calculates premium with government subsidies
6. Results streamed back to user

#### 13. **Insurance Purchase Flow** (`insurance_purchase_flow.png`)
**Description**: Complete sequence diagram for insurance purchase and certificate generation, demonstrating sophisticated integration between LangGraph workflow management and MCP server PDF generation.

**Process Steps**:
1. User requests insurance purchase
2. Intent analysis determines purchase intent
3. Policy data generation with unique identifiers
4. MCP server generates PDF certificate
5. Policy stored in database
6. Certificate delivered to user

#### 14. **LangGraph-MCP Integration** (`langgraph_mcp_integration.png`)
**Description**: Technical architecture diagram showing the integration patterns between LangGraph FSM and MCP server, demonstrating agentic integration capabilities.

## 🎯 **Professional Report Descriptions**

### System Architecture Diagrams

#### Diagram 01 - Application Architecture
The Application Architecture diagram presents the complete technical architecture of the Sasya Arogya Engine, showcasing a seven-layer stack from client applications to infrastructure components. The visualization demonstrates clear data flow through the API Gateway Layer, Core Engine, AI/ML Services, and External Services, with dedicated Observability and Infrastructure layers providing monitoring and deployment support. Each layer is color-coded using the Sasya Arogya green theme and properly spaced to ensure readability, with straight arrows indicating primary data flow paths and dotted lines showing observability and infrastructure connections. This diagram serves as the foundational reference for understanding the system's component relationships and data movement patterns.

#### Diagram 02 - LangGraph Workflow State Machine
The LangGraph Workflow State Machine diagram illustrates the complete finite state machine implementation that orchestrates user interactions through the agricultural intelligence platform. The visualization shows 12 distinct states including START, INITIAL, CLASSIFYING, PRESCRIBING, INSURANCE, VENDOR_QUERY, SHOW_VENDORS, ORDER_BOOKING, FOLLOWUP, COMPLETED, ERROR, and END states, with 24 labeled transitions between them. The diagram uses the Sasya Arogya green color scheme to distinguish state types (process, service, error, terminal) and employs curved arrows with clear labels to show the decision flow from user input through disease classification, treatment prescription, insurance calculation, and vendor selection. This state machine ensures robust conversation management and prevents infinite loops while providing multiple pathways for user interaction completion.

### MCP Integration Diagrams

#### Diagram 11 - MCP Integration Architecture
The MCP Integration Architecture diagram presents the complete technical integration between the LangGraph finite state machine workflow engine and the Model Context Protocol (MCP) server, showcasing a multi-layered architecture from client applications to external data sources. The visualization demonstrates clear data flow through the FastAPI server, LangGraph FSM engine, intent analysis system, and MCP server tools, with dedicated layers for external services and data processing. Each layer is color-coded using the Sasya Arogya green theme and properly spaced to ensure readability, with straight arrows indicating primary data flow paths and clear separation between client, engine, MCP, and external service layers. This diagram serves as the foundational reference for understanding the complete system integration and service communication patterns.

#### Diagram 12 - Insurance Premium Calculation Flow
The Insurance Premium Calculation Flow diagram illustrates the complete sequence of operations for calculating crop insurance premiums, from user input through MCP server processing to final response delivery. The visualization shows 12 distinct interaction steps including user input processing, LangGraph FSM routing, LLM-powered intent analysis, MCP server communication, premium calculation with government subsidies, and result streaming. The diagram uses the Sasya Arogya green theme with clear participant labels and detailed annotations to show the decision flow from user request through intent disambiguation, context extraction, MCP tool execution, and premium calculation with subsidy application. This sequence diagram ensures comprehensive understanding of the premium calculation process and serves as technical documentation for developers and business stakeholders.

## 📁 **File Structure**

```
diagrams/
├── sasya-arogya-theme.json                    # Custom theme configuration
├── 
├── # System Architecture Diagrams (Sasya Arogya Theme)
├── diagram_01_vertical_sasya.png              # Application Architecture
├── diagram_02_clean_sasya.png                 # LangGraph Workflow FSM
├── diagram_03_sasya.png                       # AI/ML Pipeline Architecture
├── diagram_04_sasya.png                       # Microservices Architecture
├── diagram_05_sasya.png                       # Data Flow Sequence
├── diagram_06_sasya.png                       # Observability & Monitoring
├── diagram_07_sasya.png                       # Deployment Architecture
├── diagram_08_sasya.png                       # Security Architecture
├── diagram_09_sasya.png                       # Performance Metrics
├── diagram_10_fixed_sasya.png                 # Technology Stack Overview
├── 
├── # MCP Integration Diagrams (Sasya Arogya Theme)
├── mcp_integration_architecture.png           # MCP Integration Architecture
├── insurance_premium_flow.png                 # Insurance Premium Flow
├── insurance_purchase_flow.png                # Insurance Purchase Flow
├── langgraph_mcp_integration.png              # LangGraph-MCP Integration
├── 
├── # Documentation
├── MCP_INTEGRATION_WRITEUP.md                 # Comprehensive MCP writeup
├── MCP_DIAGRAMS_SUMMARY.md                    # MCP diagrams summary
└── SASYA_AROGYA_DIAGRAMS_COMPLETE.md          # This complete collection
```

## 🎨 **Theme Specifications**

### Color Palette
- **Primary Green**: #2E7D32 (Deep Forest Green) - Main elements
- **Secondary Green**: #4CAF50 (Material Green) - Accent elements
- **Light Green**: #E8F5E8 (Light Green Background) - Backgrounds
- **Dark Green**: #1B5E20 (Dark Green) - Text and borders
- **Background**: White with green accents

### Design Principles
- **Consistent Branding**: All diagrams use the Sasya Arogya green theme
- **High Contrast**: Dark green text on light backgrounds for readability
- **Professional Appearance**: Clean, modern design suitable for business documents
- **Agricultural Theme**: Green color scheme reflects agricultural focus

## 🎯 **Usage Instructions**

### For Technical Reports
1. **Use Sasya Arogya themed diagrams** for consistent branding
2. **Copy the PNG files** to your report directory
3. **Use the provided descriptions** for figure captions
4. **Reference the technical writeups** for detailed implementation details

### For Presentations
1. **Use the architecture diagrams** for system overview
2. **Include the MCP integration diagrams** for technical discussions
3. **Reference the sequence diagrams** for process explanations
4. **Maintain consistent Sasya Arogya branding** throughout

### For Documentation
1. **Include all themed diagrams** in technical documentation
2. **Use the Mermaid source files** for version control
3. **Update diagrams** as the system evolves
4. **Maintain theme consistency** across all visual materials

## 📊 **Technical Specifications**

- **Format**: PNG (1920x1080 resolution)
- **Theme**: Custom Sasya Arogya green theme
- **Quality**: High-resolution for print and digital use
- **Compatibility**: Works in Word, PowerPoint, PDF, and web documents
- **Branding**: Consistent agricultural green color scheme

## 🎉 **Ready for Professional Use!**

All diagrams are now available in the **Sasya Arogya theme** with:
- ✅ **Consistent Branding** - Agricultural green color scheme
- ✅ **Professional Quality** - High-resolution PNG format
- ✅ **Complete Coverage** - All system and MCP integration diagrams
- ✅ **Report Ready** - Professional descriptions and documentation
- ✅ **Theme Applied** - Custom Sasya Arogya green theme throughout

The complete diagram collection is now ready for use in technical reports, presentations, and system documentation with consistent Sasya Arogya branding! 🌾
