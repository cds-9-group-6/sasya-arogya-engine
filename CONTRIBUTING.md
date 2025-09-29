# 🤝 Contributing to Sasya Arogya Engine

Thank you for your interest in contributing to the Sasya Arogya Engine! We welcome contributions from developers, researchers, agricultural experts, and anyone passionate about improving agriculture through technology.

## 🎯 Ways to Contribute

### 🐛 **Bug Reports**
- Report bugs via [GitHub Issues](https://github.com/your-org/sasya-arogya-engine/issues)
- Use the bug report template
- Include detailed reproduction steps
- Attach logs, screenshots, or error messages

### ✨ **Feature Requests**
- Propose new features through [GitHub Discussions](https://github.com/your-org/sasya-arogya-engine/discussions)
- Describe the agricultural use case
- Explain the expected benefit
- Consider implementation complexity

### 📖 **Documentation**
- Improve README, API docs, or guides
- Add code examples and tutorials
- Translate documentation to local languages
- Create video tutorials or walkthroughs

### 🧪 **Testing & QA**
- Test new features and report issues
- Improve test coverage
- Add integration tests
- Performance and load testing

### 💻 **Code Contributions**
- Fix bugs and implement features
- Optimize performance
- Add new agricultural services
- Improve code quality and architecture

## 🚀 Getting Started

### 1. **Development Environment Setup**

#### Prerequisites
- Python 3.11+
- Git
- UV package manager
- Docker/Podman (for full stack testing)

#### Initial Setup
```bash
# Fork the repository on GitHub
# Clone your fork
git clone https://github.com/yourusername/sasya-arogya-engine.git
cd sasya-arogya-engine

# Add upstream remote
git remote add upstream https://github.com/original-org/sasya-arogya-engine.git

# Create virtual environment
uv venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install development dependencies
uv add --dev pytest black flake8 mypy pre-commit
uv pip install -r requirements.txt

# Install pre-commit hooks
pre-commit install
```

### 2. **Running the Development Environment**

```bash
# Start external services (in separate terminals)
ollama serve                                    # Terminal 1: Ollama
cd sasya-arogya-mcp && python mcp_http_server.py  # Terminal 2: MCP Server  
mlflow server --host 127.0.0.1 --port 5000       # Terminal 3: MLflow (optional)

# Start the main engine
uvicorn api.agent_api:app --reload --port 8080    # Terminal 4: Main Engine

# Verify setup
curl http://localhost:8080/health
```

### 3. **Development Workflow**

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make your changes
# ... edit files ...

# Run quality checks
make lint      # or: black . && flake8 . && mypy .
make test      # or: python -m pytest
make coverage  # or: python -m pytest --cov=fsm_agent

# Commit changes
git add .
git commit -m "feat: add your feature description"

# Push to your fork
git push origin feature/your-feature-name

# Create Pull Request on GitHub
```

## 📋 Development Guidelines

### **Code Style**

#### Python Code Standards
```python
# Use Black for formatting (120 char line length)
black --line-length 120 fsm_agent/ tests/

# Follow PEP 8 naming conventions
class MyNewNode(BaseNode):      # PascalCase for classes
    def my_method(self):        # snake_case for methods
        my_variable = "value"   # snake_case for variables

# Type hints are required
def process_data(input_data: Dict[str, Any]) -> Optional[str]:
    """Process input data and return result.
    
    Args:
        input_data: Dictionary containing input parameters
        
    Returns:
        Processed result string or None if processing failed
    """
    pass
```

#### Documentation Standards
```python
class MyService:
    """Service for handling agricultural data.
    
    This service provides methods for processing agricultural
    data including crop information and disease analysis.
    
    Attributes:
        config: Configuration dictionary
        logger: Logger instance for this service
    """
    
    def analyze_crop(self, image_data: bytes, crop_type: str) -> Dict[str, Any]:
        """Analyze crop image for disease detection.
        
        Args:
            image_data: Raw image bytes
            crop_type: Type of crop (e.g., 'rice', 'wheat')
            
        Returns:
            Dictionary containing:
                - disease_name: Detected disease name
                - confidence: Confidence score (0-1)
                - severity: Severity level
                
        Raises:
            ValueError: If image_data is invalid
            ProcessingError: If analysis fails
        """
        pass
```

### **Testing Requirements**

#### Unit Tests
```python
# tests/test_insurance_node.py
import pytest
from fsm_agent.core.nodes.insurance_node import InsuranceNode
from fsm_agent.core.workflow_state import WorkflowState

class TestInsuranceNode:
    @pytest.fixture
    def insurance_node(self):
        return InsuranceNode()
    
    @pytest.fixture
    def sample_state(self):
        return WorkflowState(
            session_id="test-session",
            user_message="I need crop insurance"
        )
    
    async def test_execute_with_valid_context(self, insurance_node, sample_state):
        """Test insurance node execution with valid context."""
        # Given
        sample_state.update({
            "crop": "wheat",
            "area_hectare": 5.0,
            "state": "Punjab"
        })
        
        # When
        result_state = await insurance_node.execute(sample_state)
        
        # Then
        assert result_state.get("insurance_premium_details") is not None
        assert result_state.get("next_action") == "followup"
```

#### Integration Tests
```python
# tests/integration/test_full_workflow.py
import pytest
import requests
from tests.fixtures import sample_requests

class TestFullWorkflow:
    def test_disease_to_insurance_workflow(self):
        """Test complete workflow from disease diagnosis to insurance."""
        # 1. Disease diagnosis
        diagnosis_response = requests.post(
            "http://localhost:8080/chat-stream",
            json=sample_requests.disease_diagnosis
        )
        assert diagnosis_response.status_code == 200
        
        # 2. Insurance request in same session
        insurance_response = requests.post(
            "http://localhost:8080/chat-stream", 
            json=sample_requests.insurance_followup
        )
        assert insurance_response.status_code == 200
        assert "premium" in insurance_response.json()["response"].lower()
```

### **Architecture Patterns**

#### Adding New Services
```python
# 1. Create tool (fsm_agent/tools/weather_tool.py)
from .base_tool import BaseTool

class WeatherTool(BaseTool):
    name = "weather_tool"
    description = "Provides weather information for agricultural planning"
    
    async def _arun(self, location: str, days: int = 7) -> Dict[str, Any]:
        # Implementation here
        pass

# 2. Create node (fsm_agent/core/nodes/weather_node.py)  
from .base_node import BaseNode

class WeatherNode(BaseNode):
    async def execute(self, state: WorkflowState) -> WorkflowState:
        # Implementation here
        return state

# 3. Register in node factory (fsm_agent/core/nodes/node_factory.py)
from .weather_node import WeatherNode

def _create_nodes(self) -> Dict[str, BaseNode]:
    return {
        # ... existing nodes
        "weather": WeatherNode()
    }

# 4. Add intent rules (fsm_agent/core/intent_analyzer.py)
weather_rule = IntentRule(
    service="weather",
    keywords=["weather", "forecast", "rain", "temperature"],
    priority=7,
    min_confidence=0.6
)
```

#### State Management Best Practices
```python
# Always use WorkflowState methods
state.update({"new_field": "value"})           # ✅ Good
state["new_field"] = "value"                   # ❌ Avoid direct assignment

# Validate state before processing
required_fields = ["crop", "location"]
missing = [f for f in required_fields if not state.get(f)]
if missing:
    raise ValueError(f"Missing required fields: {missing}")

# Use type hints for state fields
def process_insurance_data(state: WorkflowState) -> Optional[Dict[str, Any]]:
    crop: str = state.get("crop")
    area: float = state.get("area_hectare", 0.0)
    # Process with proper types
```

### **Error Handling Standards**

```python
import logging
from typing import Optional

logger = logging.getLogger(__name__)

async def process_request(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process agricultural data request with proper error handling."""
    try:
        # Validate input
        if not data.get("crop"):
            raise ValueError("Crop type is required")
            
        # Process data
        result = await external_service_call(data)
        
        # Log success
        logger.info(f"Successfully processed request for crop: {data['crop']}")
        return {"success": True, "result": result}
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return {"success": False, "error": "invalid_input", "message": str(e)}
        
    except ConnectionError as e:
        logger.error(f"Service connection failed: {str(e)}")
        return {"success": False, "error": "service_unavailable", "message": "Service temporarily unavailable"}
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return {"success": False, "error": "internal_error", "message": "An internal error occurred"}
```

## 🧪 Testing Guidelines

### **Running Tests**

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_insurance_node.py -v

# Run tests with coverage
python -m pytest --cov=fsm_agent --cov-report=html

# Run integration tests only
python -m pytest tests/integration/ -v

# Run performance tests
python -m pytest tests/performance/ -v
```

### **Writing Tests**

#### Test Categories
1. **Unit Tests**: Test individual functions/methods
2. **Integration Tests**: Test component interactions  
3. **End-to-End Tests**: Test complete workflows
4. **Performance Tests**: Test response times and throughput

#### Test Data Management
```python
# tests/fixtures/sample_data.py
SAMPLE_INSURANCE_REQUEST = {
    "message": "I need crop insurance for my wheat farm",
    "session_id": "test-insurance-session",
    "context": {
        "crop": "wheat",
        "area_hectare": 10.0,
        "state": "Punjab"
    }
}

SAMPLE_DISEASE_IMAGE = {
    "message": "Diagnose this plant disease",
    "session_id": "test-disease-session", 
    "image_b64": "base64-encoded-test-image-data"
}
```

#### Mocking External Services
```python
# tests/test_insurance_integration.py
import pytest
from unittest.mock import patch, MagicMock

@patch('fsm_agent.tools.insurance_tool.requests.post')
def test_insurance_premium_calculation(mock_post):
    """Test insurance premium calculation with mocked MCP server."""
    # Given
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "success": True,
        "premium_per_hectare": 2500.0,
        "total_premium": 25000.0
    }
    mock_post.return_value = mock_response
    
    # When
    result = calculate_insurance_premium("wheat", 10.0, "Punjab")
    
    # Then
    assert result["success"] is True
    assert result["total_premium"] == 25000.0
    mock_post.assert_called_once()
```

## 📦 Submitting Contributions

### **Pull Request Guidelines**

#### PR Title Format
```
<type>: <description>

Examples:
feat: add weather advisory service
fix: resolve insurance premium calculation error  
docs: update API documentation with examples
test: add integration tests for vendor service
refactor: improve intent analysis performance
```

#### PR Description Template
```markdown
## Description
Brief description of the changes and why they were made.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed
- [ ] All existing tests pass

## Agricultural Impact
Describe how this change benefits farmers or agricultural workflows.

## Screenshots (if applicable)
Add screenshots or diagrams to help explain your changes.

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review of code completed
- [ ] Code is commented, particularly in hard-to-understand areas
- [ ] Documentation updated (README, API docs, etc.)
- [ ] No new warnings or errors introduced
```

#### Review Process
1. **Automated Checks**: CI pipeline runs tests, linting, and security scans
2. **Code Review**: At least one maintainer reviews the code
3. **Agricultural Review**: Agricultural experts review feature relevance (for new features)
4. **Testing**: Manual testing in development environment
5. **Approval**: Maintainer approval required before merge

### **Commit Message Guidelines**

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Format: <type>(<scope>): <description>

feat(insurance): add weather-based premium adjustment
fix(classification): resolve confidence score calculation
docs(api): add insurance endpoint examples  
test(integration): add end-to-end workflow tests
refactor(nodes): improve state management patterns
perf(ml): optimize disease classification inference
ci(docker): update deployment configuration
```

#### Commit Types
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **test**: Adding or fixing tests
- **refactor**: Code refactoring
- **perf**: Performance improvements
- **ci**: CI/CD changes
- **chore**: Maintenance tasks

## 🌾 Agricultural Domain Guidelines

### **Understanding Agricultural Context**

When contributing to agricultural features, consider:

#### **Crop Lifecycle Awareness**
```python
# Consider seasonal variations
CROP_SEASONS = {
    "rice": ["kharif", "rabi"],      # Monsoon and winter seasons
    "wheat": ["rabi"],               # Winter season primarily
    "cotton": ["kharif"],            # Monsoon season
    "sugarcane": ["annual"]          # Year-round crop
}

# Regional variations matter
REGIONAL_CROP_VARIETIES = {
    "punjab": ["wheat", "rice", "cotton"],
    "tamil_nadu": ["rice", "sugarcane", "cotton"],
    "maharashtra": ["cotton", "sugarcane", "soybean"]
}
```

#### **Agricultural Terminology**
- **Hectare**: Standard area measurement (1 hectare = 2.47 acres)
- **Kharif**: Monsoon season crops (June-October)
- **Rabi**: Winter season crops (November-April)
- **Zaid**: Summer season crops (March-June)

#### **Disease Classification Context**
```python
# Consider disease-crop relationships
CROP_DISEASE_MAPPING = {
    "rice": ["bacterial_blight", "blast", "brown_spot"],
    "wheat": ["rust", "bunt", "powdery_mildew"],
    "tomato": ["late_blight", "early_blight", "bacterial_wilt"]
}

# Severity levels have agricultural meaning
DISEASE_SEVERITY = {
    "low": "Early stage, preventive measures sufficient",
    "medium": "Active treatment required",
    "high": "Immediate intervention, potential crop loss",
    "critical": "Severe infection, crop loss likely"
}
```

### **Insurance Domain Knowledge**

#### **Premium Calculation Factors**
```python
PREMIUM_FACTORS = {
    "crop_type": 0.3,        # Different crops have different risk profiles
    "region": 0.25,          # Geographic risk factors
    "season": 0.2,           # Seasonal risk variations
    "farm_size": 0.15,       # Scale advantages/disadvantages
    "historical_claims": 0.1  # Past claim history
}

# Government subsidy patterns
SUBSIDY_RATES = {
    "small_farmer": 0.5,     # Up to 2 hectares
    "medium_farmer": 0.4,    # 2-10 hectares  
    "large_farmer": 0.3      # Above 10 hectares
}
```

## 🎯 Priority Contribution Areas

### **High Priority** 🔴
1. **Bug Fixes**: Critical issues affecting core functionality
2. **Performance**: Response time optimization
3. **Test Coverage**: Increasing test coverage above 90%
4. **Documentation**: API examples and tutorials

### **Medium Priority** 🟡  
1. **New Services**: Weather, soil testing, market prices
2. **ML Improvements**: Better disease classification models
3. **Mobile Optimization**: Improved mobile API responses
4. **Localization**: Support for regional languages

### **Low Priority** 🟢
1. **UI Enhancements**: Better developer experience
2. **Monitoring**: Additional metrics and dashboards
3. **Code Cleanup**: Refactoring for maintainability

## 🎉 Recognition

### **Contributor Acknowledgment**
- All contributors are acknowledged in the README
- Significant contributors get special mention in releases
- Regular contributors may be invited as maintainers

### **Contribution Categories**
- 🏆 **Major Contributors**: 10+ merged PRs or significant features
- 🥇 **Active Contributors**: 5+ merged PRs  
- 🥉 **Contributors**: Any merged PR
- 📖 **Documentation Contributors**: Significant doc improvements
- 🐛 **Bug Hunters**: Multiple bug reports with good reproduction steps

## 📞 Getting Help

### **Communication Channels**
- **GitHub Discussions**: General questions and feature discussions
- **GitHub Issues**: Bug reports and specific problems
- **Email**: [dev@sasyaarogya.com](mailto:dev@sasyaarogya.com) for private inquiries

### **Development Help**
- **Architecture Questions**: Tag maintainers in issues
- **Agricultural Context**: Consult with domain experts
- **Code Review**: Request review from relevant maintainers

---

## 📋 Maintainer Information

### **Core Maintainers**
- **Technical Lead**: [@techmoksha](https://github.com/techmoksha)
- **Agricultural Expert**: [@agri-expert](https://github.com/agri-expert)
- **ML Engineer**: [@ml-engineer](https://github.com/ml-engineer)

### **Review Areas**
- **Backend/API**: Technical Lead, ML Engineer
- **Agricultural Features**: Agricultural Expert, Technical Lead
- **ML/AI Components**: ML Engineer
- **Documentation**: All maintainers

---

Thank you for contributing to Sasya Arogya Engine! Your contributions help empower farmers and improve agricultural outcomes worldwide. 🌾✨
