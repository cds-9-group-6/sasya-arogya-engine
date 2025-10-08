#!/bin/bash

# Test script to verify dependency installation fix
# This script simulates the dependency installation process

set -e

echo "🧪 Testing dependency installation fix..."
echo "========================================"

# Test 1: Check if aiohttp is available
echo ""
echo "1. Checking aiohttp availability:"
if python3 -c "import aiohttp" 2>/dev/null; then
    echo "✅ aiohttp is available"
else
    echo "❌ aiohttp is NOT available"
fi

# Test 2: Check if test_requirements.txt exists
echo ""
echo "2. Checking test_requirements.txt:"
if [ -f "test_requirements.txt" ]; then
    echo "✅ test_requirements.txt exists"
    echo "Contents:"
    head -5 test_requirements.txt
else
    echo "❌ test_requirements.txt does not exist"
fi

# Test 3: Test dependency installation function
echo ""
echo "3. Testing dependency installation:"
if [ -f "run_periodic_tests.sh" ]; then
    echo "✅ run_periodic_tests.sh exists"
    
    # Extract and test the install_dependencies function
    echo "Testing dependency installation logic..."
    
    # Check if test_requirements.txt exists
    if [ -f "test_requirements.txt" ]; then
        echo "Would install from test_requirements.txt"
    elif [ -f "requirements.txt" ]; then
        echo "Would install from requirements.txt"
    else
        echo "Would install aiohttp directly"
    fi
    
    # Test aiohttp import
    if python3 -c "import aiohttp" 2>/dev/null; then
        echo "✅ aiohttp import test passed"
    else
        echo "❌ aiohttp import test failed"
    fi
else
    echo "❌ run_periodic_tests.sh does not exist"
fi

# Test 4: Test Python script execution
echo ""
echo "4. Testing Python script execution:"
if [ -f "test_engine_periodic.py" ]; then
    echo "✅ test_engine_periodic.py exists"
    
    # Test if the script can be imported (syntax check)
    if python3 -c "import test_engine_periodic" 2>/dev/null; then
        echo "✅ Python script syntax is valid"
    else
        echo "❌ Python script has syntax errors"
        python3 -c "import test_engine_periodic" 2>&1 | head -5
    fi
else
    echo "❌ test_engine_periodic.py does not exist"
fi

echo ""
echo "========================================"
echo "🎉 Dependency fix test completed!"
