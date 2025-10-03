#!/usr/bin/env python3
"""
Test suite for error state persistence fix

This test validates that error state is properly cleared when operations succeed,
preventing false error messages in completed node.

Run with: python3 test_error_state_clearing.py
"""

import unittest
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fsm_agent.core.workflow_state import WorkflowState, set_error, clear_error


class TestErrorStateClearing(unittest.TestCase):
    """Test suite for error state clearing functionality"""
    
    def test_set_error_adds_error_state(self):
        """Test that set_error properly sets error state"""
        state = WorkflowState()
        error_message = "Test error message"
        
        set_error(state, error_message)
        
        self.assertEqual(state["error_message"], error_message)
        self.assertEqual(state["retry_count"], 1)
        self.assertIn("messages", state)
        
        # Check that system message was added
        last_message = state["messages"][-1]
        self.assertEqual(last_message["role"], "system")
        self.assertIn(error_message, last_message["content"])
    
    def test_clear_error_removes_error_state(self):
        """Test that clear_error properly removes error state"""
        state = WorkflowState()
        
        # Set error state first
        set_error(state, "Test error")
        self.assertIn("error_message", state)
        self.assertIn("retry_count", state)
        
        # Clear error state
        clear_error(state)
        
        self.assertNotIn("error_message", state)
        self.assertNotIn("retry_count", state)
    
    def test_clear_error_on_empty_state(self):
        """Test that clear_error works safely on state without errors"""
        state = WorkflowState()
        
        # Should not raise exception
        clear_error(state)
        
        self.assertNotIn("error_message", state)
        self.assertNotIn("retry_count", state)
    
    def test_error_state_persistence_scenario(self):
        """Test the specific scenario from user's bug report"""
        state = WorkflowState()
        
        # Simulate first operation failing
        set_error(state, "Sasya Arogya MCP server not available")
        self.assertEqual(state["error_message"], "Sasya Arogya MCP server not available")
        
        # Simulate second operation succeeding (should clear error)
        # This is what insurance node would do on success
        clear_error(state)
        
        # Verify error state is cleared
        self.assertNotIn("error_message", state)
        self.assertNotIn("retry_count", state)
        
        # This is what completed node checks - should find no error
        error_exists = state.get("error_message") is not None
        self.assertFalse(error_exists, "Error state should be cleared after successful operation")
    
    def test_multiple_error_cycles(self):
        """Test multiple error/success cycles"""
        state = WorkflowState()
        
        # First error
        set_error(state, "First error")
        self.assertEqual(state["retry_count"], 1)
        
        # Success clears error
        clear_error(state)
        self.assertNotIn("error_message", state)
        self.assertNotIn("retry_count", state)
        
        # Second error (should start fresh)
        set_error(state, "Second error")  
        self.assertEqual(state["error_message"], "Second error")
        self.assertEqual(state["retry_count"], 1)  # Fresh count
        
        # Another error (retry count increments)
        set_error(state, "Third error")
        self.assertEqual(state["retry_count"], 2)
        
        # Success clears everything
        clear_error(state)
        self.assertNotIn("error_message", state)
        self.assertNotIn("retry_count", state)


class TestCompletedNodeErrorDetection(unittest.TestCase):
    """Test that completed node error detection works correctly with cleared errors"""
    
    def setUp(self):
        """Set up test fixtures"""
        from fsm_agent.core.nodes.completed_node import CompletedNode
        from unittest.mock import Mock
        
        self.mock_llm = Mock()
        self.mock_tools = {}
        self.completed_node = CompletedNode(tools=self.mock_tools, llm=self.mock_llm)
    
    def test_no_error_when_state_cleared(self):
        """Test that completed node finds no error when error state is cleared"""
        state = WorkflowState()
        
        # Simulate the user's scenario
        set_error(state, "Sasya Arogya MCP server not available")
        clear_error(state)  # This is what insurance node now does on success
        
        # Add some insurance data to simulate successful operation
        state["insurance_premium_details"] = {"premium": 3978.67}
        
        context = {"state": state}
        
        # Check if completed node detects errors
        error_info = self.completed_node._check_service_errors("insurance", context)
        
        self.assertIsNone(error_info, "Should find no errors when error state is cleared and operation succeeded")
    
    def test_error_detected_when_state_not_cleared(self):
        """Test that completed node still detects errors when error state is not cleared"""
        state = WorkflowState()
        
        # Simulate error without clearing
        set_error(state, "Sasya Arogya MCP server not available")
        # Don't call clear_error() - simulating old buggy behavior
        
        context = {"state": state}
        
        # Check if completed node detects errors
        error_info = self.completed_node._check_service_errors("insurance", context)
        
        self.assertIsNotNone(error_info, "Should detect error when error state is not cleared")
        title, message = error_info
        self.assertIn("⚠️", title)
        self.assertIn("Sasya Arogya MCP server not available", message)


if __name__ == "__main__":
    # Run the tests
    unittest.main(verbosity=2)
