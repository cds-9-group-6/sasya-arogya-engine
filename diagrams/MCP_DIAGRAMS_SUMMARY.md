# 🏦 MCP Integration Diagrams - Complete Collection

## 📊 Generated Diagrams

This directory contains comprehensive visualizations of the LangGraph-MCP integration for crop insurance services in the Sasya Arogya Engine.

### 1. **MCP Integration Architecture** (`mcp_integration_architecture.png`)
**Purpose**: High-level system architecture showing the complete integration between LangGraph FSM and MCP server.

**Key Components**:
- Client Layer (Android, Web, API Clients)
- Sasya Arogya Engine (FastAPI, LangGraph, Intent Analyzer)
- MCP Server Layer (Premium Calculator, Certificate Generator, Company Data, Recommendations)
- External Services (Government APIs, Insurance APIs, Weather Data, Database Services)

**Use Case**: System overview for technical documentation and architecture presentations.

### 2. **Insurance Premium Calculation Flow** (`insurance_premium_flow.png`)
**Purpose**: Detailed sequence diagram showing the complete premium calculation process.

**Flow Steps**:
1. User requests premium calculation
2. LangGraph FSM processes intent
3. LLM analyzes sub-intent (premium vs purchase)
4. Insurance Tool calls MCP server
5. MCP server calculates premium with government subsidies
6. Results streamed back to user

**Use Case**: Process documentation for developers and business stakeholders.

### 3. **Insurance Purchase Flow** (`insurance_purchase_flow.png`)
**Purpose**: Complete sequence diagram for insurance purchase and certificate generation.

**Flow Steps**:
1. User requests insurance purchase
2. Intent analysis determines purchase intent
3. Policy data generation with unique identifiers
4. MCP server generates PDF certificate
5. Policy stored in database
6. Certificate delivered to user

**Use Case**: End-to-end process documentation for insurance operations.

### 4. **LangGraph-MCP Integration** (`langgraph_mcp_integration.png`)
**Purpose**: Technical architecture diagram showing the integration patterns between LangGraph FSM and MCP server.

**Key Integration Points**:
- LangGraph FSM Workflow Engine
- Intent Analysis System
- MCP Integration Layer
- MCP Server Tools
- External Data Sources

**Use Case**: Technical architecture documentation for system integration.

## 🎯 Diagram Descriptions for Reports

### MCP Integration Architecture
The MCP Integration Architecture diagram presents the complete technical integration between the LangGraph finite state machine workflow engine and the Model Context Protocol (MCP) server, showcasing a multi-layered architecture from client applications to external data sources. The visualization demonstrates clear data flow through the FastAPI server, LangGraph FSM engine, intent analysis system, and MCP server tools, with dedicated layers for external services and data processing. Each layer is color-coded and properly spaced to ensure readability, with straight arrows indicating primary data flow paths and clear separation between client, engine, MCP, and external service layers. This diagram serves as the foundational reference for understanding the complete system integration and service communication patterns.

### Insurance Premium Calculation Flow
The Insurance Premium Calculation Flow diagram illustrates the complete sequence of operations for calculating crop insurance premiums, from user input through MCP server processing to final response delivery. The visualization shows 12 distinct interaction steps including user input processing, LangGraph FSM routing, LLM-powered intent analysis, MCP server communication, premium calculation with government subsidies, and result streaming. The diagram uses clear participant labels and detailed annotations to show the decision flow from user request through intent disambiguation, context extraction, MCP tool execution, and premium calculation with subsidy application. This sequence diagram ensures comprehensive understanding of the premium calculation process and serves as technical documentation for developers and business stakeholders.

### Insurance Purchase Flow
The Insurance Purchase Flow diagram details the complete sequence of operations for insurance purchase and certificate generation, demonstrating the sophisticated integration between LangGraph workflow management and MCP server PDF generation capabilities. The visualization shows 12 distinct interaction steps including purchase intent recognition, policy data generation with unique identifiers, MCP server certificate generation, database storage, and PDF delivery. The diagram employs clear participant separation and detailed process annotations to show the complete flow from user purchase request through policy creation, certificate generation, and final delivery. This sequence diagram provides comprehensive documentation for the insurance purchase process and serves as a reference for understanding the complete certificate generation workflow.

### LangGraph-MCP Integration
The LangGraph-MCP Integration diagram presents the technical architecture patterns for integrating LangGraph's finite state machine workflow engine with the Model Context Protocol server, showcasing the sophisticated agentic integration that enables intelligent crop insurance operations. The visualization shows five distinct architectural layers including the LangGraph FSM workflow, intent analysis system, MCP integration layer, MCP server tools, and external data sources, with clear data flow connections between each layer. The diagram uses color-coded layers and straight arrows to demonstrate the integration patterns, service communication flows, and data processing pathways that enable autonomous decision-making and context-aware processing. This architecture diagram serves as the technical foundation for understanding how LangGraph and MCP work together to deliver intelligent agricultural insurance services.

## 📁 File Structure

```
diagrams/
├── mcp_integration_architecture.mmd          # Mermaid source
├── mcp_integration_architecture.png          # Generated PNG
├── insurance_premium_flow.mmd                # Mermaid source
├── insurance_premium_flow.png                # Generated PNG
├── insurance_purchase_flow.mmd               # Mermaid source
├── insurance_purchase_flow.png               # Generated PNG
├── langgraph_mcp_integration.mmd             # Mermaid source
├── langgraph_mcp_integration.png             # Generated PNG
├── MCP_INTEGRATION_WRITEUP.md                # Comprehensive technical writeup
└── MCP_DIAGRAMS_SUMMARY.md                   # This summary file
```

## 🎯 Usage Instructions

### For Technical Reports
1. **Copy the PNG files** to your report directory
2. **Use the diagram descriptions** provided above for figure captions
3. **Reference the technical writeup** for detailed implementation details
4. **Include the architecture diagram** for system overview sections

### For Presentations
1. **Use the sequence diagrams** for process flow explanations
2. **Include the architecture diagram** for system overview
3. **Reference the integration diagram** for technical architecture discussions
4. **Use the technical writeup** for detailed explanations

### For Documentation
1. **Include all diagrams** in technical documentation
2. **Use the Mermaid source files** for version control
3. **Reference the writeup** for comprehensive technical details
4. **Update diagrams** as the system evolves

## 🔧 Technical Specifications

- **Format**: PNG (1920x1080 resolution)
- **Theme**: Neutral with white background
- **Quality**: High-resolution for print and digital use
- **Compatibility**: Works in Word, PowerPoint, PDF, and web documents
- **Source**: Mermaid diagrams with professional styling

## 📚 Related Documentation

- **[MCP Integration Writeup](./MCP_INTEGRATION_WRITEUP.md)** - Comprehensive technical documentation
- **[Technical Architecture](../TECHNICAL_ARCHITECTURE.md)** - Complete system architecture
- **[Architecture Diagrams](../ARCHITECTURE_DIAGRAMS.md)** - Visual system diagrams
- **[Insurance Architecture](../INSURANCE_ARCHITECTURE.md)** - Insurance system documentation

---

**🎉 Ready for Professional Use!**

These diagrams provide comprehensive visual documentation of the LangGraph-MCP integration, suitable for technical reports, presentations, and system documentation. All diagrams are high-resolution and professionally styled for maximum clarity and impact.
