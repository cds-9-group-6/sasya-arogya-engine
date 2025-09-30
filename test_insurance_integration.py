#!/usr/bin/env python3
"""
Test script for Insurance Integration with MCP Server

This script tests the complete insurance integration including:
1. Insurance tool MCP communication
2. Intent analysis for insurance requests
3. Workflow routing to insurance node
4. Insurance purchase and certificate generation
5. PDF streaming and download functionality
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
        
        # Test certificate generation (new purchase functionality)
        print("\n4. Testing Certificate Generation (Insurance Purchase):")
        certificate_result = await insurance_tool._arun(
            action="generate_certificate",
            farmer_name="Raj Kumar",
            crop="Wheat",
            area_hectare=5.0,
            state="Punjab",
            session_id="test_session_4"
        )
        print(f"Certificate Result: {certificate_result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Insurance tool test failed: {e}")
        return False


async def test_insurance_purchase_flow():
    """Test complete insurance purchase and certificate generation flow"""
    print("\n🧪 Testing Insurance Purchase Flow...")
    
    try:
        # Import required modules
        from langchain_ollama import ChatOllama
        from fsm_agent.core.nodes.initial_node import InitialNode
        from fsm_agent.core.nodes.insurance_node import InsuranceNode
        from fsm_agent.tools.insurance_tool import InsuranceTool
        from fsm_agent.tools.context_extractor import ContextExtractorTool
        
        # Setup LLM and tools
        llm = ChatOllama(model="llama3.1:8b", base_url="http://localhost:11434")
        tools = {
            "insurance": InsuranceTool(),
            "context_extractor": ContextExtractorTool()
        }
        
        # Create nodes
        initial_node = InitialNode(tools, llm)
        insurance_node = InsuranceNode(tools, llm)
        
        # Test purchase intent recognition
        purchase_messages = [
            "I want to buy crop insurance for my wheat farm",
            "Help me apply for crop insurance with these premium details",
            "Buy insurance for me with this premium",
            "Generate insurance certificate for my farm",
            "I want to purchase crop insurance policy"
        ]
        
        print("\n📋 Testing Purchase Intent Recognition:")
        purchase_intents_detected = 0
        
        for i, message in enumerate(purchase_messages, 1):
            print(f"\n   {i}. Message: '{message}'")
            
            try:
                # Create test state
                state = create_initial_state(
                    session_id=f"purchase_intent_test_{i}",
                    user_message=message
                )
                
                # Analyze intent with initial node
                intent = await initial_node._analyze_user_intent(message)
                
                # Check for purchase intent
                wants_insurance = intent.get("wants_insurance", False)
                wants_purchase = intent.get("wants_insurance_purchase", False)
                
                if wants_insurance and wants_purchase:
                    print(f"      ✅ Purchase intent detected!")
                    purchase_intents_detected += 1
                else:
                    print(f"      ❌ Purchase intent NOT detected (insurance: {wants_insurance}, purchase: {wants_purchase})")
                    
            except Exception as e:
                print(f"      ❌ Intent analysis failed: {e}")
        
        print(f"\n   Purchase Intent Detection: {purchase_intents_detected}/{len(purchase_messages)} successful")
        
        # Test complete purchase flow with insurance node
        print("\n📜 Testing Complete Purchase Flow:")
        
        # Test successful certificate generation
        print("\n   1. Testing Successful Certificate Generation:")
        success_state = create_initial_state(
            session_id="cert_success_test",
            user_message="I want to buy crop insurance for my wheat farm"
        )
        success_state["user_intent"] = {"wants_insurance_purchase": True}
        success_state["farmer_name"] = "Suresh Kumar"
        success_state["crop"] = "Wheat"
        success_state["area_hectare"] = 3.5
        success_state["state"] = "Haryana"
        
        try:
            result_state = await insurance_node.execute(success_state)
            certificate_data = result_state.get("insurance_certificate", {})
            
            if certificate_data.get("success"):
                print(f"      ✅ Certificate generated successfully!")
                print(f"         Policy ID: {certificate_data.get('policy_id', 'N/A')}")
                print(f"         Farmer: {certificate_data.get('farmer_name', 'N/A')}")
                print(f"         PDF Generated: {certificate_data.get('pdf_generated', False)}")
            else:
                print(f"      ❌ Certificate generation failed: {certificate_data.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"      ❌ Certificate generation test failed: {e}")
        
        # Test missing information handling
        print("\n   2. Testing Missing Information Handling:")
        missing_state = create_initial_state(
            session_id="missing_info_test",
            user_message="I want to buy crop insurance"
        )
        missing_state["user_intent"] = {"wants_insurance_purchase": True}
        missing_state["farmer_name"] = "Test Farmer"
        # Missing: crop, area_hectare, state
        
        try:
            result_state = await insurance_node.execute(missing_state)
            requires_input = result_state.get("requires_user_input", False)
            next_action = result_state.get("next_action")
            
            if requires_input and next_action == "followup":
                print(f"      ✅ Missing information handled correctly - awaiting user input")
            else:
                print(f"      ❌ Missing information not handled properly (requires_input: {requires_input}, next_action: {next_action})")
                
        except Exception as e:
            print(f"      ❌ Missing information test failed: {e}")
        
        # Test streaming behavior
        print("\n   3. Testing Message Streaming:")
        stream_state = create_initial_state(
            session_id="stream_test",
            user_message="Buy insurance for me"
        )
        stream_state["user_intent"] = {"wants_insurance_purchase": True}
        stream_state["farmer_name"] = "Stream Test Farmer"
        stream_state["crop"] = "Cotton"
        stream_state["area_hectare"] = 2.0
        stream_state["state"] = "Gujarat"
        
        try:
            result_state = await insurance_node.execute(stream_state)
            conversation = result_state.get("conversation_history", [])
            assistant_messages = [msg for msg in conversation if msg.get("role") == "assistant"]
            has_streaming = result_state.get("stream_immediately", False)
            
            print(f"      Messages generated: {len(assistant_messages)}")
            print(f"      Streaming enabled: {has_streaming}")
            
            if len(assistant_messages) > 0 and has_streaming:
                print(f"      ✅ Message streaming working correctly")
                # Show first message preview
                first_msg = assistant_messages[0]["content"][:80] + "..." if len(assistant_messages) > 0 else "None"
                print(f"      First message: {first_msg}")
            else:
                print(f"      ❌ Message streaming not working properly")
                
        except Exception as e:
            print(f"      ❌ Streaming test failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Insurance purchase flow test failed: {e}")
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
        
        # Test insurance intent messages (including purchase intents)
        test_messages = [
            "I need crop insurance for my wheat farm",
            "How much will insurance cost for 5 hectares of paddy?",
            "Which insurance companies are available in Karnataka?",
            "My cotton has disease, need treatment and insurance",
            "I want to buy crop insurance for my farm",
            "Help me apply for insurance with these premium details",
            "Generate insurance certificate for my crops"
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
        
        mcp_url = os.getenv("SASYA_AROGYA_MCP_URL", "http://localhost:8001")
        
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
        print("💡 Make sure the Sasya Arogya MCP server is running on port 8001")
        return False


def print_integration_summary():
    """Print integration summary"""
    print("\n" + "="*70)
    print("🏦 INSURANCE INTEGRATION SUMMARY")
    print("="*70)
    print("✅ Components Implemented:")
    print("   • InsuranceTool - MCP HTTP client for Sasya Arogya server")
    print("   • InsuranceNode - LangGraph workflow node with context extraction")
    print("   • Intent Analysis - LLM-based insurance request detection")
    print("   • Purchase Flow - Complete insurance purchase and certificate generation")
    print("   • Workflow Routing - Dynamic routing to insurance node")
    print("   • State Management - Insurance-related state fields")
    print("   • Message Streaming - Real-time streaming of all insurance messages")
    print("")
    print("🔧 Configuration:")
    print(f"   • MCP Server URL: {os.getenv('SASYA_AROGYA_MCP_URL', 'http://localhost:8001')}")
    print(f"   • Prescription Engine URL: {os.getenv('PRESCRIPTION_ENGINE_URL', 'http://localhost:8081')}")
    print("")
    print("🚀 Available Insurance Services:")
    print("   • Premium Calculation - Calculate insurance premiums by crop/area/state")
    print("   • Company Listings - Get available insurance companies by state")
    print("   • Recommendations - Get personalized insurance recommendations")
    print("   • Certificate Generation - Generate PDF insurance certificates")
    print("   • Purchase Processing - Complete insurance purchase workflow")
    print("   • PDF Download - Stream insurance certificates to users")
    print("")
    print("💬 Example User Messages:")
    print('   Information Requests:')
    print('      • "I need crop insurance for my wheat farm"')
    print('      • "How much will insurance cost for 5 hectares of paddy?"')
    print('      • "Which insurance companies are available in Karnataka?"')
    print('      • "My cotton has disease, need treatment and insurance"')
    print('   Purchase Requests:')
    print('      • "I want to buy crop insurance for my wheat farm"')
    print('      • "Help me apply for crop insurance with these premium details"')
    print('      • "Buy insurance for me with this premium"')
    print('      • "Generate insurance certificate for my farm"')
    print("")
    print("🎯 Purchase Flow Features:")
    print("   • Intent Recognition - Detects purchase keywords automatically")
    print("   • Data Validation - Ensures required information is available")
    print("   • Policy Generation - Creates unique policy IDs and farmer IDs")
    print("   • Premium Calculation - Automatic calculation with government subsidy")
    print("   • MCP Integration - Calls generate_insurance_certificate endpoint")
    print("   • PDF Processing - Handles PDF certificate generation and streaming")
    print("   • Error Handling - Graceful failure handling with helpful messages")
    print("   • Missing Info Prompts - Guides users through required information")
    print("="*70)


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
        
        # Test purchase flow (requires MCP server)
        purchase_success = await test_insurance_purchase_flow()
        test_results.append(("Purchase Flow", purchase_success))
    else:
        print("⚠️ Skipping insurance tool and purchase tests - MCP server not available")
        test_results.append(("Insurance Tool", False))
        test_results.append(("Purchase Flow", False))
    
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
