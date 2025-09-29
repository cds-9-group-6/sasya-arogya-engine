#!/bin/bash

# Sasya Arogya Engine - Automated Setup Script
# This script sets up the development environment for the Sasya Arogya Engine

set -e  # Exit on any error

echo "🌾 Sasya Arogya Engine - Automated Setup"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    local missing_deps=()
    
    # Check Python version
    if command_exists python3; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1-2)
        REQUIRED_VERSION="3.11"
        if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
            missing_deps+=("python3.11+")
        else
            log_success "Python $PYTHON_VERSION found"
        fi
    else
        missing_deps+=("python3")
    fi
    
    # Check UV
    if ! command_exists uv; then
        missing_deps+=("uv")
    else
        log_success "UV package manager found"
    fi
    
    # Check Git
    if ! command_exists git; then
        missing_deps+=("git")
    else
        log_success "Git found"
    fi
    
    # Check Docker/Podman (optional)
    if ! command_exists docker && ! command_exists podman; then
        log_warning "Docker/Podman not found - some features may not work"
    else
        if command_exists docker; then
            log_success "Docker found"
        fi
        if command_exists podman; then
            log_success "Podman found"
        fi
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        log_error "Missing dependencies: ${missing_deps[*]}"
        echo ""
        echo "Please install the missing dependencies:"
        echo "  - Python 3.11+: https://python.org/downloads/"
        echo "  - UV: curl -LsSf https://astral.sh/uv/install.sh | sh"
        echo "  - Git: https://git-scm.com/downloads"
        exit 1
    fi
}

# Create .env file from template
setup_env_file() {
    log_info "Setting up environment configuration..."
    
    if [ ! -f .env ]; then
        cat > .env << EOL
# Sasya Arogya Engine Configuration

# Core Services
OLLAMA_BASE_URL=http://localhost:11434
PRESCRIPTION_ENGINE_URL=http://localhost:8081
SASYA_AROGYA_MCP_URL=http://localhost:8001

# Optional Services  
MLFLOW_TRACKING_URI=http://localhost:5000

# Performance Settings
MAX_CONCURRENT_SESSIONS=1000
REQUEST_TIMEOUT=30
WORKER_PROCESSES=4

# Security Settings
API_KEY_REQUIRED=false
CORS_ORIGINS=["http://localhost:3000"]

# Development Settings
DEBUG=true
LOG_LEVEL=INFO
METRICS_ENABLED=true
EOL
        log_success "Created .env configuration file"
    else
        log_warning ".env file already exists - skipping"
    fi
}

# Setup Python environment
setup_python_env() {
    log_info "Setting up Python virtual environment..."
    
    # Initialize UV project (if not already done)
    if [ ! -f pyproject.toml ]; then
        uv init --no-readme --no-pin-python
        log_success "Initialized UV project"
    fi
    
    # Create virtual environment
    if [ ! -d .venv ]; then
        uv venv
        log_success "Created virtual environment"
    else
        log_warning "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source .venv/bin/activate
    log_success "Activated virtual environment"
    
    # Install dependencies
    log_info "Installing Python dependencies..."
    uv add fastapi uvicorn python-multipart
    
    if [ -f requirements.txt ]; then
        uv pip install -r requirements.txt
        log_success "Installed requirements.txt dependencies"
    fi
    
    # Install development dependencies
    log_info "Installing development dependencies..."
    uv add --dev pytest black flake8 mypy pre-commit
    log_success "Installed development dependencies"
}

# Setup pre-commit hooks
setup_precommit() {
    log_info "Setting up pre-commit hooks..."
    
    if command_exists pre-commit; then
        # Activate virtual environment
        source .venv/bin/activate
        
        # Create pre-commit config if it doesn't exist
        if [ ! -f .pre-commit-config.yaml ]; then
            cat > .pre-commit-config.yaml << EOL
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
  
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        args: [--line-length=120]
  
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=120, --ignore=E203,W503]
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-requests]
EOL
            log_success "Created .pre-commit-config.yaml"
        fi
        
        # Install pre-commit hooks
        pre-commit install
        log_success "Installed pre-commit hooks"
    else
        log_warning "Pre-commit not installed - skipping hook setup"
    fi
}

# Setup external services
setup_external_services() {
    log_info "Setting up external services..."
    
    # Create docker-compose for external services
    if command_exists docker || command_exists podman; then
        if [ ! -f docker-compose.dev.yml ]; then
            cat > docker-compose.dev.yml << EOL
version: '3.8'

services:
  ollama:
    image: ollama/ollama:latest
    container_name: sasya-ollama-dev
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0
    command: >
      sh -c "ollama serve & 
             sleep 10 && 
             ollama pull llama3.1:8b && 
             wait"
    
  mcp-server:
    build:
      context: ../sasya-arogya-mcp
      dockerfile: Dockerfile
    container_name: sasya-mcp-dev
    ports:
      - "8001:8001"
    environment:
      - PORT=8001
      - HOST=0.0.0.0
    volumes:
      - ./mcp-data:/app/data
      
  mlflow:
    image: python:3.11-slim
    container_name: sasya-mlflow-dev
    ports:
      - "5000:5000"
    command: >
      bash -c "pip install mlflow && 
               mlflow server --host 0.0.0.0 --port 5000 --backend-store-uri sqlite:///mlflow.db"
    volumes:
      - mlflow_data:/mlflow

volumes:
  ollama_data:
  mlflow_data:
EOL
            log_success "Created docker-compose.dev.yml for external services"
        fi
    fi
}

# Create helpful scripts
create_scripts() {
    log_info "Creating helpful development scripts..."
    
    # Create start script
    cat > start-dev.sh << EOL
#!/bin/bash
# Start development environment

source .venv/bin/activate

echo "🚀 Starting Sasya Arogya Engine Development Environment"

# Start external services
echo "📦 Starting external services..."
docker-compose -f docker-compose.dev.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 15

# Check service health
echo "🔍 Checking service health..."
curl -f http://localhost:11434/api/tags > /dev/null 2>&1 && echo "✅ Ollama ready" || echo "❌ Ollama not ready"
curl -f http://localhost:8001/health > /dev/null 2>&1 && echo "✅ MCP Server ready" || echo "❌ MCP Server not ready"
curl -f http://localhost:5000 > /dev/null 2>&1 && echo "✅ MLflow ready" || echo "❌ MLflow not ready"

# Start main engine
echo "🌾 Starting Sasya Arogya Engine..."
uvicorn api.agent_api:app --reload --port 8080 --host 0.0.0.0
EOL
    chmod +x start-dev.sh
    log_success "Created start-dev.sh script"
    
    # Create test script
    cat > run-tests.sh << EOL
#!/bin/bash
# Run tests with coverage

source .venv/bin/activate

echo "🧪 Running Sasya Arogya Engine Tests"

# Run linting
echo "🔍 Running code quality checks..."
black --check fsm_agent/ tests/ || (echo "❌ Black formatting failed" && exit 1)
flake8 fsm_agent/ tests/ || (echo "❌ Flake8 linting failed" && exit 1)
mypy fsm_agent/ || (echo "❌ MyPy type checking failed" && exit 1)

# Run tests with coverage
echo "🧪 Running tests with coverage..."
python -m pytest --cov=fsm_agent --cov-report=html --cov-report=term

echo "✅ All tests passed!"
echo "📊 Coverage report generated in htmlcov/index.html"
EOL
    chmod +x run-tests.sh
    log_success "Created run-tests.sh script"
    
    # Create Makefile
    cat > Makefile << EOL
.PHONY: help install test lint format clean start stop

help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*\$\$' \$(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\\n", \$\$1, \$\$2}'

install:  ## Install dependencies
	uv pip install -r requirements.txt
	uv add --dev pytest black flake8 mypy pre-commit

test:  ## Run tests with coverage
	./run-tests.sh

lint:  ## Run linting and type checking
	source .venv/bin/activate && black --check fsm_agent/ tests/
	source .venv/bin/activate && flake8 fsm_agent/ tests/
	source .venv/bin/activate && mypy fsm_agent/

format:  ## Format code with black
	source .venv/bin/activate && black fsm_agent/ tests/

start:  ## Start development environment
	./start-dev.sh

stop:  ## Stop development environment
	docker-compose -f docker-compose.dev.yml down

clean:  ## Clean up temporary files
	rm -rf __pycache__ .pytest_cache .mypy_cache htmlcov/ .coverage
	find . -name "*.pyc" -delete

dev-setup:  ## Complete development setup
	./setup.sh
EOL
    log_success "Created Makefile with common tasks"
}

# Verify installation
verify_installation() {
    log_info "Verifying installation..."
    
    # Check if virtual environment works
    source .venv/bin/activate
    
    # Check if main dependencies are installed
    python -c "import fastapi; import uvicorn; print('FastAPI and Uvicorn installed')" || {
        log_error "FastAPI/Uvicorn installation failed"
        exit 1
    }
    
    # Check if development tools work
    black --version > /dev/null 2>&1 || {
        log_error "Black installation failed"
        exit 1
    }
    
    pytest --version > /dev/null 2>&1 || {
        log_error "Pytest installation failed"  
        exit 1
    }
    
    log_success "All core dependencies verified"
}

# Print final instructions
print_final_instructions() {
    echo ""
    echo "🎉 Setup completed successfully!"
    echo "================================"
    echo ""
    echo "Next steps:"
    echo ""
    echo "1. Start the development environment:"
    echo "   ${GREEN}./start-dev.sh${NC}"
    echo ""
    echo "2. Or start services manually:"
    echo "   ${BLUE}# Activate virtual environment${NC}"
    echo "   ${YELLOW}source .venv/bin/activate${NC}"
    echo ""
    echo "   ${BLUE}# Start external services${NC}"
    echo "   ${YELLOW}docker-compose -f docker-compose.dev.yml up -d${NC}"
    echo ""
    echo "   ${BLUE}# Start main engine${NC}"
    echo "   ${YELLOW}uvicorn api.agent_api:app --reload --port 8080${NC}"
    echo ""
    echo "3. Run tests:"
    echo "   ${YELLOW}./run-tests.sh${NC} or ${YELLOW}make test${NC}"
    echo ""
    echo "4. View all available commands:"
    echo "   ${YELLOW}make help${NC}"
    echo ""
    echo "5. Access the application:"
    echo "   ${BLUE}Health check:${NC} http://localhost:8080/health"
    echo "   ${BLUE}API docs:${NC} http://localhost:8080/docs"
    echo "   ${BLUE}MLflow:${NC} http://localhost:5000"
    echo ""
    echo "📖 For more information, see:"
    echo "   - README.md - Overview and usage"
    echo "   - CONTRIBUTING.md - Development guidelines"
    echo "   - DEPLOYMENT.md - Production deployment"
    echo ""
    log_success "Happy coding! 🌾✨"
}

# Main execution
main() {
    echo ""
    log_info "Starting automated setup process..."
    echo ""
    
    check_prerequisites
    setup_env_file
    setup_python_env
    setup_precommit
    setup_external_services
    create_scripts
    verify_installation
    
    print_final_instructions
}

# Run main function
main "$@"
