"""
Insurance Node for FSM Agent workflow
Handles crop insurance operations and context extraction
"""

import logging
from typing import Dict, Any, Optional, List
import re
import json

from langchain.prompts import ChatPromptTemplate
from .base_node import BaseNode
from ..workflow_state import WorkflowState, add_message_to_state, set_error, clear_error

logger = logging.getLogger(__name__)


class InsuranceNode(BaseNode):
    """Insurance node - handles crop insurance operations and context gathering"""
    
    # ChatPromptTemplate for insurance action disambiguation
    INSURANCE_ACTION_PROMPT = ChatPromptTemplate.from_template("""
You are an expert insurance analyst. Analyze the user's message and determine whether they want to:

1. **CALCULATE_PREMIUM** - They want to know the cost/price/premium of insurance
2. **GENERATE_CERTIFICATE** - They want to buy/purchase insurance or generate a certificate
3. **GET_COMPANIES** - They want to know about insurance companies
4. **RECOMMEND** - They want insurance recommendations

CONTEXT:
- Crop: {crop}
- Area: {area_hectare} hectares
- State: {state}
- User Message: "{user_message}"

EXAMPLES FOR CALCULATE_PREMIUM:
- "Help me with insurance premium cost for my farm."
- "What is the cost of premium for my potato farm of 1 acre?"
- "How much will it cost me to buy insurance for my tomato farm?"
- "What's the insurance premium for wheat?"
- "Calculate insurance cost for my crops"
- "Show me premium rates"

EXAMPLES FOR GENERATE_CERTIFICATE:
- "Help me buy insurance for this premium."
- "Help me with buying insurance for my crop."
- "Buy crop insurance for me with this premium for my farm."
- "I am fine with purchasing this insurance at this premium."
- "Generate insurance certificate for my farm"
- "I want to purchase this insurance"
- "Apply for insurance coverage"
- "Complete my insurance purchase"

EXAMPLES FOR GET_COMPANIES:
- "Which insurance companies are available?"
- "Show me insurance providers in my area"
- "List insurance companies"

EXAMPLES FOR RECOMMEND:
- "What insurance should I get for my diseased crops?"
- "Recommend insurance for my farm"
- "Suggest the best insurance option"

CRITICAL DISAMBIGUATION RULES:
1. If the message contains words like "cost", "price", "premium", "how much", "calculate" WITHOUT purchase intent → CALCULATE_PREMIUM
2. If the message contains "buy", "purchase", "apply", "generate certificate", "I want to purchase" → GENERATE_CERTIFICATE  
3. If the message asks about "companies", "providers", "insurers" → GET_COMPANIES
4. If the message asks for "recommend", "suggest", "what should I", "best option" → RECOMMEND
5. When in doubt between CALCULATE_PREMIUM and GENERATE_CERTIFICATE:
   - "How much does it cost to buy insurance?" → CALCULATE_PREMIUM (asking about cost)
   - "Buy insurance with this cost" → GENERATE_CERTIFICATE (ready to purchase)

Respond with ONLY a JSON object:
{{
    "action": "calculate_premium|generate_certificate|get_companies|recommend",
    "confidence": 0.95,
    "reasoning": "Brief explanation of why you chose this action based on the key words and context"
}}
""")
    
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
        session_id = state['session_id']
        user_message = state.get("user_message", "")
        
        logger.info(f"Insurance request detected for session {session_id}")
        
        # Infinite loop prevention: Check if we've processed this exact message recently
        last_insurance_message = state.get("last_insurance_message")
        insurance_action_count = state.get("insurance_action_count", 0)
        
        if last_insurance_message == user_message:
            insurance_action_count += 1
            logger.warning(f"⚠️ Same message processed {insurance_action_count} times: '{user_message[:50]}...'")
            
            if insurance_action_count >= 3:  # Changed from > 2 to >= 3
                logger.error(f"❌ Infinite loop detected! Stopping after {insurance_action_count} attempts")
                add_message_to_state(state, "assistant", 
                    "🏦 I'm having trouble processing your request. Could you please rephrase what you'd like to do with insurance?")
                state["stream_immediately"] = True
                state["next_action"] = "await_user_input"
                state["requires_user_input"] = True
                # Reset the loop tracking
                state["insurance_action_count"] = 0
                state["last_insurance_message"] = None
                return state
        else:
            insurance_action_count = 1
        
        # Update tracking
        state["last_insurance_message"] = user_message
        state["insurance_action_count"] = insurance_action_count
        
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
            
            # If LLM analysis is needed, perform it
            if action == "llm_analysis_needed":
                logger.info(f"🤖 Performing LLM-based insurance action analysis...")
                action = await self._determine_insurance_action_with_llm(state, insurance_context)
                logger.info(f"🎯 Final action determined: {action}")
            
            # Execute insurance operation
            result = await self._execute_insurance_operation(state, action, insurance_context)
            
            if result and not result.get("error"):
                # Clear any previous error state since this operation succeeded
                clear_error(state)
                
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
        state["stream_immediately"] = True  # Stream missing info request immediately
    
    async def _determine_insurance_action_with_llm(self, state: WorkflowState, context: Dict[str, Any]) -> str:
        """Use LLM to determine the appropriate insurance action with high precision"""
        user_message = state.get("user_message", "")
        
        try:
            # Prepare context for LLM
            crop = context.get("crop", "unknown")
            area_hectare = context.get("area_hectare", "unknown")
            state_location = context.get("state", "unknown")
            
            # Format the prompt with context
            formatted_prompt = self.INSURANCE_ACTION_PROMPT.format_messages(
                user_message=user_message,
                crop=crop,
                area_hectare=area_hectare,
                state=state_location
            )
            
            # Get LLM response
            response = await self.llm.ainvoke(formatted_prompt)
            response_text = response.content.strip()
            
            logger.info(f"🔍 LLM Insurance Action Analysis: {response_text}")
            
            # Parse JSON response
            try:
                parsed_response = json.loads(response_text)
                action = parsed_response.get("action", "").lower()
                confidence = parsed_response.get("confidence", 0.0)
                reasoning = parsed_response.get("reasoning", "")
                
                logger.info(f"🎯 LLM determined action: {action} (confidence: {confidence})")
                logger.info(f"📝 Reasoning: {reasoning}")
                
                # Map action to our internal action names
                action_mapping = {
                    "calculate_premium": "calculate_premium",
                    "generate_certificate": "generate_certificate", 
                    "get_companies": "get_companies",
                    "recommend": "recommend"
                }
                
                if action in action_mapping:
                    return action_mapping[action]
                else:
                    logger.warning(f"⚠️ Unknown action from LLM: {action}, using fallback")
                    return self._fallback_action_determination(user_message, context)
                    
            except json.JSONDecodeError as e:
                logger.error(f"❌ Failed to parse LLM response as JSON: {e}")
                logger.error(f"Raw response: {response_text}")
                return self._fallback_action_determination(user_message, context)
                
        except Exception as e:
            logger.error(f"❌ LLM action determination failed: {e}")
            return self._fallback_action_determination(user_message, context)
    
    def _fallback_action_determination(self, user_message: str, context: Dict[str, Any]) -> str:
        """Fallback action determination using refined keyword analysis"""
        message_lower = user_message.lower()
        
        # PRIORITY 1: Strong purchase indicators (highest priority)
        strong_purchase_phrases = [
            "buy insurance for this premium", "buy insurance with this premium",
            "buy crop insurance for me with this premium",
            "i am fine with purchasing", "i want to purchase",
            "purchase this insurance", "complete purchase", "proceed with purchase",
            "generate certificate", "generate insurance certificate"
        ]
        
        for phrase in strong_purchase_phrases:
            if phrase in message_lower:
                logger.info(f"🎯 Fallback detected STRONG PURCHASE intent: '{phrase}'")
                return "generate_certificate"
        
        # PRIORITY 2: Purchase with context phrases
        purchase_with_context = [
            ("help me buy", "not asking cost"),
            ("help me with buying", "buying assistance"),
            ("buy crop insurance", "direct purchase request"),
            ("apply for insurance", "application for coverage"),
            ("complete my insurance purchase", "finalizing purchase")
        ]
        
        for phrase, context_note in purchase_with_context:
            if phrase in message_lower and "cost" not in message_lower and "how much" not in message_lower:
                logger.info(f"🎯 Fallback detected PURCHASE WITH CONTEXT: '{phrase}' ({context_note})")
                return "generate_certificate"
        
        # PRIORITY 3: Clear cost inquiry indicators (asking about price/cost)
        cost_inquiry_phrases = [
            "how much does it cost", "how much will it cost", "what is the cost",
            "what's the cost", "premium cost", "cost of premium", "insurance premium",
            "calculate premium", "show me premium rates", "what's the premium"
        ]
        
        for phrase in cost_inquiry_phrases:
            if phrase in message_lower:
                logger.info(f"🎯 Fallback detected COST INQUIRY intent: '{phrase}'")
                return "calculate_premium"
        
        # PRIORITY 4: Help/assistance phrases - need context analysis
        if "help me" in message_lower:
            if any(word in message_lower for word in ["buy", "purchase", "apply", "get insurance"]) and "cost" not in message_lower:
                logger.info(f"🎯 Fallback: Help with purchase/buying detected")
                return "generate_certificate"
            elif any(word in message_lower for word in ["cost", "premium", "price", "how much"]):
                logger.info(f"🎯 Fallback: Help with cost inquiry detected")
                return "calculate_premium"
        
        # PRIORITY 5: Company inquiry
        if any(phrase in message_lower for phrase in ["insurance companies", "providers", "insurers", "list companies", "which companies"]):
            logger.info(f"🎯 Fallback detected COMPANIES intent")
            return "get_companies"
        
        # PRIORITY 6: Recommendation request
        if any(word in message_lower for word in ["recommend", "suggest", "what should i", "best option", "advice"]):
            logger.info(f"🎯 Fallback detected RECOMMENDATION intent")
            return "recommend"
        
        # PRIORITY 7: Disease context defaults to recommendation
        if context.get("disease"):
            logger.info(f"🎯 Fallback: Disease context detected, recommending insurance")
            return "recommend"
        
        # PRIORITY 8: Default fallback - analyze remaining patterns
        if any(word in message_lower for word in ["buy", "purchase", "apply", "get", "obtain"]) and "cost" not in message_lower:
            logger.info(f"🎯 Fallback: Purchase-related keywords without cost inquiry")
            return "generate_certificate"
        elif any(word in message_lower for word in ["cost", "price", "premium", "how much", "calculate"]):
            logger.info(f"🎯 Fallback: Cost-related keywords detected")
            return "calculate_premium"
        
        # Final default
        logger.info(f"🎯 Fallback: Final default to premium calculation")
        return "calculate_premium"
    
    def _determine_insurance_action(self, state: WorkflowState, context: Dict[str, Any]) -> str:
        """Determine the appropriate insurance action based on user intent and context"""
        user_intent = state.get("user_intent", {})
        
        # First check explicit user intent from initial node (highest priority)
        if user_intent.get("wants_insurance_premium"):
            logger.info(f"🎯 Explicit intent: wants_insurance_premium")
            return "calculate_premium"
        elif user_intent.get("wants_insurance_companies"):
            logger.info(f"🎯 Explicit intent: wants_insurance_companies")
            return "get_companies"
        elif user_intent.get("wants_insurance_recommendation"):
            logger.info(f"🎯 Explicit intent: wants_insurance_recommendation")
            return "recommend"
        elif user_intent.get("wants_insurance_purchase"):
            logger.info(f"🎯 Explicit intent: wants_insurance_purchase")
            return "generate_certificate"
        
        # If no explicit intent, use LLM-based analysis
        logger.info(f"🤔 No explicit intent detected, using LLM analysis...")
        # Note: This will be called asynchronously in the main flow
        return "llm_analysis_needed"
    
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
            state["stream_immediately"] = True  # Stream processing status immediately
            
            # Execute tool with tracking
            import time
            tool_start_time = time.time()
            tool_success = True
            
            try:
                result = await insurance_tool._arun(mlflow_manager=self.mlflow_manager, **tool_input)
                return result
            except Exception as tool_error:
                tool_success = False
                raise tool_error
            finally:
                tool_duration = time.time() - tool_start_time
                self.record_tool_usage("insurance_tool", tool_duration, tool_success)
            
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
            
            elif action == "generate_certificate":
                if result.get("success"):
                    farmer_name = result.get("farmer_name", "Farmer")
                    crop = result.get("crop", "your crop")
                    policy_id = result.get("policy_id", "N/A")
                    
                    message = f"🏦 **Insurance Policy Certificate Generated Successfully! 🎉**\n\n"
                    message += f"**Farmer:** {farmer_name}\n"
                    message += f"**Crop:** {crop.title()}\n"
                    message += f"**Policy ID:** {policy_id}\n"
                    message += f"**Coverage Area:** {result.get('area_hectare', 'N/A')} hectares\n"
                    
                    # Include premium details if available
                    if result.get("premium_details"):
                        message += f"\n**Premium Details:**\n{result['premium_details']}"
                    
                    if result.get("pdf_generated"):
                        message += f"\n\n📄 **Your insurance certificate PDF has been generated and is ready for download.**"
                        if result.get("certificate_details"):
                            message += f"\n\n**Certificate Details:**\n{result['certificate_details']}"
                    else:
                        # Fallback if PDF generation failed
                        message += f"\n\n⚠️ Certificate details processed, but PDF generation is temporarily unavailable."
                        if result.get("certificate_details"):
                            message += f"\n\n**Certificate Information:**\n{result['certificate_details']}"
                else:
                    error_msg = result.get("error", "Certificate generation failed")
                    message = f"🏦 **Certificate Generation Issue**\n\n❌ {error_msg}"
                    
                    # Provide guidance on what information might be missing
                    if "required" in error_msg.lower() or "missing" in error_msg.lower():
                        message += f"\n\n💡 **To generate your insurance certificate, we need:**\n"
                        message += f"• Complete farmer information\n"
                        message += f"• Selected insurance company details\n"
                        message += f"• Premium calculation results\n"
                        message += f"• Policy terms confirmation\n"
                        message += f"\nPlease ensure you have completed premium calculation first."
                
            else:
                message = f"🏦 Insurance operation '{action}' completed successfully."
            
            add_message_to_state(state, "assistant", message)
            state["stream_immediately"] = True  # Stream insurance responses immediately
            
        except Exception as e:
            logger.error(f"Error providing insurance response: {e}")
            add_message_to_state(state, "assistant", "🏦 Insurance operation completed, but there was an issue formatting the response.")
            state["stream_immediately"] = True  # Stream error messages too
    
    def _determine_next_action(self, state: WorkflowState, action: str, result: Dict[str, Any]) -> str:
        """Determine the next workflow action after insurance operation"""
        
        # Mark insurance operation as completed to prevent infinite loops
        state["insurance_operation_completed"] = True
        state["last_completed_insurance_action"] = action
        
        # Clear the action count after successful completion
        state["insurance_action_count"] = 0
        
        logger.info(f"✅ Insurance operation '{action}' completed successfully, routing to completed")
        
        # Route to completed node to show completion message and wait for new user input
        # This prevents the system from immediately trying to process the same message again
        return "completed"
