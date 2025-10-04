"""
Completed Node for FSM Agent workflow
Final state with follow-up questions
"""

import logging
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime

from .base_node import BaseNode

try:
    from ..workflow_state import WorkflowState, add_message_to_state
except ImportError:
    from ..workflow_state import WorkflowState, add_message_to_state

logger = logging.getLogger(__name__)


class CompletedNode(BaseNode):
    """Completed node - final state with follow-up questions"""
    
    @property
    def node_name(self) -> str:
        return "completed"
    
    async def execute(self, state: WorkflowState) -> WorkflowState:
        """
        Execute completed node logic
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        self.update_node_state(state)
        
        # FIXED: Never do goodbye detection in completed node!
        # Goodbye detection is handled at routing level (initial_node, followup_node)
        # The completed node should ONLY create completion messages and end the workflow
        
        # FIXED: Check if there's a clean, direct response from followup node
        existing_response = state.get("assistant_response", "")
        previous_node = state.get("previous_node", "")
        
        # Analyze what services were actually used to generate contextual completion
        services_used = self._analyze_services_used(state)
        completion_context = self._create_completion_context(state, services_used)
        
        # Generate relevant follow-ups using LLM-driven contextual next steps
        follow_ups = self._generate_contextual_next_steps(state)
        
        # Create contextual completion message based on what actually happened
        if existing_response and existing_response.strip() and previous_node == "followup":
            # Direct followup response - use as-is, just add minimal follow-up options
            completion_message = self._create_clean_followup_response(existing_response, follow_ups)
        elif existing_response and existing_response.strip():
            # Tool workflow completed - add follow-up options without ugly formatting
            completion_message = self._create_clean_workflow_completion(existing_response, follow_ups, state)
        else:
            # No direct response - show contextual completion message based on services used
            completion_message = self._create_contextual_completion_message(services_used, completion_context, follow_ups)
        
        # Store the enhanced completion response
        state["assistant_response"] = completion_message
        
        # GENERIC ARCHITECTURAL FIX: Mark response as final and ready for streaming
        state["response_status"] = "final"  # This is the enhanced, final version
        state["stream_immediately"] = True  # Ready to stream to user
        state["stream_in_state_update"] = False  # Use dedicated streaming, not state_update
        
        # Also add to messages for conversation history
        add_message_to_state(state, "assistant", completion_message)
        
        # FIXED: Never mark session as complete in completed node
        # Only session_end node should mark sessions as ended
        state["is_complete"] = False  # Workflow complete, but session continues
        
        return state
    
    def _analyze_services_used(self, state: WorkflowState) -> Dict[str, bool]:
        """Analyze which services were actually used in this session"""
        return {
            "classification": bool(state.get("classification_results") or state.get("disease_name")),
            "prescription": bool(state.get("prescription_data") or state.get("treatment_recommendations")),
            "insurance": bool(state.get("insurance_context") or state.get("insurance_premium_details") 
                           or state.get("insurance_recommendations") or state.get("insurance_companies"))
        }
    
    def _create_completion_context(self, state: WorkflowState, services_used: Dict[str, bool]) -> Dict[str, Any]:
        """Create context summary of what happened in this session"""
        context = {
            "services_count": sum(services_used.values()),
            "services_list": [service for service, used in services_used.items() if used],
            "state": state  # Pass state for error checking
        }
        
        # Extract key details for each service used
        if services_used["classification"]:
            context["disease_name"] = state.get("disease_name", "disease")
            context["plant_type"] = state.get("plant_type", "plant")
            
        if services_used["prescription"]:
            treatments = state.get("treatment_recommendations", [])
            context["treatment_count"] = len(treatments)
            
        if services_used["insurance"]:
            context["farmer_name"] = state.get("farmer_name", "Farmer")
            context["crop"] = state.get("plant_type") or "your crop"
            context["insurance_type"] = "recommendation" if state.get("insurance_recommendations") else "premium calculation"
        
        return context
    
    def _create_contextual_completion_message(self, services_used: Dict[str, bool], context: Dict[str, Any], follow_ups: List[str]) -> str:
        """Create appropriate completion message based on services actually used"""
        services_list = context["services_list"]
        services_count = context["services_count"]
        
        if services_count == 0:
            # No specific services used - general help
            title = "✅ **HOW CAN I HELP YOU?**"
            summary = "I'm here to help with plant disease diagnosis, treatment recommendations, and crop insurance."
        elif services_count == 1:
            # Single service used
            service = services_list[0]
            title, summary = self._get_single_service_summary(service, context)
        else:
            # Multiple services used
            title = f"✅ **YOUR {services_count} SERVICES COMPLETED**"
            summary = self._get_multiple_services_summary(services_list, context)
        
        # Build the completion message
        completion_message = f"{title}\n\n🌱 **WHAT WE DID**\n{summary}"
        
        # Add next steps
        completion_message += "\n\n🚀 **WHAT TO DO NEXT**"
        if follow_ups:
            for i, follow_up in enumerate(follow_ups, 1):
                completion_message += f"\n{i}. {follow_up}"
        else:
            completion_message += "\n1. Ask me any questions about your results\n2. Upload new images for analysis\n3. Get additional recommendations"
        
        # Add contextual help section
        completion_message += self._get_contextual_help_section(services_used)
        
        return completion_message
    
    def _get_single_service_summary(self, service: str, context: Dict[str, Any]) -> Tuple[str, str]:
        """Get title and summary for single service completion - checks for errors first"""
        # First check if there are any errors for this service
        error_info = self._check_service_errors(service, context)
        if error_info:
            return error_info
            
        # Only show success if no errors detected
        if service == "classification":
            disease = context.get("disease_name", "disease")
            plant = context.get("plant_type", "plant") or "plant"
            return f"✅ **YOUR {plant.upper()} DIAGNOSIS COMPLETE**", f"We analyzed your plant and identified {disease}. Our smart system provided detailed diagnostic information."
            
        elif service == "prescription":
            treatment_count = context.get("treatment_count", 0)
            return "✅ **YOUR TREATMENT PLAN READY**", f"We provided you with {treatment_count} treatment options and preventive measures for your plant's condition."
            
        elif service == "insurance":
            farmer = context.get("farmer_name", "Farmer")
            crop = context.get("crop", "crop")
            insurance_type = context.get("insurance_type", "insurance") or "services"
            return f"✅ **YOUR CROP INSURANCE {insurance_type.upper()} COMPLETE**", f"We provided {farmer} with {insurance_type} for {crop} cultivation. Your insurance details are ready."
            
        else:
            return "✅ **SERVICE COMPLETED**", "We've completed your request and provided the information you needed."
    
    def _check_service_errors(self, service: str, context: Dict[str, Any]) -> Optional[Tuple[str, str]]:
        """Check if a service has errors based on current operation evidence, not persistent error state"""
        state = context.get("state")
        if not state:
            return None
            
        # REMOVED: Don't check persistent error_message - focus on current operation evidence
        # This prevents false errors when previous operations failed but current ones succeeded
        
        # Check tool results for service-specific errors (current operation evidence)
        tool_results = state.get("tool_results", {})
        
        if service == "classification":
            # Check if classification actually succeeded
            if not state.get("classification_results") and not state.get("disease_name"):
                return self._format_service_error(service, "Disease analysis could not be completed", "no_results")
            
            # Check for classification-specific errors in tool results
            if "classification" in tool_results:
                result = tool_results["classification"]
                if isinstance(result, dict) and result.get("error"):
                    return self._format_service_error(service, result["error"], "tool_error")
                    
        elif service == "prescription":
            # Check if prescription actually succeeded
            if not state.get("prescription_data") and not state.get("treatment_recommendations"):
                return self._format_service_error(service, "Treatment recommendations could not be generated", "no_results")
                
            # Check for prescription-specific errors
            if "prescription" in tool_results:
                result = tool_results["prescription"]
                if isinstance(result, dict) and result.get("error"):
                    return self._format_service_error(service, result["error"], "tool_error")
                    
        elif service == "insurance":
            # Check if insurance operation actually succeeded
            has_insurance_data = any([
                state.get("insurance_premium_details"),
                state.get("insurance_recommendations"),
                state.get("insurance_companies"),
                state.get("insurance_certificate")
            ])
            
            if not has_insurance_data:
                return self._format_service_error(service, "Insurance service is currently unavailable", "no_results")
                
            # Check for insurance-specific errors (MCP server issues)
            if "insurance" in tool_results:
                result = tool_results["insurance"]
                if isinstance(result, dict) and result.get("error"):
                    error_msg = result["error"]
                    if "mcp" in error_msg.lower() or "server" in error_msg.lower():
                        return self._format_service_error(service, "Insurance service is temporarily unavailable", "mcp_error")
                    else:
                        return self._format_service_error(service, error_msg, "tool_error")
        
        return None  # No errors detected
    
    def _format_service_error(self, service: str, error_msg: str, error_type: str) -> Tuple[str, str]:
        """Format appropriate error message for service failures"""
        service_names = {
            "classification": "Plant Diagnosis",
            "prescription": "Treatment Recommendations", 
            "insurance": "Crop Insurance"
        }
        
        service_name = service_names.get(service, "Service")
        
        if error_type == "mcp_error":
            title = f"⚠️ **{service_name.upper()} TEMPORARILY UNAVAILABLE**"
            message = f"Our insurance service is currently experiencing technical difficulties. Please try again in a few minutes or contact support if the issue persists."
            
        elif error_type == "no_results":
            title = f"⚠️ **{service_name.upper()} INCOMPLETE**"
            message = f"{error_msg}. Please try uploading a clearer image or providing more details, then retry the operation."
            
        elif error_type == "tool_error":
            title = f"⚠️ **{service_name.upper()} FAILED**"
            message = f"We encountered an issue: {error_msg}. Please try again or contact support if the problem continues."
            
        else:  # general error
            title = f"⚠️ **{service_name.upper()} ERROR**"
            message = f"An error occurred: {error_msg}. Please try again or contact support for assistance."
            
        return title, message
    
    def _get_multiple_services_summary(self, services_list: List[str], context: Dict[str, Any]) -> str:
        """Get summary for multiple services completion - handles mixed success/failure scenarios"""
        successes = []
        failures = []
        
        # Check each service for success or failure
        for service in services_list:
            error_info = self._check_service_errors(service, context)
            
            if error_info:
                # Service failed
                service_names = {
                    "classification": "plant diagnosis",
                    "prescription": "treatment recommendations", 
                    "insurance": "insurance services"
                }
                service_name = service_names.get(service, service)
                failures.append(service_name)
            else:
                # Service succeeded
                if service == "classification":
                    disease = context.get("disease_name", "disease")
                    successes.append(f"diagnosed {disease}")
                elif service == "prescription":
                    treatment_count = context.get("treatment_count", 0)
                    successes.append(f"provided {treatment_count} treatments")
                elif service == "insurance":
                    insurance_type = context.get("insurance_type", "insurance services")
                    successes.append(f"handled crop {insurance_type}")
        
        # Build summary message based on successes and failures
        if successes and failures:
            # Mixed scenario - some succeeded, some failed
            success_part = f"We {', '.join(successes[:-1])} and {successes[-1]}" if len(successes) > 1 else f"We {successes[0]}"
            failure_part = f"However, {', '.join(failures)} encountered issues"
            return f"{success_part} for you. {failure_part}. Please retry the failed operations."
            
        elif successes:
            # All succeeded
            if len(successes) > 1:
                return f"We {', '.join(successes[:-1])} and {successes[-1]} for you."
            else:
                return f"We {successes[0]} for you."
                
        elif failures:
            # All failed (shouldn't normally happen, but handle gracefully)
            return f"We encountered issues with {', '.join(failures)}. Please try again or contact support."
            
        else:
            # Fallback
            return "We processed your request."
    
    def _get_contextual_help_section(self, services_used: Dict[str, bool]) -> str:
        """Get contextual help section based on services used"""
        help_items = []
        
        if services_used["classification"] or services_used["prescription"]:
            help_items.extend([
                "Take new photos if you see more problems",
                "Ask questions about treatment progress"
            ])
            
        if services_used["insurance"]:
            help_items.extend([
                "Get insurance for additional crops",
                "Calculate premiums for different areas"
            ])
        
        # Add general help items
        help_items.extend([
            "Get tips for different seasons and weather",
            "Ask general agricultural questions"
        ])
        
        # Remove duplicates and limit to 4 items
        unique_help_items = list(dict.fromkeys(help_items))[:4]
        
        help_section = "\n\n💚 **WE'RE HERE TO HELP**"
        for item in unique_help_items:
            help_section += f"\n• {item}"
            
        return help_section
    
    def _create_clean_followup_response(self, direct_response: str, follow_ups: List[str]) -> str:
        """Create clean followup response without ugly formatting - farmers want direct answers!"""
        
        # FIXED: No ugly horizontal lines, no extra wrapping - just the answer!
        clean_message = direct_response.strip()
        
        # Add minimal follow-up options only if needed
        if follow_ups:
            clean_message += "\n\n💡 **Next steps**:"
            for follow_up in follow_ups[:2]:
                clean_message += f"\n• {follow_up}"
        else:
            clean_message += "\n\n💡 **Ask me anything else about your plants!**"
            
        return clean_message
    
    def _create_clean_workflow_completion(self, workflow_response: str, follow_ups: List[str], state: WorkflowState) -> str:
        """Create clean completion for workflow tools (classification, prescription) without ugly formatting"""
        
        # FIXED: No ugly horizontal lines - just clean completion
        clean_message = workflow_response.strip()
        
        # Add clean next steps for workflow completions
        clean_message += "\n\n**What would you like to do next?**"
        if follow_ups:
            for i, follow_up in enumerate(follow_ups[:3], 1):
                clean_message += f"\n• {follow_up}"
        else:
            # Generate contextual next steps based on what has been done
            contextual_steps = self._generate_contextual_next_steps(state)
            if contextual_steps:
                for step in contextual_steps:
                    clean_message += f"\n• {step}"
            else:
                clean_message += "\n\n💡 **Ask me anything else about your plants!**"
            
        return clean_message
    
    def _generate_contextual_next_steps(self, state: WorkflowState) -> List[str]:
        """Generate contextual next steps using LLM based on current workflow state"""
        try:
            # Get current workflow context
            context = self._build_workflow_context(state)
            
            # Use LLM to determine next steps
            prompt = self._create_next_steps_prompt(context)
            response = self.llm.invoke(prompt)
            
            # Parse LLM response to extract next steps
            next_steps = self._parse_next_steps_response(response.content)
            
            # Return maximum 3 steps
            return next_steps[:3]
            
        except Exception as e:
            logger.error(f"Error generating contextual next steps: {e}")
            # Fallback to basic next steps
            return self._get_fallback_next_steps(state)
    
    def _build_workflow_context(self, state: WorkflowState) -> Dict[str, Any]:
        """Build comprehensive workflow context for LLM"""
        context = {
            "completed_operations": {},
            "available_data": {},
            "user_context": {},
            "conversation_summary": ""
        }
        
        # Track completed operations
        context["completed_operations"] = {
            "classification": bool(state.get("classification_results") or state.get("disease_name")),
            "prescription": bool(state.get("prescription_data") or state.get("treatment_recommendations")),
            "insurance": bool(state.get("insurance_premium_details") or state.get("insurance_recommendations") 
                           or state.get("insurance_companies") or state.get("insurance_certificate"))
        }
        
        # Extract available data details
        if context["completed_operations"]["classification"]:
            disease_name = state.get("disease_name", "")
            is_healthy = disease_name.lower() in ["healthy", "healthy_plant"]
            context["available_data"]["disease_info"] = {
                "disease_name": disease_name,
                "is_healthy": is_healthy,
                "confidence": state.get("classification_results", {}).get("confidence", 0)
            }
            
        if context["completed_operations"]["prescription"]:
            treatments = state.get("treatment_recommendations", [])
            context["available_data"]["treatment_info"] = {
                "treatment_count": len(treatments),
                "has_treatments": len(treatments) > 0
            }
            
        if context["completed_operations"]["insurance"]:
            context["available_data"]["insurance_info"] = {
                "has_premium": bool(state.get("insurance_premium_details")),
                "has_recommendations": bool(state.get("insurance_recommendations")),
                "has_companies": bool(state.get("insurance_companies")),
                "has_certificate": bool(state.get("insurance_certificate"))
            }
        
        # User context
        context["user_context"] = {
            "plant_type": state.get("plant_type", ""),
            "farmer_name": state.get("farmer_name", ""),
            "location": state.get("location", "")
        }
        
        # Recent conversation context
        messages = state.get("messages", [])
        recent_messages = messages[-4:] if len(messages) > 4 else messages
        user_messages = [msg.get("content", "") for msg in recent_messages if msg.get("role") == "user"]
        context["conversation_summary"] = " | ".join(user_messages[-2:]) if user_messages else ""
        
        return context
    
    def _create_next_steps_prompt(self, context: Dict[str, Any]) -> str:
        """Create prompt for LLM to determine contextual next steps"""
        
        # Build context description
        context_desc = self._format_context_for_prompt(context)
        
        prompt = f"""You are an expert agricultural assistant helping farmers with plant disease diagnosis, treatment recommendations, and crop insurance services.

CURRENT WORKFLOW CONTEXT:
{context_desc}

SERVICES WE PROVIDE:
1. Plant Disease Classification - Analyze plant images to identify diseases
2. Treatment Recommendations - Provide specific treatment plans and medicines  
3. Crop Insurance Services - Calculate premiums, recommend policies, find companies, generate certificates
4. General Agricultural Guidance - Soil health, weather tips, farming best practices

TASK: Based on the current context, suggest 2-3 logical next steps that would be most helpful to the user.

GUIDELINES:
- Only suggest services we actually provide
- Don't suggest operations that are already completed unless there's a good reason (like getting insurance for a different crop)
- Consider the natural workflow progression 
- Be contextually relevant to what the user has accomplished
- Focus on actionable next steps, not just general advice
- Use emojis to make suggestions engaging: 📸 🔍 💊 🛡️ 📋 📊 🌱 ❓

RESPONSE FORMAT:
Return ONLY a JSON array of 2-3 next step strings. Each string should be a clear, actionable suggestion.

Example: ["💊 Get treatment recommendations for this disease", "🛡️ Calculate crop insurance premium for protection", "📸 Upload another plant image for analysis"]

Response:"""

        return prompt
    
    def _format_context_for_prompt(self, context: Dict[str, Any]) -> str:
        """Format context information for the prompt"""
        lines = []
        
        # Completed operations
        completed = context["completed_operations"]
        completed_list = [op for op, done in completed.items() if done]
        if completed_list:
            lines.append(f"✅ COMPLETED: {', '.join(completed_list)}")
        else:
            lines.append("✅ COMPLETED: None (new session)")
            
        # Available data details
        data = context["available_data"]
        if "disease_info" in data:
            disease = data["disease_info"]
            status = "healthy" if disease["is_healthy"] else f"diseased ({disease['disease_name']})"
            lines.append(f"🌿 PLANT STATUS: {status} (confidence: {disease['confidence']:.0%})")
            
        if "treatment_info" in data:
            treatment = data["treatment_info"]
            lines.append(f"💊 TREATMENT: {treatment['treatment_count']} recommendations provided")
            
        if "insurance_info" in data:
            insurance = data["insurance_info"]
            insurance_parts = []
            if insurance["has_premium"]: insurance_parts.append("premium calculated")
            if insurance["has_recommendations"]: insurance_parts.append("recommendations given")
            if insurance["has_companies"]: insurance_parts.append("companies listed")
            if insurance["has_certificate"]: insurance_parts.append("certificate generated")
            if insurance_parts:
                lines.append(f"🛡️ INSURANCE: {', '.join(insurance_parts)}")
                
        # User context
        user = context["user_context"]
        user_details = []
        if user["plant_type"]: user_details.append(f"plant: {user['plant_type']}")
        if user["farmer_name"]: user_details.append(f"farmer: {user['farmer_name']}")
        if user["location"]: user_details.append(f"location: {user['location']}")
        if user_details:
            lines.append(f"👤 USER: {', '.join(user_details)}")
            
        # Recent conversation
        if context["conversation_summary"]:
            lines.append(f"💬 RECENT: {context['conversation_summary']}")
            
        return "\n".join(lines)
    
    def _parse_next_steps_response(self, response_content: str) -> List[str]:
        """Parse LLM response to extract next steps"""
        try:
            import json
            import re
            
            # Try to extract JSON array from response
            json_match = re.search(r'\[.*?\]', response_content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                next_steps = json.loads(json_str)
                if isinstance(next_steps, list):
                    return [step for step in next_steps if isinstance(step, str)]
                    
            # Fallback: try to extract bullet points
            lines = response_content.split('\n')
            steps = []
            for line in lines:
                line = line.strip()
                # Look for bullet points or numbered items
                if line.startswith(('•', '-', '*', '1.', '2.', '3.')):
                    clean_step = re.sub(r'^[\s\-\*\•\d\.]+', '', line).strip()
                    if clean_step:
                        steps.append(clean_step)
                        
            return steps
            
        except Exception as e:
            logger.error(f"Error parsing next steps response: {e}")
            return []
    
    def _get_fallback_next_steps(self, state: WorkflowState) -> List[str]:
        """Fallback next steps if LLM fails"""
        fallback_steps = [
            "📸 Upload another image for analysis",
            "❓ Ask general questions about plant care"
        ]
        
        # Add contextual fallback based on state
        if not state.get("classification_results") and not state.get("disease_name"):
            fallback_steps.insert(0, "🔍 Upload plant image for disease diagnosis")
        elif state.get("disease_name") and not state.get("prescription_data"):
            fallback_steps.insert(0, "💊 Get treatment recommendations")
        elif not state.get("insurance_recommendations"):
            fallback_steps.insert(0, "🛡️ Explore crop insurance options")
            
        return fallback_steps[:3]
