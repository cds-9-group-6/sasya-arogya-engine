"""
Insurance Node for FSM Agent workflow
Handles crop insurance operations and context extraction
"""

import logging
from typing import Dict, Any, Optional, List
import re

from .base_node import BaseNode
from ..workflow_state import WorkflowState, add_message_to_state, set_error

logger = logging.getLogger(__name__)


class InsuranceNode(BaseNode):
    """Insurance node - handles crop insurance operations and context gathering"""
    
    @property
    def node_name(self) -> str:
        return "insurance"
    
    async def execute(self, state: WorkflowState) -> WorkflowState:
        """
        Execute insurance node logic
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        self.update_node_state(state)
        logger.info(f"Insurance request detected for session {state['session_id']}")
        
        try:
            # Extract insurance context from state and user message
            insurance_context = self._extract_insurance_context(state)
            state["insurance_context"] = insurance_context
            
            logger.info(f"Extracted insurance context: {insurance_context}")
            
            # Check if we have sufficient context to proceed
            missing_fields = self._check_required_context(insurance_context)
            
            if missing_fields:
                # Prompt user for missing information
                await self._prompt_for_missing_info(state, missing_fields)
                state["next_action"] = "followup"  # Wait for user input
                state["requires_user_input"] = True
                return state
            
            # Determine the appropriate insurance action based on context
            action = self._determine_insurance_action(state, insurance_context)
            
            # Execute insurance operation
            result = await self._execute_insurance_operation(state, action, insurance_context)
            
            if result and not result.get("error"):
                # Store insurance results in state
                self._store_insurance_results(state, action, result)
                
                # Provide response to user
                await self._provide_insurance_response(state, action, result)
                
                # Clear requires_user_input flag since operation completed successfully
                state["requires_user_input"] = False
                
                # Determine next action
                next_action = self._determine_next_action(state, action, result)
                state["next_action"] = next_action
                
                logger.info(f"Insurance operation '{action}' completed successfully")
            else:
                # Handle error
                error_msg = result.get("error", "Unknown insurance operation error")
                set_error(state, error_msg)
                state["next_action"] = "error"
                logger.error(f"Insurance operation failed: {error_msg}")
            
            return state
            
        except Exception as e:
            error_msg = f"Insurance node execution error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            set_error(state, error_msg)
            state["next_action"] = "error"
            return state
    
    def _extract_insurance_context(self, state: WorkflowState) -> Dict[str, Any]:
        """Extract insurance-related context from state and user message"""
        context = {}
        user_message = state.get("user_message", "").lower()
        
        # Extract existing context from state
        context["disease"] = state.get("disease_name")  # Optional - can be None
        context["crop"] = state.get("plant_type") or state.get("crop")  # Check both fields
        context["state"] = state.get("location") or state.get("state")  # Check both fields
        context["farmer_name"] = state.get("farmer_name")
        context["area_hectare"] = state.get("area_hectare")
        
        # Extract additional context from user message
        extracted = self._extract_from_message(user_message)
        context.update(extracted)
        
        # Set reasonable defaults for optional fields
        if not context.get("farmer_name"):
            context["farmer_name"] = "Farmer"  # Default farmer name
        
        # Keep disease as optional - don't set default
        # Clean up None values but preserve disease as None if not provided
        cleaned_context = {}
        for k, v in context.items():
            if k == "disease":
                cleaned_context[k] = v  # Keep even if None
            elif v is not None:
                cleaned_context[k] = v
                
        return cleaned_context
    
    def _extract_from_message(self, message: str) -> Dict[str, Any]:
        """Extract insurance context from user message using pattern matching"""
        context = {}
        
        # Extract farmer name patterns
        farmer_patterns = [
            r"(?:my name is|i am|farmer|i'm)\s+([a-zA-Z\s]+)",
            r"farmer\s+([a-zA-Z\s]+)",
            r"name:\s*([a-zA-Z\s]+)"
        ]
        
        for pattern in farmer_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                name = match.group(1).strip().title()
                if len(name) > 2:  # Reasonable name length
                    context["farmer_name"] = name
                    break
        
        # Extract area patterns
        area_patterns = [
            r"(\d+(?:\.\d+)?)\s*hectares?",
            r"(\d+(?:\.\d+)?)\s*ha\b",
            r"area.*?(\d+(?:\.\d+)?)",
            r"(\d+(?:\.\d+)?)\s*acres?"  # Convert acres to hectares if needed
        ]
        
        for pattern in area_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                area = float(match.group(1))
                # Convert acres to hectares if the pattern mentions acres
                if "acre" in pattern:
                    area = area * 0.4047  # 1 acre = 0.4047 hectares
                context["area_hectare"] = area
                break
        
        # Extract crop type if not already present - try common crops first
        common_crops = ["rice", "wheat", "corn", "maize", "cotton", "sugarcane", "soybean", "tomato", 
                       "potato", "onion", "garlic", "chili", "pepper", "cabbage", "carrot", "mustard",
                       "barley", "groundnut", "sesame", "sunflower", "jowar", "bajra"]
        
        # First try to match common crops directly
        for crop in common_crops:
            if crop in message:
                context["crop"] = crop.title()
                break
        else:
            # If no common crop found, try pattern matching
            crop_patterns = [
                r"(?:crop|plant|growing)\s+([a-zA-Z\s]+)",
                r"([a-zA-Z]+)\s+(?:crop|cultivation)",
                r"cultivating\s+([a-zA-Z\s]+)"
            ]
            
            for pattern in crop_patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    crop = match.group(1).strip().title()
                    if len(crop) > 2:
                        context["crop"] = crop
                        break
        
        return context
    
    def _check_required_context(self, context: Dict[str, Any]) -> List[str]:
        """Check for required context fields and return missing ones"""
        # Only essential fields are required - disease and farmer_name are optional
        required_fields = ["state", "area_hectare", "crop"]
        missing = []
        
        for field in required_fields:
            if not context.get(field):
                missing.append(field)
        
        return missing
    
    async def _prompt_for_missing_info(self, state: WorkflowState, missing_fields: List[str]) -> None:
        """Prompt user for missing information"""
        field_prompts = {
            "state": "your state or location",
            "area_hectare": "the area of your farm in hectares",
            "crop": "the type of crop you are growing"
        }
        
        if len(missing_fields) == 1:
            field = missing_fields[0]
            prompt = f"To help you with crop insurance, I need to know {field_prompts.get(field, field)}. Could you please provide this information?"
        else:
            field_list = [field_prompts.get(field, field) for field in missing_fields]
            if len(field_list) > 2:
                field_str = ", ".join(field_list[:-1]) + f", and {field_list[-1]}"
            else:
                field_str = " and ".join(field_list)
            prompt = f"To help you with crop insurance, I need the following information: {field_str}. Could you please provide these details?"
        
        add_message_to_state(state, "assistant", f"🏦 {prompt}")
    
    def _determine_insurance_action(self, state: WorkflowState, context: Dict[str, Any]) -> str:
        """Determine the appropriate insurance action based on user intent and context"""
        user_message = state.get("user_message", "").lower()
        user_intent = state.get("user_intent", {})
        
        # Check user intent first
        if user_intent.get("wants_insurance_premium"):
            return "calculate_premium"
        elif user_intent.get("wants_insurance_companies"):
            return "get_companies"
        elif user_intent.get("wants_insurance_recommendation"):
            return "recommend"
        
        # Analyze message content
        if any(word in user_message for word in ["premium", "cost", "price", "calculate", "how much"]):
            return "calculate_premium"
        elif any(word in user_message for word in ["companies", "insurer", "provider", "list"]):
            return "get_companies"
        elif any(word in user_message for word in ["recommend", "suggest", "advice", "help", "what should"]):
            return "recommend"
        
        # Default to recommendation if we have disease context
        if context.get("disease"):
            return "recommend"
        
        # Fallback to premium calculation
        return "calculate_premium"
    
    async def _execute_insurance_operation(self, state: WorkflowState, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the insurance operation using the insurance tool"""
        try:
            insurance_tool = self.tools.get("insurance")
            if not insurance_tool:
                return {"error": "Insurance tool not available"}
            
            # Prepare tool input
            tool_input = {
                "action": action,
                "session_id": state.get("session_id", "unknown"),
                **context
            }
            
            add_message_to_state(
                state,
                "assistant",
                f"🏦 Processing your insurance request... This may take a moment."
            )
            
            # Execute tool
            result = await insurance_tool._arun(mlflow_manager=self.mlflow_manager, **tool_input)
            return result
            
        except Exception as e:
            logger.error(f"Error executing insurance operation: {e}")
            return {"error": f"Insurance operation failed: {str(e)}"}
    
    def _store_insurance_results(self, state: WorkflowState, action: str, result: Dict[str, Any]) -> None:
        """Store insurance operation results in state"""
        if action == "calculate_premium":
            state["insurance_premium_details"] = result
        elif action == "get_companies":
            state["insurance_companies"] = [result]  # Wrap in list for consistency
        elif action == "recommend":
            state["insurance_recommendations"] = result
        elif action == "generate_certificate":
            state["insurance_certificate"] = result
        
        # Store farmer information if extracted
        if result.get("farmer_name"):
            state["farmer_name"] = result["farmer_name"]
        if result.get("area_hectare"):
            state["area_hectare"] = result["area_hectare"]
    
    async def _provide_insurance_response(self, state: WorkflowState, action: str, result: Dict[str, Any]) -> None:
        """Provide appropriate response to user based on insurance operation result"""
        try:
            if action == "calculate_premium":
                premium_text = result.get("premium_details", "Premium calculation completed")
                message = f"🏦 **Insurance Premium Calculation**\n\n{premium_text}"
                
            elif action == "get_companies":
                companies_text = result.get("companies", "Insurance companies information retrieved")
                message = f"🏦 **Available Insurance Companies**\n\n{companies_text}"
                
            elif action == "recommend":
                recommendation_text = result.get("recommendation_text", "")
                
                if result.get("pdf_generated"):
                    message = f"🏦 **Insurance Recommendation**\n\n{recommendation_text}\n\n📄 A detailed insurance recommendation PDF has been generated for you."
                else:
                    message = f"🏦 **Insurance Recommendation**\n\n{recommendation_text}"
                    
                # Add crop and disease specific information
                if result.get("crop") and result.get("disease"):
                    message += f"\n\n**Coverage Details:**\n- Crop: {result['crop']}\n- Disease Risk: {result['disease']}\n- Coverage Area: {result.get('area_hectare', 'N/A')} hectares"
                
            else:
                message = f"🏦 Insurance operation '{action}' completed successfully."
            
            add_message_to_state(state, "assistant", message)
            
        except Exception as e:
            logger.error(f"Error providing insurance response: {e}")
            add_message_to_state(state, "assistant", "🏦 Insurance operation completed, but there was an issue formatting the response.")
    
    def _determine_next_action(self, state: WorkflowState, action: str, result: Dict[str, Any]) -> str:
        """Determine the next workflow action after insurance operation"""
        # Keep it simple - insurance node should focus only on insurance logic
        # Let the workflow manager and followup node handle complex routing decisions
        
        # For insurance recommendations, stay in followup for user to decide next steps
        if action == "recommend" and result.get("success"):
            return "followup"
        
        # For all other insurance operations, default to followup
        # The followup node will analyze user intent and route appropriately
        return "followup"
