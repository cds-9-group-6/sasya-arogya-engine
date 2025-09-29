# 🏗️ Sasya Arogya Engine - Detailed Architecture

## System Overview

The Sasya Arogya Engine is built using a modular, event-driven architecture that supports multiple agricultural services through an intelligent workflow system.

## Core Components

### 1. LangGraph FSM Workflow

```
                                    ┌─────────────────────────────────────┐
                                    │           User Input                │
                                    │                                     │
                                    │ • Natural language query            │
                                    │ • Optional plant image              │
                                    │ • Session context                   │
                                    └──────────────┬──────────────────────┘
                                                   │
                                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                            Intent Analysis Layer                                    │
│                                                                                     │
│  ┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐    │
│  │                     │    │                     │    │                     │    │
│  │  Agriculture        │    │   Rule Engine       │    │   Context           │    │
│  │  Intent Analyzer    │◄──►│                     │◄──►│   Extractor         │    │
│  │                     │    │ • Insurance rules   │    │                     │    │
│  │ • Classification    │    │ • Vendor rules      │    │ • Plant type        │    │
│  │ • Treatment         │    │ • Treatment rules   │    │ • Location          │    │
│  │ • Insurance         │    │ • Priority scoring  │    │ • Disease context   │    │
│  │ • Vendor            │    │                     │    │                     │    │
│  └─────────────────────┘    └─────────────────────┘    └─────────────────────┘    │
└─────────────────────────────────────┬───────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              Workflow Router                                        │
│                                                                                     │
│     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐    │
│     │             │     │             │     │             │     │             │    │
│     │ Initial     │────►│ Followup    │◄────│ Completed   │     │ Error       │    │
│     │ Node        │     │ Node        │     │ Node        │     │ Node        │    │
│     │             │     │             │     │             │     │             │    │
│     └─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘    │
│            │                    │                                                   │
│            ▼                    ▼                                                   │
│     ┌──────────────────────────────────────────────────────────────────────────┐   │
│     │                    Service Execution Layer                              │   │
│     │                                                                          │   │
│     │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐      │   │
│     │  │             │ │             │ │             │ │             │      │   │
│     │  │Classifying  │ │Prescribing  │ │Insurance    │ │Vendors      │      │   │
│     │  │Node         │ │Node         │ │Node         │ │Node         │      │   │
│     │  │             │ │             │ │             │ │             │      │   │
│     │  │• CNN Model  │ │• RAG Query  │ │• MCP Call   │ │• Supplier   │      │   │
│     │  │• Attention  │ │• Treatment  │ │• Premium    │ │• Search     │      │   │
│     │  │• Disease ID │ │• Dosage     │ │• Companies  │ │• Pricing    │      │   │
│     │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘      │   │
│     └──────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           External Services Layer                                   │
│                                                                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐  │
│  │                 │  │                 │  │                 │  │              │  │
│  │ Prescription    │  │ Sasya Arogya    │  │ Ollama LLM      │  │ MLflow       │  │
│  │ RAG Server      │  │ MCP Server      │  │ Server          │  │ Tracking     │  │
│  │                 │  │                 │  │                 │  │              │  │
│  │ • Treatment DB  │  │ • Insurance API │  │ • Intent LLM    │  │ • Experiments│  │
│  │ • Vector Search │  │ • Premium Calc  │  │ • Response Gen  │  │ • Metrics    │  │
│  │ • RAG Pipeline  │  │ • PDF Gen       │  │ • Classification│  │ • Models     │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 2. State Management Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              Session State Management                               │
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                        WorkflowState                                        │   │
│  │                                                                             │   │
│  │  Core Fields:                    Service-Specific Fields:                  │   │
│  │  ├─ session_id                   ├─ classification_results                 │   │
│  │  ├─ user_message                 ├─ disease_name                          │   │
│  │  ├─ assistant_response           ├─ prescription_data                     │   │
│  │  ├─ current_node                 ├─ insurance_premium_details             │   │
│  │  ├─ previous_node                ├─ insurance_recommendations             │   │
│  │  ├─ next_action                  ├─ vendor_options                        │   │
│  │  ├─ messages[]                   ├─ farmer_name                           │   │
│  │  ├─ requires_user_input          ├─ area_hectare                          │   │
│  │  └─ is_complete                  └─ plant_type                            │   │
│  │                                                                             │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                          │                                          │
│                                          ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                     Session Persistence                                     │   │
│  │                                                                             │   │
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  ┌──────────────┐ │   │
│  │  │               │  │               │  │               │  │              │ │   │
│  │  │ In-Memory     │  │ Database      │  │ Redis Cache   │  │ File System  │ │   │
│  │  │ Store         │  │ Persistence   │  │ (Optional)    │  │ (Dev/Test)   │ │   │
│  │  │               │  │               │  │               │  │              │ │   │
│  │  │ • Fast Access │  │ • Long-term   │  │ • Distributed │  │ • Simple     │ │   │
│  │  │ • Session Data│  │ • Analytics   │  │ • Scalable    │  │ • Debug      │ │   │
│  │  └───────────────┘  └───────────────┘  └───────────────┘  └──────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 3. Insurance Service Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           Insurance Service Flow                                    │
│                                                                                     │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐                │
│  │                 │    │                 │    │                 │                │
│  │ User Request    │───►│ Insurance Node  │───►│ Context         │                │
│  │                 │    │                 │    │ Extraction      │                │
│  │ "I need crop    │    │ • Analyze input │    │                 │                │
│  │  insurance for  │    │ • Extract context│    │ • Crop type     │                │
│  │  my wheat farm" │    │ • Validate data │    │ • Farm area     │                │
│  │                 │    │                 │    │ • Location      │                │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘                │
│                                  │                        │                        │
│                                  ▼                        ▼                        │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                          Missing Info Handler                              │   │
│  │                                                                             │   │
│  │   ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐      │   │
│  │   │                 │     │                 │     │                 │      │   │
│  │   │ Check Required  │────►│ Extract from    │────►│ Smart Defaults  │      │   │
│  │   │ Fields          │     │ User Message    │     │                 │      │   │
│  │   │                 │     │                 │     │                 │      │   │
│  │   │ • State         │     │ • Crop patterns │     │ • Farmer name   │      │   │
│  │   │ • Area          │     │ • Area patterns │     │ • Default area  │      │   │
│  │   │ • Crop type     │     │ • State patterns│     │ • Fallback crop │      │   │
│  │   └─────────────────┘     └─────────────────┘     └─────────────────┘      │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                  │                                                  │
│                                  ▼                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                         Insurance Tool                                      │   │
│  │                                                                             │   │
│  │   ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐      │   │
│  │   │                 │     │                 │     │                 │      │   │
│  │   │ Premium         │     │ Company         │     │ Recommendations │      │   │
│  │   │ Calculation     │     │ Comparison      │     │                 │      │   │
│  │   │                 │     │                 │     │                 │      │   │
│  │   │ • Base premium  │     │ • Rate analysis │     │ • Policy match  │      │   │
│  │   │ • Risk factors  │     │ • Coverage opts │     │ • Best options  │      │   │
│  │   │ • Subsidies     │     │ • Terms compare │     │ • Custom advice │      │   │
│  │   └─────────────────┘     └─────────────────┘     └─────────────────┘      │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                  │                                                  │
│                                  ▼                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                        MCP Server Interface                                 │   │
│  │                                                                             │   │
│  │  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │   │
│  │  │                 │    │                 │    │                 │         │   │
│  │  │ HTTP Client     │───►│ MCP Server      │───►│ Response        │         │   │
│  │  │                 │    │                 │    │ Processing      │         │   │
│  │  │ • POST requests │    │ • Premium calc  │    │                 │         │   │
│  │  │ • Error handling│    │ • Company data  │    │ • Format results│         │   │
│  │  │ • Timeout mgmt  │    │ • PDF generation│    │ • Extract data  │         │   │
│  │  └─────────────────┘    └─────────────────┘    └─────────────────┘         │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 4. Intent Analysis System

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        Agriculture Intent Analyzer                                  │
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                              Input Layer                                    │   │
│  │                                                                             │   │
│  │    User Message: "I want to buy crop insurance for my 5 hectare farm"      │   │
│  │                                    │                                        │   │
│  │                                    ▼                                        │   │
│  │    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐       │   │
│  │    │                 │    │                 │    │                 │       │   │
│  │    │ Text            │    │ Context         │    │ Session         │       │   │
│  │    │ Preprocessing   │    │ Extraction      │    │ History         │       │   │
│  │    │                 │    │                 │    │                 │       │   │
│  │    │ • Lowercase     │    │ • Plant type    │    │ • Previous      │       │   │
│  │    │ • Tokenization  │    │ • Location      │    │   intents       │       │   │
│  │    │ • Normalization │    │ • Disease info  │    │ • Context       │       │   │
│  │    └─────────────────┘    └─────────────────┘    └─────────────────┘       │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                              │
│                                      ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                           Rule Engine                                       │   │
│  │                                                                             │   │
│  │    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐       │   │
│  │    │                 │    │                 │    │                 │       │   │
│  │    │ Insurance Rules │    │ Vendor Rules    │    │ Treatment Rules │       │   │
│  │    │                 │    │                 │    │                 │       │   │
│  │    │ Keywords:       │    │ Keywords:       │    │ Keywords:       │       │   │
│  │    │ • insurance     │    │ • buy           │    │ • treatment     │       │   │
│  │    │ • premium       │    │ • purchase      │    │ • prescription  │       │   │
│  │    │ • coverage      │    │ • vendor        │    │ • dosage        │       │   │
│  │    │ • policy        │    │ • shop          │    │ • medicine      │       │   │
│  │    │                 │    │                 │    │                 │       │   │
│  │    │ Exclusions:     │    │ Exclusions:     │    │ Context Req:    │       │   │
│  │    │ • pesticide     │    │ • insurance     │    │ • disease       │       │   │
│  │    │ • fertilizer    │    │ • policy        │    │ • plant type    │       │   │
│  │    │                 │    │                 │    │                 │       │   │
│  │    │ Priority: 10    │    │ Priority: 7     │    │ Priority: 9     │       │   │
│  │    └─────────────────┘    └─────────────────┘    └─────────────────┘       │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                              │
│                                      ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                        Confidence Scoring                                   │   │
│  │                                                                             │   │
│  │    Intent: "insurance"                                                      │   │
│  │    ├─ Keyword matches: insurance(+0.3), crop(+0.3), buy(+0.3)              │   │
│  │    ├─ Exclusions: None found (+0.0)                                        │   │
│  │    ├─ Context boost: farm mentioned (+0.2)                                 │   │
│  │    ├─ Priority multiplier: 10 (highest)                                    │   │
│  │    └─ Final confidence: 0.8                                                │   │
│  │                                                                             │   │
│  │    Intent: "vendor"                                                         │   │
│  │    ├─ Keyword matches: buy(+0.3)                                           │   │
│  │    ├─ Exclusions: insurance(-0.2)                                          │   │
│  │    ├─ Context requirement: No agricultural product (-0.3)                  │   │
│  │    └─ Final confidence: 0.1                                                │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                              │
│                                      ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                           Output                                            │   │
│  │                                                                             │   │
│  │    Primary Intent: "insurance" (confidence: 0.8)                           │   │
│  │    └─ Route to: InsuranceNode                                               │   │
│  │                                                                             │   │
│  │    All Intents:                                                             │   │
│  │    ├─ insurance: 0.8                                                        │   │
│  │    ├─ treatment: 0.2                                                        │   │
│  │    ├─ vendor: 0.1                                                           │   │
│  │    └─ classification: 0.0                                                   │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow Patterns

### 1. New Session Initialization
```
User Request → Initial Node → Intent Analysis → Route to Service Node → Update State → Response
```

### 2. Follow-up Conversations  
```
User Request → Followup Node → Loop Prevention Check → Intent Analysis → Route/Complete → Response
```

### 3. Multi-Service Workflow
```
Disease Image → Classification → Treatment → Insurance → Vendors → Completion
     ▲              │             │           │           │           │
     └──────────────┴─────────────┴───────────┴───────────┴───────────┘
                            State Accumulation
```

### 4. Error Recovery Flow
```
Service Failure → Error Node → Log/Track → Fallback Response → Continue/Restart
```

## Performance Characteristics

### Response Time Targets
- **Intent Analysis**: < 100ms
- **Disease Classification**: < 2s
- **Insurance Premium Calc**: < 3s  
- **Treatment Recommendations**: < 1s
- **Complete Workflow**: < 10s

### Scalability Metrics
- **Concurrent Sessions**: 1000+
- **Requests/Second**: 100+
- **Session Storage**: 10GB+
- **ML Model Memory**: 2GB per instance

### Reliability Features
- **Circuit Breakers**: Prevent cascade failures
- **Retry Logic**: Automatic retry with backoff
- **Graceful Degradation**: Fallback responses when services are down
- **Health Checks**: Continuous monitoring of all components

This architecture provides a solid foundation for agricultural intelligence services while maintaining flexibility for future enhancements and integrations.
