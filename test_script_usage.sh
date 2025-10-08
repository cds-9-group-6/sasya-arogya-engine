#!/bin/bash

# Test script to demonstrate the usage of run_periodic_tests.sh
# This script shows different ways to call the periodic test runner

echo "🧪 Testing run_periodic_tests.sh with different parameters"
echo "========================================================="

# Test 1: Show help
echo ""
echo "1. Testing help option:"
echo "----------------------"
./run_periodic_tests.sh --help

echo ""
echo "2. Testing with default parameters:"
echo "----------------------------------"
echo "Command: ./run_periodic_tests.sh"
echo "This will use default ENGINE_URL from environment or http://localhost:8080"

echo ""
echo "3. Testing with custom engine URL:"
echo "---------------------------------"
echo "Command: ./run_periodic_tests.sh http://sasya-engine-service:8080"
echo "This will use the provided engine URL"

echo ""
echo "4. Testing with custom max tests:"
echo "--------------------------------"
echo "Command: ./run_periodic_tests.sh -t 5 http://localhost:8080"
echo "This will run maximum 5 tests per category"

echo ""
echo "5. Testing with custom python path:"
echo "----------------------------------"
echo "Command: ./run_periodic_tests.sh -p python3.11 http://engine:8080"
echo "This will use python3.11 instead of default python3"

echo ""
echo "6. Testing with all options:"
echo "---------------------------"
echo "Command: ./run_periodic_tests.sh --max-tests 2 --python python3.11 http://sasya-engine-service:8080"
echo "This will use all custom parameters"

echo ""
echo "7. Testing invalid option:"
echo "-------------------------"
echo "Command: ./run_periodic_tests.sh --invalid-option"
echo "This should show help and exit with error"

echo ""
echo "========================================================="
echo "✅ Usage examples completed!"
echo "Note: These are just examples. The actual test execution requires a running engine."
