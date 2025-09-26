#!/bin/bash

# Test script for Sasya Arogya Engine API
# This script tests the API endpoints exposed by the FSM Agent
# Assumes the container/API is already running

set -e  # Exit on any error

# Configuration
DEFAULT_HOST="localhost"
DEFAULT_PORT="8080"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
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

log_section() {
    echo -e "\n${PURPLE}═══ $1 ═══${NC}"
}

# Function to check API connectivity
check_api_connectivity() {
    local host=$1
    local port=$2
    
    log_info "Checking API connectivity at http://$host:$port"
    
    if curl -s --connect-timeout 5 "http://$host:$port/health" > /dev/null 2>&1; then
        log_success "API is accessible"
        return 0
    else
        log_error "API not accessible at http://$host:$port"
        log_info "Please ensure the container/API is running"
        return 1
    fi
}


# Function to make HTTP request and display response
make_request() {
    local method=$1
    local endpoint=$2
    local data=$3
    local description=$4
    local host=$5
    local port=$6
    
    echo -e "\n${CYAN}🔍 Testing: $description${NC}"
    echo "   Method: $method"
    echo "   Endpoint: http://$host:$port$endpoint"
    
    if [ -n "$data" ]; then
        echo "   Data: $data"
        response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
                      -X "$method" \
                      -H "Content-Type: application/json" \
                      -d "$data" \
                      "http://$host:$port$endpoint")
    else
        response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
                      -X "$method" \
                      "http://$host:$port$endpoint")
    fi
    
    # Parse response and status code
    body=$(echo "$response" | sed '$d')
    status_code=$(echo "$response" | tail -n1 | sed 's/.*://')
    
    if [[ "$status_code" =~ ^2[0-9][0-9]$ ]]; then
        log_success "Response (HTTP $status_code):"
        echo "$body" | jq . 2>/dev/null || echo "$body"
    else
        log_error "Request failed (HTTP $status_code):"
        echo "$body"
    fi
    
    echo ""
}

# Function to test streaming endpoint
test_streaming() {
    local host=$1
    local port=$2
    local data=$3
    local description=$4
    
    echo -e "\n${CYAN}🔍 Testing: $description${NC}"
    echo "   Method: POST"
    echo "   Endpoint: http://$host:$port/sasya-chikitsa/chat-stream"
    echo "   Data: $data"
    
    log_info "Streaming for 10 seconds..."
    timeout 10s curl -s \
        -X POST \
        -H "Content-Type: application/json" \
        -d "$data" \
        "http://$host:$port/sasya-chikitsa/chat-stream" || true
    
    echo ""
    log_success "Streaming test completed"
}





# Function to display usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Test script for Sasya Arogya Engine API"
    echo "Assumes the API/container is already running"
    echo ""
    echo "Options:"
    echo "  -h, --host HOST        API host (default: $DEFAULT_HOST)"
    echo "  -p, --port PORT        API port (default: $DEFAULT_PORT)"
    echo "  --help                 Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                     # Test with default settings (localhost:8080)"
    echo "  $0 -h 192.168.1.100    # Test API on different host"
    echo "  $0 -p 8002             # Test API on port 8002"
    echo "  $0 -h 0.0.0.0 -p 8080  # Test API on all interfaces, port 8080"
    echo ""
}

# Main test function
run_tests() {
    local host=$1
    local port=$2
    
    log_section "API ENDPOINT TESTS"
    
    # Test basic endpoints
    make_request "GET" "/" "" "Root endpoint" "$host" "$port"
    make_request "GET" "/health" "" "Health check" "$host" "$port"
    make_request "GET" "/sasya-chikitsa/stats" "" "Agent statistics" "$host" "$port"
    
    # Test chat endpoint with simple message
    local simple_chat='{"message": "Hello, can you help me with plant disease diagnosis?"}'
    make_request "POST" "/sasya-chikitsa/chat" "$simple_chat" "Simple chat message" "$host" "$port"
    
    # Test chat endpoint with image (base64 encoded)
    local image_chat='{"message": "What disease is affecting this plant?", "image_b64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="}'
    make_request "POST" "/sasya-chikitsa/chat" "$image_chat" "Chat with image" "$host" "$port"
    
    # Test session endpoints (use session ID from previous response if available)
    local test_session_id="session_12345678_1234567890"
    make_request "GET" "/sasya-chikitsa/session/$test_session_id" "" "Get session info" "$host" "$port"
    make_request "GET" "/sasya-chikitsa/session/$test_session_id/history" "" "Get conversation history" "$host" "$port"
    make_request "GET" "/sasya-chikitsa/session/$test_session_id/classification" "" "Get classification results" "$host" "$port"
    make_request "GET" "/sasya-chikitsa/session/$test_session_id/prescription" "" "Get prescription data" "$host" "$port"
    
    # Test session cleanup
    make_request "POST" "/sasya-chikitsa/cleanup" "" "Cleanup sessions" "$host" "$port"
    
    # Test streaming endpoint
    test_streaming "$host" "$port" "$simple_chat" "Streaming chat"
    
    # Test session continuation
    local continue_chat='{"session_id": "'$test_session_id'", "message": "Can you provide more details about the treatment?"}'
    make_request "POST" "/sasya-chikitsa/chat" "$continue_chat" "Continue chat session" "$host" "$port"
    
    # Test session deletion
    make_request "DELETE" "/sasya-chikitsa/session/$test_session_id" "" "End session" "$host" "$port"
    
    log_section "ALL TESTS COMPLETED"
    log_success "API testing finished successfully!"
}

# Parse command line arguments
HOST="$DEFAULT_HOST"
PORT="$DEFAULT_PORT"

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--host)
            HOST="$2"
            shift 2
            ;;
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Main execution
echo -e "${PURPLE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${PURPLE}║                 SASYA AROGYA ENGINE API TESTER               ║${NC}"
echo -e "${PURPLE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check dependencies
log_section "DEPENDENCY CHECK"

# Check curl
if ! command -v curl &> /dev/null; then
    log_error "curl is required but not installed"
    exit 1
fi
log_success "curl is available"

# Check jq (optional but recommended)
if command -v jq &> /dev/null; then
    log_success "jq is available (JSON formatting enabled)"
else
    log_warning "jq not found (JSON responses will not be formatted)"
fi

# Check API connectivity
log_section "API CONNECTIVITY CHECK"
if ! check_api_connectivity "$HOST" "$PORT"; then
    exit 1
fi

# Run tests
echo ""
log_info "Testing API at http://$HOST:$PORT"
echo "Configuration:"
echo "  Host: $HOST"
echo "  Port: $PORT"
echo ""

run_tests "$HOST" "$PORT"

echo ""
log_success "Script completed successfully! 🎉"
