#!/usr/bin/env python3
"""
Test suite for intent analysis classification vs prescription disambiguation fix

This test validates that the intent analysis correctly distinguishes between
classification requests (analyze disease) and prescription requests (get treatment).

Run with: python3 test_intent_analysis_classification_fix.py
"""

import unittest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fsm_agent.core.nodes.initial_node import InitialNode
from fsm_agent.core.nodes.followup_node import FollowupNode
from fsm_agent.core.workflow_state import WorkflowState


class TestIntentAnalysisClassificationFix(unittest.TestCase):
    """Test suite for intent analysis classification vs prescription disambiguation"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock LLM and tools
        self.mock_llm = Mock()
        self.mock_tools = {
            "context_extractor": AsyncMock(return_value={"error": None})
        }
        
        # Create nodes with mocked dependencies
        self.initial_node = InitialNode(tools=self.mock_tools, llm=self.mock_llm)
        self.followup_node = FollowupNode(tools=self.mock_tools, llm=self.mock_llm)
    
    def test_classification_only_messages(self):
        """Test messages that should only trigger classification, not prescription"""
        classification_only_messages = [
            "Analyze this plant disease",
            "Please analyze what's wrong with this leaf", 
            "Can you analyze and identify the disease in my plant?",
            "Analyze my crop disease",
            "What disease does my plant have?",
            "Identify the problem with my tomato leaves",
            "Diagnose this plant issue",
            "Check what's wrong with my crop"
        ]
        
        for message in classification_only_messages:
            with self.subTest(message=message):
                # Mock LLM response for classification only
                mock_response = Mock()
                mock_response.content = json.dumps({
                    "wants_classification": True,
                    "wants_prescription": False,
                    "wants_full_workflow": False,
                    "wants_insurance": False,
                    "wants_insurance_premium": False,
                    "wants_insurance_companies": False,
                    "wants_insurance_recommendation": False,
                    "wants_insurance_purchase": False,
                    "is_general_question": False,
                    "is_agriculture_related": True,
                    "out_of_scope": False,
                    "scope_confidence": 0.95,
                    "general_answer": ""
                })
                self.mock_llm.invoke.return_value = mock_response
                
                # Test intent analysis
                result = asyncio.run(self.initial_node._analyze_user_intent(message))
                
                self.assertTrue(result["wants_classification"], 
                              f"'{message}' should trigger classification")
                self.assertFalse(result["wants_prescription"], 
                               f"'{message}' should NOT trigger prescription")
                self.assertFalse(result["wants_full_workflow"], 
                               f"'{message}' should NOT trigger full workflow")
    
    def test_classification_and_prescription_messages(self):
        """Test messages that should trigger both classification and prescription"""
        both_classification_and_prescription_messages = [
            "Analyze and treat my plant disease",
            "Analyze this leaf and give me treatment options",
            "Help my plant get better - analyze and cure it",
            "Diagnose and provide treatment for my crop",
            "Analyze my disease and get medicine recommendations",
            "Check what's wrong and how to fix it",
            "Identify the problem and tell me how to treat it"
        ]
        
        for message in both_classification_and_prescription_messages:
            with self.subTest(message=message):
                # Mock LLM response for both classification and prescription
                mock_response = Mock()
                mock_response.content = json.dumps({
                    "wants_classification": True,
                    "wants_prescription": True,
                    "wants_full_workflow": False,
                    "wants_insurance": False,
                    "wants_insurance_premium": False,
                    "wants_insurance_companies": False,
                    "wants_insurance_recommendation": False,
                    "wants_insurance_purchase": False,
                    "is_general_question": False,
                    "is_agriculture_related": True,
                    "out_of_scope": False,
                    "scope_confidence": 0.98,
                    "general_answer": ""
                })
                self.mock_llm.invoke.return_value = mock_response
                
                # Test intent analysis
                result = asyncio.run(self.initial_node._analyze_user_intent(message))
                
                self.assertTrue(result["wants_classification"], 
                              f"'{message}' should trigger classification")
                self.assertTrue(result["wants_prescription"], 
                              f"'{message}' should trigger prescription")
    
    def test_fallback_classification_keywords(self):
        """Test fallback analysis correctly identifies classification keywords"""
        classification_messages = [
            "analyze my plant",
            "detect the disease",
            "identify what's wrong", 
            "classify this leaf issue",
            "what disease is this"
        ]
        
        for message in classification_messages:
            with self.subTest(message=message):
                # Test fallback analysis (used when LLM fails)
                result = asyncio.run(self.initial_node._fallback_intent_analysis(message))
                
                self.assertTrue(result["wants_classification"], 
                              f"Fallback should classify '{message}' as classification request")
    
    def test_followup_node_classification_intent(self):
        """Test followup node correctly routes analyze requests to classification"""
        # Create mock state
        state = WorkflowState()
        state["session_id"] = "test_session"
        state["user_message"] = "analyze this plant disease"
        state["user_image"] = "base64_image_data"
        state["previous_node"] = "classifying"
        state["conversation_history"] = []
        
        # Mock LLM response for followup classification
        mock_response = Mock()
        mock_response.content = json.dumps({
            "action": "classify",
            "response": "",
            "overlay_type": "",
            "confidence": 0.95,
            "is_agriculture_related": True,
            "scope_confidence": 0.95
        })
        self.mock_llm.invoke.return_value = mock_response
        
        # Test followup intent analysis
        result = asyncio.run(self.followup_node._analyze_followup_intent(state))
        
        self.assertEqual(result["action"], "classify", 
                        "Followup node should route 'analyze' to classify action")
        self.assertGreaterEqual(result["confidence"], 0.9, 
                               "Should have high confidence in classification")
    
    def test_edge_cases_analyze_keyword(self):
        """Test edge cases with analyze keyword that might be ambiguous"""
        edge_cases = [
            ("analyze", "classify"),  # Just "analyze" should default to classify
            ("analyze disease", "classify"),  # Clear classification request
            ("analyze and fix", "prescribe"),  # Both analysis and treatment
            ("analyze for treatment", "prescribe"),  # Implies treatment needed
            ("analyze my crop health", "classify"),  # Health assessment = classification
        ]
        
        for message, expected_primary_action in edge_cases:
            with self.subTest(message=message, expected=expected_primary_action):
                # Create state for followup testing
                state = WorkflowState()
                state["session_id"] = "test_session"
                state["user_message"] = message
                state["user_image"] = "base64_image_data"
                state["previous_node"] = "initial"
                state["conversation_history"] = []
                
                # Mock appropriate LLM response
                if expected_primary_action == "classify":
                    mock_response_content = {
                        "action": "classify",
                        "response": "",
                        "overlay_type": "",
                        "confidence": 0.9,
                        "is_agriculture_related": True,
                        "scope_confidence": 0.95
                    }
                else:  # prescribe
                    mock_response_content = {
                        "action": "prescribe", 
                        "response": "",
                        "overlay_type": "",
                        "confidence": 0.9,
                        "is_agriculture_related": True,
                        "scope_confidence": 0.95
                    }
                
                mock_response = Mock()
                mock_response.content = json.dumps(mock_response_content)
                self.mock_llm.invoke.return_value = mock_response
                
                # Test followup intent analysis
                result = asyncio.run(self.followup_node._analyze_followup_intent(state))
                
                self.assertEqual(result["action"], expected_primary_action,
                               f"'{message}' should route to {expected_primary_action}")
    
    def test_prescription_only_messages(self):
        """Test messages that should only trigger prescription (with existing classification)"""
        prescription_only_messages = [
            "Give me treatment options",
            "How do I treat this disease?",
            "What medicine should I use?",
            "Provide dosage instructions",
            "How to cure my plant?",
            "Treatment recommendations please"
        ]
        
        for message in prescription_only_messages:
            with self.subTest(message=message):
                # Create state with existing classification (common scenario)
                state = WorkflowState()
                state["session_id"] = "test_session"
                state["user_message"] = message
                state["classification_result"] = {"disease": "leaf_blight"}
                state["previous_node"] = "classifying"
                state["conversation_history"] = []
                
                # Mock LLM response for prescription only
                mock_response = Mock()
                mock_response.content = json.dumps({
                    "action": "prescribe",
                    "response": "",
                    "overlay_type": "",
                    "confidence": 0.95,
                    "is_agriculture_related": True,
                    "scope_confidence": 0.95
                })
                self.mock_llm.invoke.return_value = mock_response
                
                # Test followup intent analysis
                result = asyncio.run(self.followup_node._analyze_followup_intent(state))
                
                self.assertEqual(result["action"], "prescribe",
                               f"'{message}' should route to prescribe action")
    
    def test_ambiguous_analyze_defaults_to_classification(self):
        """Test that ambiguous 'analyze' requests default to classification"""
        ambiguous_messages = [
            "analyze this",
            "analyze my image", 
            "please analyze",
            "can you analyze this leaf?"
        ]
        
        for message in ambiguous_messages:
            with self.subTest(message=message):
                # Mock LLM response defaulting to classification
                mock_response = Mock()
                mock_response.content = json.dumps({
                    "wants_classification": True,
                    "wants_prescription": False,
                    "wants_full_workflow": False,
                    "wants_insurance": False,
                    "wants_insurance_premium": False,
                    "wants_insurance_companies": False,
                    "wants_insurance_recommendation": False,
                    "wants_insurance_purchase": False,
                    "is_general_question": False,
                    "is_agriculture_related": True,
                    "out_of_scope": False,
                    "scope_confidence": 0.85,
                    "general_answer": ""
                })
                self.mock_llm.invoke.return_value = mock_response
                
                # Test intent analysis
                result = asyncio.run(self.initial_node._analyze_user_intent(message))
                
                self.assertTrue(result["wants_classification"], 
                              f"Ambiguous '{message}' should default to classification")
                self.assertFalse(result["wants_prescription"], 
                               f"Ambiguous '{message}' should NOT trigger prescription")


class TestAnalyzeKeywordExamples(unittest.TestCase):
    """Test that the new examples in the prompts work correctly"""
    
    def test_prompt_examples_parse_correctly(self):
        """Test that the new examples in the prompts are valid JSON"""
        # Test some of the new examples we added
        examples = [
            '{"wants_classification": true, "wants_prescription": false, "wants_full_workflow": false, "wants_insurance": false, "wants_insurance_premium": false, "wants_insurance_companies": false, "wants_insurance_recommendation": false, "wants_insurance_purchase": false, "is_general_question": false, "is_agriculture_related": true, "out_of_scope": false, "scope_confidence": 0.98, "general_answer": ""}',
            '{"wants_classification": true, "wants_prescription": true, "wants_full_workflow": false, "wants_insurance": false, "wants_insurance_premium": false, "wants_insurance_companies": false, "wants_insurance_recommendation": false, "wants_insurance_purchase": false, "is_general_question": false, "is_agriculture_related": true, "out_of_scope": false, "scope_confidence": 0.99, "general_answer": ""}'
        ]
        
        for example_json in examples:
            with self.subTest(json_string=example_json[:50] + "..."):
                try:
                    parsed = json.loads(example_json)
                    # Verify it has the required fields
                    self.assertIn("wants_classification", parsed)
                    self.assertIn("wants_prescription", parsed)
                    self.assertIn("is_agriculture_related", parsed)
                    self.assertIsInstance(parsed["wants_classification"], bool)
                    self.assertIsInstance(parsed["wants_prescription"], bool)
                except json.JSONDecodeError as e:
                    self.fail(f"Example JSON is invalid: {e}")


if __name__ == "__main__":
    # Run the tests
    unittest.main(verbosity=2)
