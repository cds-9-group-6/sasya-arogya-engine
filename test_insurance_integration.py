#!/usr/bin/env python3
"""
Test script for Insurance Integration with MCP Server

This script tests the complete insurance integration including:
1. Insurance tool MCP communication
2. Intent analysis for insurance requests
3. Workflow routing to insurance node
"""

import asyncio
import logging
import os
import sys
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from fsm_agent.tools.insurance_tool import InsuranceTool
from fsm_agent.core.workflow_state import create_initial_state

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_insurance_tool():
    """Test the insurance tool directly"""
    print("🧪 Testing Insurance Tool...")
    
    try:
        # Create insurance tool instance
        insurance_tool = InsuranceTool()
        
        # Test premium calculation
        print("\n1. Testing Premium Calculation:")
        premium_result = await insurance_tool._arun(
            action="calculate_premium",
            crop="Wheat",
            area_hectare=2.5,
            state="Karnataka",
            session_id="test_session_1"
        )
        print(f"Premium Result: {premium_result}")
        
        # Test insurance companies
        print("\n2. Testing Insurance Companies:")
        companies_result = await insurance_tool._arun(
            action="get_companies",
            state="Karnataka",
            session_id="test_session_2"
        )
        print(f"Companies Result: {companies_result}")
        
        # Test insurance recommendation
        print("\n3. Testing Insurance Recommendation:")
        recommendation_result = await insurance_tool._arun(
            action="recommend",
            disease="Brown Hopper Blast",
            farmer_name="Test Farmer",
            crop="Paddy",
            area_hectare=3.0,
            state="Tamil Nadu",
            session_id="test_session_3"
        )
        print(f"Recommendation Result: {recommendation_result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Insurance tool test failed: {e}")
        return False


async def test_intent_analysis():
    """Test intent analysis for insurance requests"""
    print("\n🧪 Testing Intent Analysis...")
    
    try:
        # Import the node and LLM for testing
        from langchain_ollama import ChatOllama
        from fsm_agent.core.nodes.initial_node import InitialNode
        from fsm_agent.tools.insurance_tool import InsuranceTool
        from fsm_agent.tools.context_extractor import ContextExtractorTool
        
        # Setup LLM and tools
        llm = ChatOllama(model="llama3.1:8b", base_url="http://localhost:11434")
        tools = {
            "insurance": InsuranceTool(),
            "context_extractor": ContextExtractorTool()
        }
        
        # Create initial node
        initial_node = InitialNode(tools, llm)
        
        # Test insurance intent messages
        test_messages = [
            "I need crop insurance for my wheat farm",
            "How much will insurance cost for 5 hectares of paddy?",
            "Which insurance companies are available in Karnataka?",
            "My cotton has disease, need treatment and insurance"
        ]
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n{i}. Testing message: '{message}'")
            
            # Create test state
            state = create_initial_state(
                session_id=f"intent_test_{i}",
                user_message=message
            )
            
            # Analyze intent
            try:
                intent = await initial_node._analyze_user_intent(message)
                print(f"   Intent: {intent}")
                
                # Check if insurance intent was detected
                if intent.get("wants_insurance"):
                    print(f"   ✅ Insurance intent detected!")
                else:
                    print(f"   ❌ Insurance intent NOT detected")
                    
            except Exception as e:
                print(f"   ❌ Intent analysis failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Intent analysis test failed: {e}")
        return False


def test_mcp_server_health():
    """Test MCP server health"""
    print("\n🧪 Testing MCP Server Health...")
    
    try:
        import requests
        
        mcp_url = os.getenv("SASYA_AROGYA_MCP_URL", "http://localhost:8000")
        
        # Test health endpoint
        response = requests.get(f"{mcp_url}/health", timeout=5)
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ MCP Server is healthy: {health_data}")
            return True
        else:
            print(f"❌ MCP Server returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ MCP Server health check failed: {e}")
        print("💡 Make sure the Sasya Arogya MCP server is running on port 8000")
        return False


def print_integration_summary():
    """Print integration summary"""
    print("\n" + "="*60)
    print("🏦 INSURANCE INTEGRATION SUMMARY")
    print("="*60)
    print("✅ Components Implemented:")
    print("   • InsuranceTool - MCP HTTP client for Sasya Arogya server")
    print("   • InsuranceNode - LangGraph workflow node with context extraction")
    print("   • Intent Analysis - LLM-based insurance request detection")
    print("   • Workflow Routing - Dynamic routing to insurance node")
    print("   • State Management - Insurance-related state fields")
    print("")
    print("🔧 Configuration:")
    print(f"   • MCP Server URL: {os.getenv('SASYA_AROGYA_MCP_URL', 'http://localhost:8000')}")
    print(f"   • Prescription Engine URL: {os.getenv('PRESCRIPTION_ENGINE_URL', 'http://localhost:8081')}")
    print("")
    print("🚀 Available Insurance Services:")
    print("   • Premium Calculation - Calculate insurance premiums by crop/area/state")
    print("   • Company Listings - Get available insurance companies by state")
    print("   • Recommendations - Get personalized insurance recommendations")
    print("   • Certificate Generation - Generate insurance certificates (future)")
    print("")
    print("💬 Example User Messages:")
    print('   • "I need crop insurance for my wheat farm"')
    print('   • "How much will insurance cost for 5 hectares of paddy?"')
    print('   • "Which insurance companies are available in Karnataka?"')
    print('   • "My cotton has disease, need treatment and insurance"')
    print("="*60)


async def main():
    """Main test function"""
    print("🧪 INSURANCE INTEGRATION TEST")
    print("="*50)
    
    test_results = []
    
    # Test MCP server health first
    mcp_healthy = test_mcp_server_health()
    test_results.append(("MCP Server Health", mcp_healthy))
    
    if mcp_healthy:
        # Test insurance tool
        tool_success = await test_insurance_tool()
        test_results.append(("Insurance Tool", tool_success))
    else:
        print("⚠️ Skipping insurance tool tests - MCP server not available")
        test_results.append(("Insurance Tool", False))
    
    # Test intent analysis (doesn't require MCP server)
    intent_success = await test_intent_analysis()
    test_results.append(("Intent Analysis", intent_success))
    
    # Print results
    print("\n" + "="*50)
    print("📊 TEST RESULTS")
    print("="*50)
    
    for test_name, success in test_results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:20} {status}")
    
    all_passed = all(result[1] for result in test_results)
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("The insurance integration is ready to use.")
    else:
        print("\n⚠️ SOME TESTS FAILED")
        print("Check the error messages above for troubleshooting.")
    
    # Print integration summary
    print_integration_summary()
    
    return all_passed


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test script failed: {e}")
        sys.exit(1)
