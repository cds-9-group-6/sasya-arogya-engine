# LLM Contextual Next Steps - Test Suite

This directory contains comprehensive tests for the new LLM-driven contextual next steps functionality implemented in `completed_node.py`.

## Test Files

### 1. `test_llm_contextual_next_steps.py`
**Comprehensive Unit Test Suite**

- **Purpose**: Automated testing using Python unittest framework
- **Coverage**: All functions and edge cases
- **Mocking**: Uses mock LLM responses for predictable testing

**Test Categories**:
- ✅ Context building for different workflow states
- ✅ Prompt formatting and LLM integration
- ✅ Response parsing (JSON, bullet points, numbered lists)
- ✅ Fallback mechanisms when LLM fails
- ✅ Error handling and edge cases
- ✅ Integration scenarios

**Run Tests**:
```bash
cd /Users/aathalye/dev/sasya-arogya-engine
python3 -m unittest test_llm_contextual_next_steps.py -v
```

### 2. `manual_test_llm_next_steps.py`
**Interactive Manual Testing**

- **Purpose**: Visual demonstration and manual testing
- **Coverage**: Real-world scenarios with detailed output
- **Mock LLM**: Context-aware responses based on workflow state

**Test Scenarios**:
- 🆕 **New Session**: First-time user interaction
- 🦠 **Disease Detected**: Plant disease identified, no treatment yet
- 🌿 **Healthy Plant**: Healthy plant analysis complete
- 💊 **Treatment Given**: Disease + treatment recommendations provided
- ✅ **Full Workflow**: Complete workflow (disease + treatment + insurance)

**Run Manual Tests**:
```bash
cd /Users/aathalye/dev/sasya-arogya-engine
python3 manual_test_llm_next_steps.py
```

## Key Testing Features

### 🧪 **Comprehensive Coverage**
- **Context Building**: Tests all workflow state combinations
- **Prompt Engineering**: Validates LLM prompt structure and content
- **Response Parsing**: Handles JSON, bullets, numbered lists, malformed responses
- **Fallback Logic**: Tests graceful degradation when LLM fails
- **Integration**: End-to-end workflow testing

### 🎯 **Scenario Testing**
Each test scenario validates:
- **Context Extraction**: Proper extraction of completed operations, available data, user context
- **Prompt Generation**: Contextually relevant LLM prompts
- **Response Intelligence**: LLM generates appropriate next steps for the situation
- **Fallback Handling**: Robust operation when LLM is unavailable

### 🔄 **Mock LLM Behavior**
The test suite includes a sophisticated mock LLM that:
- Returns contextually appropriate responses based on workflow state
- Simulates different response formats (JSON, bullets, text)
- Tests error conditions and malformed responses
- Validates prompt content and structure

## Example Test Output

### New Session Scenario
```
📋 CONTEXT BUILT:
   Completed Operations: {'classification': False, 'prescription': False, 'insurance': False}
   
📝 PROMPT CONTEXT:
   ✅ COMPLETED: None (new session)
   💬 RECENT: Hello, I need help with my plants
   
🎯 GENERATED NEXT STEPS:
   1. 🔍 Upload plant image for disease diagnosis
   2. 🛡️ Explore crop insurance options for protection
   3. ❓ Ask general questions about plant care
```

### Disease Detected Scenario
```
📋 CONTEXT BUILT:
   Completed Operations: {'classification': True, 'prescription': False, 'insurance': False}
   Available Data: ['disease_info']
   User Context: {'plant_type': 'tomato', 'farmer_name': 'John', 'location': 'Karnataka'}
   
📝 PROMPT CONTEXT:
   ✅ COMPLETED: classification
   🌿 PLANT STATUS: diseased (tomato_late_blight) (confidence: 87%)
   👤 USER: plant: tomato, farmer: John, location: Karnataka
   💬 RECENT: My tomato plants have dark spots on leaves
   
🎯 GENERATED NEXT STEPS:
   1. 💊 Get treatment recommendations for this disease
   2. 🛡️ Get crop insurance recommendations based on this disease
   3. 📸 Upload another plant image for analysis
```

## Benefits Demonstrated

### ✅ **LLM-Driven Intelligence**
- No hardcoded boolean logic
- Context-aware suggestions
- Natural language understanding

### ✅ **Extensibility**
- Add new services → update prompt → automatic integration
- No code changes needed for new workflow patterns

### ✅ **Robustness**
- Graceful fallback when LLM fails
- Multiple response format handling
- Error recovery and logging

### ✅ **Contextual Relevance**
- Considers completed operations
- Uses conversation history
- Respects user context (plant type, location, farmer name)

## Running All Tests

```bash
# Run unit tests
python3 -m unittest test_llm_contextual_next_steps.py -v

# Run manual demonstration
python3 manual_test_llm_next_steps.py

# Check test file syntax
python3 -m py_compile test_llm_contextual_next_steps.py
python3 -m py_compile manual_test_llm_next_steps.py
```

This test suite validates that the new LLM-driven approach successfully replaces the problematic hardcoded boolean logic with intelligent, contextual, and extensible next step generation.
