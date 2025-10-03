#!/usr/bin/env python3
"""
Test file for LLM-driven contextual next steps functionality.
Tests the new intelligent next steps generation in completed_node.py
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fsm_agent.core.nodes.completed_node import CompletedNode
from fsm_agent.core.workflow_state import WorkflowState


class TestLLMContextualNextSteps(unittest.TestCase):
    """Test suite for LLM-driven contextual next steps functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock LLM
        self.mock_llm = Mock()
        
        # Create completed node instance with mocked LLM
        self.completed_node = CompletedNode()
        self.completed_node.llm = self.mock_llm
        
        # Base state template
        self.base_state = {
            "session_id": "test-session",
            "current_node": "completed",
            "messages": []
        }
    
    def create_state(self, **kwargs):
        """Helper to create workflow state with custom properties"""
        state = self.base_state.copy()
        state.update(kwargs)
        return state
    
    def test_new_session_context_building(self):
        """Test context building for new session with no completed operations"""
        state = self.create_state(
            user_message="Hello, I need help with my plants"
        )
        
        context = self.completed_node._build_workflow_context(state)
        
        # Verify context structure
        self.assertIn("completed_operations", context)
        self.assertIn("available_data", context)
        self.assertIn("user_context", context)
        self.assertIn("conversation_summary", context)
        
        # Verify no operations completed
        self.assertFalse(context["completed_operations"]["classification"])
        self.assertFalse(context["completed_operations"]["prescription"])
        self.assertFalse(context["completed_operations"]["insurance"])
        
        # Verify empty available data
        self.assertEqual(len(context["available_data"]), 0)
    
    def test_disease_detected_context_building(self):
        """Test context building when disease is detected"""
        state = self.create_state(
            classification_results={"confidence": 0.87, "disease": "tomato_late_blight"},
            disease_name="tomato_late_blight",
            plant_type="tomato",
            farmer_name="John",
            location="Karnataka",
            messages=[
                {"role": "user", "content": "My tomato plants have dark spots"},
                {"role": "assistant", "content": "Disease detected: tomato_late_blight"}
            ]
        )
        
        context = self.completed_node._build_workflow_context(state)
        
        # Verify classification completed
        self.assertTrue(context["completed_operations"]["classification"])
        self.assertFalse(context["completed_operations"]["prescription"])
        self.assertFalse(context["completed_operations"]["insurance"])
        
        # Verify disease info extracted
        self.assertIn("disease_info", context["available_data"])
        disease_info = context["available_data"]["disease_info"] 
        self.assertEqual(disease_info["disease_name"], "tomato_late_blight")
        self.assertFalse(disease_info["is_healthy"])
        self.assertEqual(disease_info["confidence"], 0.87)
        
        # Verify user context
        self.assertEqual(context["user_context"]["plant_type"], "tomato")
        self.assertEqual(context["user_context"]["farmer_name"], "John")
        self.assertEqual(context["user_context"]["location"], "Karnataka")
    
    def test_full_workflow_context_building(self):
        """Test context building when full workflow is completed"""
        state = self.create_state(
            classification_results={"confidence": 0.92},
            disease_name="wheat_rust",
            prescription_data={"treatments": [{"name": "Fungicide A"}, {"name": "Fungicide B"}]},
            treatment_recommendations=[{"name": "Treatment 1"}, {"name": "Treatment 2"}, {"name": "Treatment 3"}],
            insurance_premium_details={"premium": 5000, "coverage": "full"},
            insurance_recommendations={"recommended": True},
            insurance_companies=[{"name": "Company A"}, {"name": "Company B"}],
            plant_type="wheat",
            farmer_name="Rajesh",
            location="Punjab"
        )
        
        context = self.completed_node._build_workflow_context(state)
        
        # Verify all operations completed
        self.assertTrue(context["completed_operations"]["classification"])
        self.assertTrue(context["completed_operations"]["prescription"]) 
        self.assertTrue(context["completed_operations"]["insurance"])
        
        # Verify treatment info
        self.assertIn("treatment_info", context["available_data"])
        self.assertEqual(context["available_data"]["treatment_info"]["treatment_count"], 3)
        self.assertTrue(context["available_data"]["treatment_info"]["has_treatments"])
        
        # Verify insurance info
        self.assertIn("insurance_info", context["available_data"])
        insurance_info = context["available_data"]["insurance_info"]
        self.assertTrue(insurance_info["has_premium"])
        self.assertTrue(insurance_info["has_recommendations"])
        self.assertTrue(insurance_info["has_companies"])
        self.assertFalse(insurance_info["has_certificate"])  # No certificate in state
    
    def test_healthy_plant_context_building(self):
        """Test context building for healthy plant detection"""
        state = self.create_state(
            classification_results={"confidence": 0.94},
            disease_name="healthy",
            plant_type="rose",
            farmer_name="Priya"
        )
        
        context = self.completed_node._build_workflow_context(state)
        
        # Verify disease info for healthy plant
        disease_info = context["available_data"]["disease_info"]
        self.assertEqual(disease_info["disease_name"], "healthy")
        self.assertTrue(disease_info["is_healthy"])
        self.assertEqual(disease_info["confidence"], 0.94)
    
    def test_prompt_formatting(self):
        """Test prompt formatting for LLM"""
        context = {
            "completed_operations": {"classification": True, "prescription": False, "insurance": False},
            "available_data": {
                "disease_info": {
                    "disease_name": "tomato_late_blight",
                    "is_healthy": False,
                    "confidence": 0.87
                }
            },
            "user_context": {"plant_type": "tomato", "farmer_name": "John", "location": "Karnataka"},
            "conversation_summary": "My tomato plants have dark spots on leaves"
        }
        
        formatted_context = self.completed_node._format_context_for_prompt(context)
        
        # Verify formatted context contains expected information
        self.assertIn("✅ COMPLETED: classification", formatted_context)
        self.assertIn("🌿 PLANT STATUS: diseased (tomato_late_blight) (confidence: 87%)", formatted_context)
        self.assertIn("👤 USER: plant: tomato, farmer: John, location: Karnataka", formatted_context)
        self.assertIn("💬 RECENT: My tomato plants have dark spots on leaves", formatted_context)
        
        # Create full prompt
        prompt = self.completed_node._create_next_steps_prompt(context)
        
        # Verify prompt structure
        self.assertIn("CURRENT WORKFLOW CONTEXT:", prompt)
        self.assertIn("SERVICES WE PROVIDE:", prompt)
        self.assertIn("Plant Disease Classification", prompt)
        self.assertIn("Treatment Recommendations", prompt)
        self.assertIn("Crop Insurance Services", prompt)
        self.assertIn("GUIDELINES:", prompt)
        self.assertIn("RESPONSE FORMAT:", prompt)
        self.assertIn("JSON array", prompt)
    
    def test_json_response_parsing(self):
        """Test parsing of JSON array responses from LLM"""
        # Test valid JSON response
        json_response = '["💊 Get treatment recommendations for this disease", "🛡️ Get crop insurance recommendations", "📸 Upload another plant image"]'
        
        result = self.completed_node._parse_next_steps_response(json_response)
        
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], "💊 Get treatment recommendations for this disease")
        self.assertEqual(result[1], "🛡️ Get crop insurance recommendations")
        self.assertEqual(result[2], "📸 Upload another plant image")
    
    def test_bullet_point_response_parsing(self):
        """Test parsing of bullet point responses from LLM"""
        # Test bullet point response
        bullet_response = """Here are the next steps:
        • 💊 Get treatment recommendations for this disease
        • 🛡️ Get crop insurance recommendations based on this disease  
        • 📸 Upload another plant image for analysis"""
        
        result = self.completed_node._parse_next_steps_response(bullet_response)
        
        self.assertEqual(len(result), 3)
        self.assertIn("💊 Get treatment recommendations for this disease", result[0])
        self.assertIn("🛡️ Get crop insurance recommendations", result[1])
        self.assertIn("📸 Upload another plant image", result[2])
    
    def test_numbered_list_response_parsing(self):
        """Test parsing of numbered list responses from LLM"""
        numbered_response = """Next steps:
        1. 💊 Get treatment recommendations for this disease
        2. 🛡️ Calculate crop insurance premium for protection
        3. 📸 Upload another plant image for analysis"""
        
        result = self.completed_node._parse_next_steps_response(numbered_response)
        
        self.assertEqual(len(result), 3)
        self.assertIn("💊 Get treatment recommendations", result[0])
        self.assertIn("🛡️ Calculate crop insurance premium", result[1])
        self.assertIn("📸 Upload another plant image", result[2])
    
    def test_fallback_next_steps(self):
        """Test fallback next steps when LLM fails"""
        # Test for new session (no classification)
        state_new = self.create_state()
        fallback_new = self.completed_node._get_fallback_next_steps(state_new)
        
        self.assertIn("🔍 Upload plant image for disease diagnosis", fallback_new[0])
        self.assertIn("📸 Upload another image for analysis", fallback_new)
        self.assertIn("❓ Ask general questions about plant care", fallback_new)
        
        # Test for disease detected (no prescription)
        state_disease = self.create_state(disease_name="tomato_blight")
        fallback_disease = self.completed_node._get_fallback_next_steps(state_disease)
        
        self.assertIn("💊 Get treatment recommendations", fallback_disease[0])
        
        # Test for no insurance
        state_no_insurance = self.create_state(
            classification_results={"confidence": 0.8},
            prescription_data={"treatments": []}
        )
        fallback_no_insurance = self.completed_node._get_fallback_next_steps(state_no_insurance)
        
        self.assertIn("🛡️ Explore crop insurance options", fallback_no_insurance[0])
    
    @patch('fsm_agent.core.nodes.completed_node.logger')
    def test_llm_success_flow(self, mock_logger):
        """Test successful LLM flow for next steps generation"""
        # Mock LLM response
        mock_response = Mock()
        mock_response.content = '["💊 Get treatment recommendations for this disease", "🛡️ Get crop insurance recommendations", "📸 Upload another plant image"]'
        self.mock_llm.invoke.return_value = mock_response
        
        state = self.create_state(
            classification_results={"confidence": 0.87},
            disease_name="tomato_late_blight",
            plant_type="tomato"
        )
        
        result = self.completed_node._generate_contextual_next_steps(state)
        
        # Verify LLM was called
        self.mock_llm.invoke.assert_called_once()
        
        # Verify result
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], "💊 Get treatment recommendations for this disease")
        self.assertEqual(result[1], "🛡️ Get crop insurance recommendations") 
        self.assertEqual(result[2], "📸 Upload another plant image")
    
    @patch('fsm_agent.core.nodes.completed_node.logger')
    def test_llm_failure_fallback(self, mock_logger):
        """Test fallback when LLM fails"""
        # Mock LLM to raise exception
        self.mock_llm.invoke.side_effect = Exception("LLM connection failed")
        
        state = self.create_state(disease_name="tomato_blight")
        
        result = self.completed_node._generate_contextual_next_steps(state)
        
        # Verify error was logged
        mock_logger.error.assert_called_once()
        self.assertIn("Error generating contextual next steps", mock_logger.error.call_args[0][0])
        
        # Verify fallback was used
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        self.assertLessEqual(len(result), 3)
    
    def test_conversation_summary_extraction(self):
        """Test extraction of conversation summary from messages"""
        state = self.create_state(
            messages=[
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
                {"role": "user", "content": "My plant has spots"},
                {"role": "assistant", "content": "Let me analyze that"},
                {"role": "user", "content": "What treatment do you recommend?"},
                {"role": "assistant", "content": "Here are treatments..."},
                {"role": "user", "content": "How do I apply the fungicide?"}
            ]
        )
        
        context = self.completed_node._build_workflow_context(state)
        
        # Should contain last 2 user messages
        expected_summary = "What treatment do you recommend? | How do I apply the fungicide?"
        self.assertEqual(context["conversation_summary"], expected_summary)


class TestServiceErrorHandling(unittest.TestCase):
    """Test suite for service error handling and failure detection"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.completed_node = CompletedNode()
        
        # Base state and context templates
        self.base_state = {
            "session_id": "test-session",
            "current_node": "completed",
            "messages": []
        }
        
        self.base_context = {
            "services_count": 1,
            "services_list": [],
            "state": {}
        }
    
    def create_error_context(self, service: str, state_overrides: dict = None, context_overrides: dict = None):
        """Helper to create context with error conditions"""
        state = self.base_state.copy()
        if state_overrides:
            state.update(state_overrides)
            
        context = self.base_context.copy()
        context["services_list"] = [service]
        context["state"] = state
        if context_overrides:
            context.update(context_overrides)
            
        return context
    
    def test_classification_error_detection(self):
        """Test detection of classification errors"""
        # Test general error state
        context = self.create_error_context("classification", {
            "error_message": "Classification model unavailable"
        })
        
        error_info = self.completed_node._check_service_errors("classification", context)
        self.assertIsNotNone(error_info)
        title, message = error_info
        self.assertIn("PLANT DIAGNOSIS ERROR", title)
        self.assertIn("Classification model unavailable", message)
        
        # Test no results scenario
        context = self.create_error_context("classification", {
            # No classification_results or disease_name
        })
        
        error_info = self.completed_node._check_service_errors("classification", context)
        self.assertIsNotNone(error_info)
        title, message = error_info
        self.assertIn("PLANT DIAGNOSIS INCOMPLETE", title)
        self.assertIn("Disease analysis could not be completed", message)
        
        # Test tool-specific error
        context = self.create_error_context("classification", {
            "tool_results": {
                "classification": {"error": "Image processing failed"}
            }
        })
        
        error_info = self.completed_node._check_service_errors("classification", context)
        self.assertIsNotNone(error_info)
        title, message = error_info
        self.assertIn("PLANT DIAGNOSIS FAILED", title)
        self.assertIn("Image processing failed", message)
    
    def test_prescription_error_detection(self):
        """Test detection of prescription errors"""
        # Test no results scenario
        context = self.create_error_context("prescription", {
            # No prescription_data or treatment_recommendations
        })
        
        error_info = self.completed_node._check_service_errors("prescription", context)
        self.assertIsNotNone(error_info)
        title, message = error_info
        self.assertIn("TREATMENT RECOMMENDATIONS INCOMPLETE", title)
        self.assertIn("Treatment recommendations could not be generated", message)
        
        # Test tool-specific error
        context = self.create_error_context("prescription", {
            "tool_results": {
                "prescription": {"error": "LLM service timeout"}
            }
        })
        
        error_info = self.completed_node._check_service_errors("prescription", context)
        self.assertIsNotNone(error_info)
        title, message = error_info
        self.assertIn("TREATMENT RECOMMENDATIONS FAILED", title)
        self.assertIn("LLM service timeout", message)
    
    def test_insurance_error_detection(self):
        """Test detection of insurance (MCP) errors"""
        # Test no results scenario (MCP server unavailable)
        context = self.create_error_context("insurance", {
            # No insurance data fields
        })
        
        error_info = self.completed_node._check_service_errors("insurance", context)
        self.assertIsNotNone(error_info)
        title, message = error_info
        self.assertIn("CROP INSURANCE INCOMPLETE", title)
        self.assertIn("Insurance service is currently unavailable", message)
        
        # Test MCP server specific error
        context = self.create_error_context("insurance", {
            "tool_results": {
                "insurance": {"error": "MCP server connection failed"}
            }
        })
        
        error_info = self.completed_node._check_service_errors("insurance", context)
        self.assertIsNotNone(error_info)
        title, message = error_info
        self.assertIn("CROP INSURANCE TEMPORARILY UNAVAILABLE", title)
        self.assertIn("technical difficulties", message)
        
        # Test generic insurance error
        context = self.create_error_context("insurance", {
            "tool_results": {
                "insurance": {"error": "Invalid farmer credentials"}
            }
        })
        
        error_info = self.completed_node._check_service_errors("insurance", context)
        self.assertIsNotNone(error_info)
        title, message = error_info
        self.assertIn("CROP INSURANCE FAILED", title)
        self.assertIn("Invalid farmer credentials", message)
    
    def test_successful_service_no_errors(self):
        """Test that successful services don't trigger error detection"""
        # Classification success
        context = self.create_error_context("classification", {
            "classification_results": {"confidence": 0.85},
            "disease_name": "tomato_blight"
        })
        
        error_info = self.completed_node._check_service_errors("classification", context)
        self.assertIsNone(error_info)
        
        # Prescription success
        context = self.create_error_context("prescription", {
            "prescription_data": {"treatments": ["Fungicide A"]},
            "treatment_recommendations": [{"name": "Treatment 1"}]
        })
        
        error_info = self.completed_node._check_service_errors("prescription", context)
        self.assertIsNone(error_info)
        
        # Insurance success
        context = self.create_error_context("insurance", {
            "insurance_premium_details": {"premium": 5000},
            "insurance_recommendations": {"policy": "Crop Shield"}
        })
        
        error_info = self.completed_node._check_service_errors("insurance", context)
        self.assertIsNone(error_info)
    
    def test_single_service_summary_with_errors(self):
        """Test single service summary shows error messages instead of success"""
        # Test classification error
        context = self.create_error_context("classification", {
            "error_message": "Model loading failed"
        }, {
            "disease_name": "tomato_blight",  # This data exists but error occurred
            "plant_type": "tomato"
        })
        
        title, summary = self.completed_node._get_single_service_summary("classification", context)
        self.assertIn("⚠️", title)
        self.assertIn("Model loading failed", summary)
        
        # Test insurance MCP error
        context = self.create_error_context("insurance", {
            "tool_results": {
                "insurance": {"error": "MCP server timeout"}
            }
        }, {
            "farmer_name": "John",
            "crop": "wheat"
        })
        
        title, summary = self.completed_node._get_single_service_summary("insurance", context)
        self.assertIn("⚠️", title)
        self.assertIn("temporarily unavailable", summary.lower())
    
    def test_multiple_services_mixed_results(self):
        """Test multiple services with mixed success/failure"""
        # Classification succeeds, prescription fails, insurance succeeds
        state = {
            "classification_results": {"confidence": 0.9},
            "disease_name": "wheat_rust",
            # No prescription data - prescription failed
            "insurance_premium_details": {"premium": 6000}
        }
        
        context = {
            "services_list": ["classification", "prescription", "insurance"],
            "state": state,
            "disease_name": "wheat_rust",
            "treatment_count": 0,  # No treatments due to failure
            "insurance_type": "premium calculation"
        }
        
        summary = self.completed_node._get_multiple_services_summary(
            ["classification", "prescription", "insurance"], 
            context
        )
        
        # Should mention successes and failures
        self.assertIn("diagnosed wheat_rust", summary)
        self.assertIn("handled crop premium calculation", summary)
        self.assertIn("treatment recommendations encountered issues", summary)
        self.assertIn("retry", summary.lower())
    
    def test_error_priority_over_success_data(self):
        """Test that errors are detected even when success data exists"""
        # Scenario: Data exists in state but error also occurred
        context = self.create_error_context("insurance", {
            "insurance_premium_details": {"premium": 5000},  # Data exists
            "error_message": "Payment processing failed"  # But error occurred
        })
        
        error_info = self.completed_node._check_service_errors("insurance", context)
        self.assertIsNotNone(error_info)
        title, message = error_info
        self.assertIn("⚠️", title)
        self.assertIn("Payment processing failed", message)


class TestErrorNodeImprovements(unittest.TestCase):
    """Test suite for improved error node user-friendly messages"""
    
    def setUp(self):
        """Set up test fixtures"""
        from fsm_agent.core.nodes.error_node import ErrorNode
        self.error_node = ErrorNode()
    
    def test_mcp_server_error_formatting(self):
        """Test MCP server error gets user-friendly message"""
        error_msg = "Sasya Arogya MCP server not available"
        
        formatted = self.error_node._format_user_friendly_error(error_msg)
        
        self.assertIn("INSURANCE SERVICE TEMPORARILY UNAVAILABLE", formatted)
        self.assertIn("technical difficulties", formatted)
        self.assertIn("try again in a few minutes", formatted)
        self.assertNotIn("MCP", formatted)  # Technical jargon removed
        self.assertNotIn("Sasya Arogya", formatted)  # Internal names removed
    
    def test_model_loading_error_formatting(self):
        """Test ML model error gets user-friendly message"""
        error_msg = "Classification model loading failed"
        
        formatted = self.error_node._format_user_friendly_error(error_msg)
        
        self.assertIn("PLANT DIAGNOSIS TEMPORARILY UNAVAILABLE", formatted)
        self.assertIn("being updated", formatted)
        self.assertIn("try uploading your plant image again", formatted)
    
    def test_image_processing_error_formatting(self):
        """Test image processing error gets user-friendly message"""
        error_msg = "Image processing failed - invalid format"
        
        formatted = self.error_node._format_user_friendly_error(error_msg)
        
        self.assertIn("IMAGE PROCESSING ISSUE", formatted)
        self.assertIn("clearer photo", formatted)
        self.assertIn("good lighting", formatted)
    
    def test_connection_error_formatting(self):
        """Test connection error gets user-friendly message"""
        error_msg = "Connection timeout to external service"
        
        formatted = self.error_node._format_user_friendly_error(error_msg)
        
        self.assertIn("CONNECTION ISSUE", formatted)
        self.assertIn("connectivity issues", formatted)
        self.assertIn("check your internet connection", formatted)
    
    def test_llm_service_error_formatting(self):
        """Test LLM service error gets user-friendly message"""
        error_msg = "LLM generation service unavailable"
        
        formatted = self.error_node._format_user_friendly_error(error_msg)
        
        self.assertIn("AI SERVICE TEMPORARILY UNAVAILABLE", formatted)
        self.assertIn("AI-powered recommendation system", formatted)
        self.assertIn("try again in a few minutes", formatted)
    
    def test_generic_error_formatting(self):
        """Test generic error gets appropriate message"""
        error_msg = "Unexpected database connection failed"
        
        formatted = self.error_node._format_user_friendly_error(error_msg)
        
        self.assertIn("TEMPORARY SERVICE ISSUE", formatted)
        self.assertIn("technical issue", formatted)
        self.assertIn("Unexpected database connection failed", formatted)  # Original error included
        self.assertIn("try your request again", formatted)
    
    def test_unknown_error_formatting(self):
        """Test completely unknown error gets fallback message"""
        error_msg = "Something completely unexpected happened"
        
        formatted = self.error_node._format_user_friendly_error(error_msg)
        
        self.assertIn("UNEXPECTED ERROR", formatted)
        self.assertIn("Something completely unexpected happened", formatted)
        self.assertIn("contact support", formatted)
    
    def test_mcp_variations_detected(self):
        """Test different MCP error message variations are detected"""
        variations = [
            "MCP server connection failed",
            "Sasya Arogya MCP server not available", 
            "mcp server timeout",
            "MCP Server unreachable"
        ]
        
        for error_msg in variations:
            formatted = self.error_node._format_user_friendly_error(error_msg)
            self.assertIn("INSURANCE SERVICE TEMPORARILY UNAVAILABLE", formatted)
            self.assertNotIn("MCP", formatted)
    
    def test_empty_response_handling(self):
        """Test handling of empty or invalid LLM responses"""
        # Test empty response
        empty_result = self.completed_node._parse_next_steps_response("")
        self.assertEqual(empty_result, [])
        
        # Test invalid JSON
        invalid_json = '{"invalid": "format"}'
        invalid_result = self.completed_node._parse_next_steps_response(invalid_json)
        self.assertEqual(invalid_result, [])
        
        # Test malformed response
        malformed = "This is not a valid response format"
        malformed_result = self.completed_node._parse_next_steps_response(malformed)
        self.assertEqual(malformed_result, [])


class TestIntegrationScenarios(unittest.TestCase):
    """Integration tests for complete workflow scenarios"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_llm = Mock()
        self.completed_node = CompletedNode()
        self.completed_node.llm = self.mock_llm
    
    def test_scenario_new_farmer(self):
        """Test scenario: New farmer, first interaction"""
        # Mock LLM response for new session
        mock_response = Mock()
        mock_response.content = '["🔍 Upload plant image for disease diagnosis", "🛡️ Explore crop insurance options", "❓ Ask general questions about plant care"]'
        self.mock_llm.invoke.return_value = mock_response
        
        state = {
            "session_id": "new-farmer-session",
            "current_node": "completed",
            "messages": [{"role": "user", "content": "I'm new to farming, can you help me?"}]
        }
        
        result = self.completed_node._generate_contextual_next_steps(state)
        
        # Verify appropriate suggestions for new farmer
        self.assertIn("🔍 Upload plant image for disease diagnosis", result[0])
        self.assertIn("🛡️ Explore crop insurance options", result)
        self.assertIn("❓ Ask general questions about plant care", result)
    
    def test_scenario_experienced_farmer_disease_follow_up(self):
        """Test scenario: Experienced farmer with disease, seeking follow-up"""
        # Mock LLM response for disease follow-up
        mock_response = Mock()
        mock_response.content = '["📊 Learn about treatment monitoring and progress tracking", "🌱 Get preventive care tips", "📄 Generate insurance certificate"]'
        self.mock_llm.invoke.return_value = mock_response
        
        state = {
            "session_id": "experienced-farmer-session",
            "current_node": "completed",
            "classification_results": {"confidence": 0.91},
            "disease_name": "cotton_bollworm",
            "prescription_data": {"treatments": [{"name": "Insecticide"}, {"name": "Bio-control"}]},
            "treatment_recommendations": [{"name": "Treatment 1"}, {"name": "Treatment 2"}],
            "insurance_premium_details": {"premium": 8000},
            "plant_type": "cotton",
            "farmer_name": "Suresh",
            "location": "Gujarat",
            "messages": [
                {"role": "user", "content": "I've applied the treatment, what's next?"}
            ]
        }
        
        result = self.completed_node._generate_contextual_next_steps(state)
        
        # Should focus on monitoring and next steps since treatment is applied
        self.assertIn("📊 Learn about treatment monitoring", result[0])
        self.assertEqual(len(result), 3)


if __name__ == "__main__":
    # Run the tests
    unittest.main(verbosity=2)
