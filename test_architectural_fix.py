#!/usr/bin/env python3
"""
Quick test to validate the architectural fix for error state persistence
Tests that completed_node ignores persistent error_message and focuses on current evidence
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fsm_agent.core.workflow_state import WorkflowState, set_error
from fsm_agent.core.nodes.completed_node import CompletedNode
from unittest.mock import Mock

def test_architectural_fix():
    """Test the architectural fix - insurance success with persistent error should show success"""
    
    # Setup
    mock_llm = Mock()
    mock_tools = {}
    completed_node = CompletedNode(tools=mock_tools, llm=mock_llm)
    
    # Create state with your exact scenario
    state = WorkflowState()
    
    # Simulate first operation failing (this sets persistent error)
    set_error(state, "Sasya Arogya MCP server not available")
    
    # Simulate second operation succeeding (sets insurance data)
    state["insurance_premium_details"] = {
        "total_premium": 10981.60,
        "farmer_contribution": 1098.16,
        "crop": "Potato"
    }
    
    context = {"state": state}
    
    # Test the fix
    error_info = completed_node._check_service_errors("insurance", context)
    
    if error_info is None:
        print("✅ SUCCESS: No error detected - insurance operation succeeded!")
        
        # Test that success message would be generated
        title, message = completed_node._get_single_service_summary("insurance", context)
        print(f"✅ Title: {title}")
        print(f"✅ Message: {message}")
        
        if "ERROR" not in title:
            print("🎉 ARCHITECTURAL FIX WORKS: Success message shown despite persistent error_message in state")
            return True
        else:
            print("❌ ISSUE: Still showing error in title")
            return False
    else:
        title, message = error_info
        print(f"❌ FAILED: Still detecting error despite successful operation")
        print(f"   Title: {title}")
        print(f"   Message: {message}")
        return False

if __name__ == "__main__":
    success = test_architectural_fix()
    
    if success:
        print("\n🚀 The architectural fix successfully resolved the error state persistence issue!")
        print("   - Persistent error_message is ignored")
        print("   - Only current operation evidence matters")
        print("   - Success shows success, regardless of previous failures")
    else:
        print("\n❌ The fix needs more work")
    
    exit(0 if success else 1)
