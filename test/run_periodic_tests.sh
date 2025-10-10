#!/bin/bash

# Sasya Arogya Engine Periodic Test Runner
# This script runs the periodic test suite for the Sasya Arogya Engine
# Designed to run in OpenShift Kubernetes cluster
#
# Usage: ./run_periodic_tests.sh [ENGINE_URL]
# Example: ./run_periodic_tests.sh http://sasya-engine-service:8080

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="test_engine_periodic.py"
LOG_DIR="/tmp/sasya_engine_tests"

# Help function
show_help() {
    echo "Sasya Arogya Engine Periodic Test Runner"
    echo ""
    echo "Usage: $0 [OPTIONS] [ENGINE_URL]"
    echo ""
    echo "Arguments:"
    echo "  ENGINE_URL              Engine service URL (default: http://localhost:8080)"
    echo ""
    echo "Options:"
    echo "  -h, --help              Show this help message"
    echo "  -t, --max-tests NUM     Maximum tests per category (default: 3)"
    echo "  -p, --python PATH       Python executable path (default: python3)"
    echo ""
    echo "Environment Variables:"
    echo "  SASYA_ENGINE_URL        Engine service URL (overridden by argument)"
    echo "  MAX_TESTS_PER_CATEGORY  Maximum tests per category (overridden by -t)"
    echo "  PYTHON_PATH             Python executable path (overridden by -p)"
    echo ""
    echo "Examples:"
    echo "  $0 http://sasya-engine-service:8080"
    echo "  $0 -t 5 http://localhost:8080"
    echo "  $0 --max-tests 2 --python python3.11 http://engine:8080"
}

# Parse command line arguments
MAX_TESTS_PER_CATEGORY="${MAX_TESTS_PER_CATEGORY:-3}"
PYTHON_PATH="${PYTHON_PATH:-python3}"
ENGINE_URL=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -t|--max-tests)
            MAX_TESTS_PER_CATEGORY="$2"
            shift 2
            ;;
        -p|--python)
            PYTHON_PATH="$2"
            shift 2
            ;;
        http://*|https://*)
            ENGINE_URL="$1"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Set default ENGINE_URL if not provided
if [ -z "$ENGINE_URL" ]; then
    ENGINE_URL="${SASYA_ENGINE_URL:-http://localhost:8080}"
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# Function to check if engine is running
check_engine_health() {
    log_info "Checking engine health at $ENGINE_URL"
    
    if command -v curl >/dev/null 2>&1; then
        if curl -s --max-time 10 "$ENGINE_URL/health" >/dev/null 2>&1; then
            log_success "Engine is healthy and responding"
            return 0
        else
            log_error "Engine health check failed"
            return 1
        fi
    else
        log_warning "curl not available, skipping health check"
        return 0
    fi
}

# Function to install Python dependencies
install_dependencies() {
    log_info "Installing Python dependencies"
    
    # Check if test_requirements.txt exists
    if [ -f "test_requirements.txt" ]; then
        log_info "Installing from test_requirements.txt"
        $PYTHON_PATH -m pip install -r test_requirements.txt --quiet
    elif [ -f "requirements.txt" ]; then
        log_info "Installing from requirements.txt"
        $PYTHON_PATH -m pip install -r requirements.txt --quiet
    else
        log_info "Installing required packages directly"
        $PYTHON_PATH -m pip install aiohttp --quiet
    fi
    
    # Verify aiohttp is installed
    if $PYTHON_PATH -c "import aiohttp" 2>/dev/null; then
        log_success "Dependencies installed successfully"
    else
        log_error "Failed to install aiohttp dependency"
        return 1
    fi
}

# Function to create test images directory if it doesn't exist
setup_test_images() {
    log_info "Setting up test images directory"
    
    TEST_IMAGES_DIR="resources/images_for_test"
    
    if [ ! -d "$TEST_IMAGES_DIR" ]; then
        log_info "Creating test images directory: $TEST_IMAGES_DIR"
        mkdir -p "$TEST_IMAGES_DIR"
        
        # Create placeholder files for test images
        # In a real deployment, these would be actual test images
        log_warning "Test images directory created but no images found"
        log_warning "Please ensure test images are available in $TEST_IMAGES_DIR"
        log_warning "Required images: rice_leaf_blight.jpg, apple_leaf_disease.jpg, tomato_disease.jpg, wheat_rust.jpg"
    else
        log_success "Test images directory exists: $TEST_IMAGES_DIR"
    fi
}

# Function to create log directory
setup_logging() {
    log_info "Setting up logging directory: $LOG_DIR"
    mkdir -p "$LOG_DIR"
    
    # Set log file with timestamp
    TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
    LOG_FILE="$LOG_DIR/periodic_test_$TIMESTAMP.log"
    
    log_info "Log file: $LOG_FILE"
}

# Function to run the tests
run_tests() {
    log_info "Starting periodic test execution"
    
    # Set environment variables
    export SASYA_ENGINE_URL="$ENGINE_URL"
    export MAX_TESTS_PER_CATEGORY="$MAX_TESTS_PER_CATEGORY"
    
    # Run the Python test script
    if [ -f "$PYTHON_SCRIPT" ]; then
        log_info "Executing test script: $PYTHON_SCRIPT"
        
        # Check if timeout command is available
        if command -v timeout >/dev/null 2>&1; then
            # Use timeout command if available
            timeout 300 $PYTHON_PATH "$PYTHON_SCRIPT" 2>&1 | tee "$LOG_FILE"
            EXIT_CODE=${PIPESTATUS[0]}
        else
            # Fallback: run without timeout (Python script has its own timeout handling)
            log_warning "timeout command not available, running without external timeout"
            $PYTHON_PATH "$PYTHON_SCRIPT" 2>&1 | tee "$LOG_FILE"
            EXIT_CODE=${PIPESTATUS[0]}
        fi
        
        # Check exit status
        if [ $EXIT_CODE -eq 0 ]; then
            log_success "Test execution completed successfully"
            return 0
        elif [ $EXIT_CODE -eq 124 ]; then
            log_error "Test execution timed out (external timeout)"
            return 1
        elif [ $EXIT_CODE -eq 1 ]; then
            log_error "Test execution failed or timed out (internal timeout)"
            return 1
        else
            log_error "Test execution failed with exit code: $EXIT_CODE"
            return 1
        fi
    else
        log_error "Test script not found: $PYTHON_SCRIPT"
        return 1
    fi
}

# Function to cleanup old logs
cleanup_old_logs() {
    log_info "Cleaning up old log files (keeping last 10)"
    
    if [ -d "$LOG_DIR" ]; then
        # Keep only the last 10 log files
        find "$LOG_DIR" -name "periodic_test_*.log" -type f -printf '%T@ %p\n' | \
        sort -rn | tail -n +11 | cut -d' ' -f2- | xargs -r rm -f
        
        log_success "Old log files cleaned up"
    fi
}

# Function to send notification (if configured)
send_notification() {
    local status="$1"
    local message="$2"
    
    # Check if notification webhook is configured
    if [ -n "$NOTIFICATION_WEBHOOK" ]; then
        log_info "Sending notification: $message"
        
        # Send webhook notification
        curl -X POST "$NOTIFICATION_WEBHOOK" \
            -H "Content-Type: application/json" \
            -d "{\"status\":\"$status\",\"message\":\"$message\",\"timestamp\":\"$(date -Iseconds)\"}" \
            2>/dev/null || log_warning "Failed to send notification"
    fi
}

# Main execution
main() {
    log_info "🌾 Sasya Arogya Engine Periodic Test Runner"
    log_info "============================================="
    log_info "Engine URL: $ENGINE_URL"
    log_info "Max tests per category: $MAX_TESTS_PER_CATEGORY"
    log_info "Python path: $PYTHON_PATH"
    log_info "============================================="
    
    # Change to script directory
    cd "$SCRIPT_DIR"
    
    # Setup
    setup_logging
    setup_test_images
    
    # Check engine health
    if ! check_engine_health; then
        log_error "Engine health check failed. Exiting."
        send_notification "error" "Engine health check failed"
        exit 1
    fi
    
    # Install dependencies
    if ! install_dependencies; then
        log_error "Failed to install dependencies. Exiting."
        send_notification "error" "Failed to install Python dependencies"
        exit 1
    fi
    
    # Run tests
    if run_tests; then
        log_success "All tests completed successfully"
        send_notification "success" "Periodic tests completed successfully"
        exit 0
    else
        log_error "Tests failed or encountered errors"
        send_notification "error" "Periodic tests failed"
        exit 1
    fi
}

# Handle script interruption
trap 'log_warning "Script interrupted"; send_notification "warning" "Periodic tests interrupted"; exit 130' INT TERM

# Run main function
main "$@"
