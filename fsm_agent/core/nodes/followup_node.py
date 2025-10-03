"""
Followup Node for FSM Agent workflow
Handles additional questions and navigation using LLM-based intent analysis
"""

import logging
import re
from typing import Dict, Any

from .base_node import BaseNode

# Import response configuration and metrics (with error handling)
logger = logging.getLogger(__name__)

try:
    from ..response_config import response_config, ResponseType
    RESPONSE_CONFIG_AVAILABLE = True
except ImportError:
    RESPONSE_CONFIG_AVAILABLE = False
    logger.warning("Response configuration not available")

try:
    import sys
    import os
    # Add project root to Python path for absolute imports
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from observability.metrics import get_metrics
    METRICS_AVAILABLE = True  
except ImportError:
    METRICS_AVAILABLE = False
    logger.warning("Metrics not available")

try:
    from ..workflow_state import WorkflowState, add_message_to_state, set_error, mark_complete
    from ...tools.attention_overlay_tool import AttentionOverlayTool
except ImportError:
    from ..workflow_state import WorkflowState, add_message_to_state, set_error, mark_complete
    from ...tools.attention_overlay_tool import AttentionOverlayTool


class FollowupNode(BaseNode):
    """Followup node - handles additional questions and navigation using LLM-based intent analysis"""
    
    @property
    def node_name(self) -> str:
        return "followup"
    
    async def execute(self, state: WorkflowState) -> WorkflowState:
        """
        Execute followup node logic
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        self.update_node_state(state)
        
        try:
            # FIXED: Check for goodbye intent FIRST in follow-up conversations
            if await self._detect_goodbye_intent(state):
                logger.info("👋 Goodbye intent detected in followup - routing to session_end")
                state["next_action"] = "session_end"
                return state
            # CRITICAL FIX: Check if we just completed a workflow step to prevent infinite loops
            previous_node = state.get("previous_node", "")
            classification_results = state.get("classification_results")
            prescription_data = state.get("prescription_data")
            
            # If we just completed classification and have results, don't re-classify
            if previous_node == "classifying" and classification_results:
                logger.info(f"🚫 Preventing infinite loop: Classification just completed, showing results instead of re-classifying")
                self._handle_classification_complete_followup(state)
                
            # If we just completed prescription and have data, don't re-prescribe  
            elif previous_node == "prescribing" and prescription_data:
                logger.info(f"🚫 Preventing infinite loop: Prescription just completed, showing results instead of re-prescribing")
                self._handle_prescription_complete_followup(state)
                
            # If insurance node just prompted for missing info, handle appropriately
            elif previous_node == "insurance" and state.get("requires_user_input"):
                logger.info(f"🚫 Preventing infinite loop: Insurance node just prompted for missing info")
                await self._handle_insurance_missing_info_followup(state)
                
            # If we just completed insurance operation and have results, don't re-query
            elif previous_node == "insurance" and (state.get("insurance_premium_details") or state.get("insurance_recommendations")):
                logger.info(f"🚫 Preventing infinite loop: Insurance operation just completed, showing results instead of re-querying")
                self._handle_insurance_complete_followup(state)
                
            else:
                # Normal flow: analyze user intent for new requests
                logger.info(f"📋 Normal followup: Analyzing user intent (previous_node: {previous_node})")
                followup_intent = await self._analyze_followup_intent(state)
                
                # Route based on LLM-determined intent
                if followup_intent["action"] == "classify":
                    await self._handle_classify_action(state)
                        
                elif followup_intent["action"] == "prescribe":
                    await self._handle_prescribe_action(state)
                        
                        
                elif followup_intent["action"] == "attention_overlay":
                    await self._handle_attention_overlay_action(state, followup_intent)
                        
                elif followup_intent["action"] == "restart":
                    self._handle_restart_action(state)
                    
                elif followup_intent["action"] == "complete":
                    await self._handle_complete_action(state)
                    
                elif followup_intent["action"] == "direct_response":
                    self._handle_direct_response_action(state, followup_intent)
                    
                elif followup_intent["action"] == "insurance":
                    await self._handle_insurance_action(state)
                    
                elif followup_intent["action"] == "out_of_scope":
                    self._handle_out_of_scope_action(state, followup_intent)
                    
                else:
                    self._handle_general_help_action(state)
            
        except Exception as e:
            logger.error(f"Error in followup node: {str(e)}", exc_info=True)
            set_error(state, f"Followup error: {str(e)}")
            state["next_action"] = "error"
        
        return state
    
    async def _handle_classify_action(self, state: WorkflowState) -> None:
        """Handle classification action - can invoke tool directly or route to classifier node"""
        if state.get("user_image"):
            # Image available - directly invoke classification tool in followup context
            logger.info("🔍 Invoking classification tool directly from followup node")
            
            try:
                # Run classification tool
                classification_tool = self.tools["classification"]
                
                # Prepare classification input
                classification_input = {
                    "image_b64": state["user_image"],  # FIX: Use correct field name
                    "plant_type": state.get("plant_type"),
                    "location": state.get("location"),
                    "season": state.get("season"),
                    "growth_stage": state.get("growth_stage"),
                    "session_id": state.get("session_id", "unknown")  # ADD SESSION ID FOR MLFLOW
                }
                
                # Run classification
                classification_result = await classification_tool._arun(mlflow_manager=self.mlflow_manager, **classification_input)
                
                if classification_result and not classification_result.get("error"):
                    # Store classification results
                    state["classification_results"] = classification_result
                    state["disease_name"] = classification_result.get("disease_name")
                    state["confidence"] = classification_result.get("confidence", 0)
                    
                    # Add classification message to conversation
                    classification_msg = self._format_classification_message(classification_result)
                    add_message_to_state(state, "assistant", classification_msg)
                    
                    # Store response for streaming
                    state["assistant_response"] = classification_msg
                    
                    # GENERIC ARCHITECTURAL FIX: Set streaming metadata for modular duplicate prevention
                    state["response_status"] = "final"  # This is the enhanced, final version ready for streaming
                    state["stream_immediately"] = True  # Node indicates immediate streaming needed
                    state["stream_in_state_update"] = False  # Don't include in state_update events
                    
                    # Complete the classification within followup
                    state["next_action"] = "await_user_input"
                    state["requires_user_input"] = True
                    
                    logger.info(f"✅ Classification completed within followup node: {classification_result.get('disease_name')}")
                else:
                    # Classification failed - route to classifier node for error handling
                    logger.warning("⚠️ Classification failed in followup, routing to classifier node")
                    state["next_action"] = "classify"
                    
            except Exception as e:
                logger.error(f"❌ Classification error in followup node: {str(e)}")
                # Fall back to routing to classifier node
                state["next_action"] = "classify"
        else:
            state["next_action"] = "request_image"
            add_message_to_state(state, "assistant", "📸 Please upload an image of the plant leaf you'd like me to analyze.")
            state["requires_user_input"] = True
    
    async def _handle_prescribe_action(self, state: WorkflowState) -> None:
        """Handle prescription action - always route to prescribing node, let it handle classification checks"""
        logger.info("💊 Routing to prescribing node for prescription processing")
        state["next_action"] = "prescribe"
    
    async def _handle_attention_overlay_action(self, state: WorkflowState, followup_intent: Dict[str, Any]) -> None:
        """Handle attention overlay action"""
        attention_tool = self.tools["attention_overlay"]
        attention_tool.set_state(state)
        
        try:
            overlay_response = await attention_tool.arun({
                "request_type": followup_intent.get("overlay_type", "show_overlay"),
                "format_preference": "base64"
            })
            add_message_to_state(state, "assistant", overlay_response)
            state["next_action"] = "general_help"
            state["requires_user_input"] = True
        except Exception as e:
            logger.error(f"Error retrieving attention overlay: {str(e)}")
            add_message_to_state(state, "assistant", "❌ Sorry, I encountered an error while trying to retrieve the attention overlay. Please try again or start a new classification.")
            state["next_action"] = "general_help"
    
    def _handle_restart_action(self, state: WorkflowState) -> None:
        """Handle restart action"""
        state["next_action"] = "restart"
        add_message_to_state(state, "assistant", "🔄 Starting a new diagnosis. Please share your plant image and any additional context.")
        state["requires_user_input"] = True
    
    async def _handle_complete_action(self, state: WorkflowState) -> None:
        """Handle completion action"""
        # Check if user wants to actually end the session
        user_wants_to_end = await self._detect_goodbye_intent(state)
        if user_wants_to_end:
            state["next_action"] = "session_end"  # Route to session_end node instead of complete
            # The session_end node will handle the farewell message
        else:
            # User reached completion but didn't say goodbye, show ongoing support
            self._show_ongoing_support(state)
    
    async def _handle_insurance_action(self, state: WorkflowState) -> None:
        """Handle insurance action - route to insurance node with proper intent analysis"""
        logger.info("🏦 Analyzing specific insurance intent for routing to insurance node")
        
        # Perform detailed insurance intent analysis
        user_message = state.get("user_message", "")
        insurance_intent = await self._analyze_insurance_sub_intent(user_message)
        
        # Set the detailed user_intent for the insurance node
        state["user_intent"] = insurance_intent
        state["next_action"] = "insurance"
        
        logger.info(f"🎯 Insurance sub-intent determined: {insurance_intent}")
    
    async def _analyze_insurance_sub_intent(self, user_message: str) -> Dict[str, Any]:
        """Analyze specific insurance intent to distinguish between premium, purchase, coverage, etc."""
        try:
            prompt = f"""You are an expert insurance intent analyzer. Analyze this user message to determine their specific insurance intent.

User message: "{user_message}"

Determine what the user specifically wants regarding insurance:

EXAMPLES FOR DIFFERENT INTENTS:

PREMIUM CALCULATION (wants_insurance_premium: true):
- "Help me with insurance premium cost for my farm"  
- "What is the cost of premium for my potato farm?"
- "How much will insurance cost for my crops?"
- "Calculate insurance premium for wheat"
- "Show me premium rates"

PURCHASE/APPLICATION (wants_insurance_purchase: true):  
- "Help me apply for crop insurance"
- "Help me buy insurance for this premium"
- "Buy crop insurance for me with this premium"
- "I want to purchase crop insurance"
- "Generate insurance certificate"
- "Apply for insurance coverage"
- "I am fine with purchasing this insurance"

COMPANY INFORMATION (wants_insurance_companies: true):
- "Which insurance companies are available?"
- "Show me insurance providers"
- "List insurance companies in my state"

COVERAGE DETAILS (wants_insurance_coverage: true):
- "What does insurance cover?"
- "Tell me about insurance benefits"
- "What are the coverage details?"

RECOMMENDATION (wants_insurance_recommendation: true):
- "Recommend best insurance for my crops"
- "Suggest insurance policy for diseased crops"
- "Which insurance should I choose?"

CRITICAL RULES:
1. "Apply for insurance" = PURCHASE intent (wants_insurance_purchase: true)
2. "Buy insurance" = PURCHASE intent (wants_insurance_purchase: true)  
3. "Insurance cost/premium" = PREMIUM intent (wants_insurance_premium: true)
4. "Generate certificate" = PURCHASE intent (wants_insurance_purchase: true)
5. If message contains both cost and purchase terms, prioritize the main intent

Respond with ONLY a JSON object:
{{
    "wants_insurance": true,
    "wants_insurance_premium": false,
    "wants_insurance_companies": false, 
    "wants_insurance_recommendation": false,
    "wants_insurance_purchase": false,
    "wants_insurance_coverage": false
}}"""

            response = await self.llm.ainvoke(prompt)
            response_text = response.content.strip()
            
            logger.info(f"🔍 LLM insurance sub-intent analysis: {response_text}")
            
            # Parse JSON response
            import json
            try:
                parsed_intent = json.loads(response_text)
                
                # Validate the response has required fields
                if not isinstance(parsed_intent, dict) or not parsed_intent.get("wants_insurance"):
                    raise ValueError("Invalid insurance intent response")
                
                return parsed_intent
                
            except json.JSONDecodeError:
                logger.error(f"Failed to parse insurance sub-intent JSON: {response_text}")
                return self._fallback_insurance_sub_intent(user_message)
                
        except Exception as e:
            logger.error(f"LLM insurance sub-intent analysis failed: {e}")
            return self._fallback_insurance_sub_intent(user_message)
    
    def _fallback_insurance_sub_intent(self, user_message: str) -> Dict[str, Any]:
        """Fallback insurance sub-intent analysis using keyword patterns"""
        message_lower = user_message.lower()
        
        # Strong purchase indicators
        purchase_phrases = [
            "apply for insurance", "apply for crop insurance", "buy insurance", 
            "purchase insurance", "generate certificate", "i want to purchase",
            "i want to buy", "help me apply", "help me buy"
        ]
        
        for phrase in purchase_phrases:
            if phrase in message_lower:
                logger.info(f"🎯 Fallback: Purchase intent detected - '{phrase}'")
                return {
                    "wants_insurance": True,
                    "wants_insurance_premium": False,
                    "wants_insurance_companies": False,
                    "wants_insurance_recommendation": False, 
                    "wants_insurance_purchase": True,
                    "wants_insurance_coverage": False
                }
        
        # Premium calculation indicators  
        if any(word in message_lower for word in ["premium", "cost", "price", "how much", "calculate"]):
            logger.info(f"🎯 Fallback: Premium intent detected")
            return {
                "wants_insurance": True,
                "wants_insurance_premium": True,
                "wants_insurance_companies": False,
                "wants_insurance_recommendation": False,
                "wants_insurance_purchase": False,
                "wants_insurance_coverage": False
            }
        
        # Company inquiry
        if any(word in message_lower for word in ["companies", "providers", "insurers"]):
            logger.info(f"🎯 Fallback: Companies intent detected")
            return {
                "wants_insurance": True,
                "wants_insurance_premium": False,
                "wants_insurance_companies": True,
                "wants_insurance_recommendation": False,
                "wants_insurance_purchase": False, 
                "wants_insurance_coverage": False
            }
        
        # Coverage inquiry  
        if any(word in message_lower for word in ["cover", "coverage", "benefits", "what does"]):
            logger.info(f"🎯 Fallback: Coverage intent detected") 
            return {
                "wants_insurance": True,
                "wants_insurance_premium": False,
                "wants_insurance_companies": False,
                "wants_insurance_recommendation": False,
                "wants_insurance_purchase": False,
                "wants_insurance_coverage": True
            }
        
        # Default fallback to recommendation
        logger.info(f"🎯 Fallback: Default to recommendation intent")
        return {
            "wants_insurance": True,
            "wants_insurance_premium": False,
            "wants_insurance_companies": False, 
            "wants_insurance_recommendation": True,
            "wants_insurance_purchase": False,
            "wants_insurance_coverage": False
        }
    
    def _handle_direct_response_action(self, state: WorkflowState, followup_intent: Dict[str, Any]) -> None:
        """Handle direct response action"""
        # GENERIC ARCHITECTURAL FIX: Use metadata to control streaming behavior
        llm_response = followup_intent.get("response", "I'm here to help! What would you like to know?")
        
        # Clear any previous assistant_response to prevent old data accumulation
        state["assistant_response"] = llm_response.strip()
        
        # GENERIC: Mark response as intermediate - let completed node enhance it
        state["response_status"] = "intermediate"  # Workflow will skip streaming this
        state["stream_immediately"] = False  # Let completed node handle final streaming
        
        # Add clean response to conversation history
        add_message_to_state(state, "assistant", llm_response.strip())
        
        # Route to completion to show enhanced response
        state["next_action"] = "await_user_input"
        state["requires_user_input"] = True
    
    async def _handle_insurance_missing_info_followup(self, state: WorkflowState) -> None:
        """Handle followup after insurance node prompted for missing information"""
        user_message = state.get("user_message", "").lower()
        
        # Check if user provided missing insurance information
        missing_info_provided = False
        updated_context = {}
        
        # Extract crop information from user message
        common_crops = ["rice", "wheat", "corn", "maize", "cotton", "sugarcane", "soybean", "tomato", 
                       "potato", "onion", "garlic", "chili", "pepper", "cabbage", "carrot"]
        
        for crop in common_crops:
            if crop in user_message:
                updated_context["crop"] = crop.title()
                missing_info_provided = True
                break
        
        # Check for area/hectare information
        area_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:hectare|hectares|ha|acre|acres)', user_message)
        if area_match:
            area = float(area_match.group(1))
            # Convert acres to hectares if needed
            if 'acre' in user_message:
                area = area * 0.404686  # Convert acres to hectares
            updated_context["area_hectare"] = area
            missing_info_provided = True
        
        # Check for state/location information
        indian_states = ["andhra pradesh", "assam", "bihar", "gujarat", "haryana", "karnataka", 
                        "kerala", "madhya pradesh", "maharashtra", "punjab", "rajasthan", 
                        "tamil nadu", "uttar pradesh", "west bengal"]
        
        for state_name in indian_states:
            if state_name in user_message:
                updated_context["state"] = state_name.title()
                missing_info_provided = True
                break
        
        if missing_info_provided:
            # Update state with extracted information
            logger.info(f"🔄 Extracted missing insurance info: {updated_context}")
            try:
                for key, value in updated_context.items():
                    state[key] = value
                
                # Clear requires_user_input and route back to insurance
                state["requires_user_input"] = False
                state["next_action"] = "insurance"
            except Exception as e:
                logger.error(f"Error updating state with extracted info: {str(e)}")
                logger.error(f"State type: {type(state)}, Updated context: {updated_context}")
                # Fallback: analyze new intent instead
                followup_intent = await self._analyze_followup_intent(state)
                self._handle_direct_response_action(state, followup_intent)
            
        else:
            # User didn't provide missing info - analyze their new intent
            logger.info("📋 User didn't provide missing insurance info, analyzing new intent")
            followup_intent = await self._analyze_followup_intent(state)
            
            # Handle the new intent (don't force insurance)
            if followup_intent["action"] == "classify":
                await self._handle_classify_action(state)
            elif followup_intent["action"] == "prescribe":
                await self._handle_prescribe_action(state)
            elif followup_intent["action"] == "direct_response":
                self._handle_direct_response_action(state, followup_intent)
            else:
                # Default to general help if unclear
                self._handle_general_help_action(state)
            
            # Clear requires_user_input since we're handling their request
            state["requires_user_input"] = False
    
    def _handle_insurance_complete_followup(self, state: WorkflowState) -> None:
        """Handle followup after insurance operation completed successfully"""
        # Show the results without re-executing insurance
        insurance_premium = state.get("insurance_premium_details", {})
        insurance_recommendations = state.get("insurance_recommendations", {})
        
        if insurance_premium:
            # Premium was calculated - show completion message
            premium_amount = insurance_premium.get("total_premium", "N/A")
            crop = state.get("crop", state.get("plant_type", "crop"))
            response = f"✅ **Insurance Premium Calculated Successfully**\n\nYour {crop} insurance premium: ₹{premium_amount}\n\nWhat would you like to do next?"
            
        elif insurance_recommendations:
            # Recommendations were provided
            response = "✅ **Insurance Recommendations Ready**\n\nYour insurance recommendations are complete. What would you like to do next?"
            
        else:
            # Fallback message
            response = "✅ **Insurance Service Completed**\n\nYour insurance request has been processed. What would you like to do next?"
        
        state["assistant_response"] = response
        state["response_status"] = "final"
        state["stream_immediately"] = True
        state["stream_in_state_update"] = False
        
        add_message_to_state(state, "assistant", response)
        
        # Route to completion to show enhanced response  
        state["next_action"] = "completed"
        state["requires_user_input"] = False  # Clear the flag
    
    def _handle_out_of_scope_action(self, state: WorkflowState, followup_intent: Dict[str, Any]) -> None:
        """Handle out-of-scope questions in followup node"""
        
        # Record metrics if available
        if METRICS_AVAILABLE:
            try:
                metrics = get_metrics()
                scope_confidence = followup_intent.get("scope_confidence", 0.0)
                intent_confidence = followup_intent.get("confidence", 0.0)
                
                # Determine message category for metrics
                user_message = state.get("user_message", "").lower()
                if any(word in user_message for word in ["technology", "computer", "phone", "software"]):
                    category = "technology"
                elif any(word in user_message for word in ["medicine", "doctor", "health", "medical"]):
                    category = "medical"
                elif any(word in user_message for word in ["car", "vehicle", "transport"]):
                    category = "automotive"
                elif any(word in user_message for word in ["cooking", "recipe", "food"]):
                    category = "cooking"  
                elif any(word in user_message for word in ["weather", "temperature", "rain"]):
                    category = "weather"
                else:
                    category = "general"
                
                metrics.record_out_of_scope_request(
                    intent_type="non_agricultural_followup", 
                    user_message_category=category
                )
                metrics.record_intent_confidence("out_of_scope", scope_confidence)
                metrics.record_intent_confidence("followup_intent", intent_confidence)
                metrics.record_response_type_usage(ResponseType.OUT_OF_SCOPE.value, "followup")
                
            except Exception as e:
                logger.warning(f"Failed to record out-of-scope metrics in followup: {e}")
        
        # Generate appropriate response
        if RESPONSE_CONFIG_AVAILABLE:
            try:
                response = response_config.get_response(ResponseType.OUT_OF_SCOPE)
                logger.info(f"🚫 Generated out-of-scope response for followup non-agricultural question")
            except Exception as e:
                logger.warning(f"Failed to get response from config in followup: {e}")
                response = "I'm sorry, but I can only help with crop care and agricultural questions. Could you please ask me something related to plant diseases, farming, or crop management?"
        else:
            response = "I'm sorry, but I can only help with crop care and agricultural questions. Could you please ask me something related to plant diseases, farming, or crop management?"
        
        # Set state for completion  
        add_message_to_state(state, response, "assistant")
        state["assistant_response"] = response
        state["next_action"] = "completed"
        state["is_complete"] = True
        
        logger.info(f"🚫 Out-of-scope followup request handled. Confidence: {followup_intent.get('confidence', 0.0)}, Scope confidence: {followup_intent.get('scope_confidence', 0.0)}")
    
    def _handle_general_help_action(self, state: WorkflowState) -> None:
        """Handle general help action"""
        state["next_action"] = "general_help"
        help_message = """🤔 I can help you with:

• **New diagnosis** - Upload a new plant image
• **Review results** - Look at previous diagnosis or prescription
• **Show attention overlay** - See where the AI focused during diagnosis
• **Ask questions** - Any plant care related questions

What would you like to do next?"""
        
        add_message_to_state(state, "assistant", help_message)
        state["requires_user_input"] = True
    
    def _handle_classification_complete_followup(self, state: WorkflowState) -> None:
        """Handle followup after classification completes to prevent infinite loops"""
        classification_results = state.get("classification_results", {})
        disease_name = classification_results.get("disease", "Unknown")
        confidence = classification_results.get("confidence", 0)
        
        completion_msg = f"""✅ **Plant Disease Analysis Complete!**
        
🔬 **Diagnosis**: {disease_name}
📊 **Confidence**: {confidence:.0%}

What would you like to do next?
• **Get treatment recommendations** - I can suggest specific treatments
• **Ask questions** - Any questions about the diagnosis
• **Upload another image** - Analyze a different plant

What's your next step?"""
        
        add_message_to_state(state, "assistant", completion_msg)
        state["next_action"] = "completed"  # End workflow, wait for user's next choice
        state["requires_user_input"] = True
    
    def _handle_prescription_complete_followup(self, state: WorkflowState) -> None:
        """Handle followup after prescription completes to prevent infinite loops"""
        completion_msg = """✅ **Treatment Recommendations Complete!**
        
I've provided detailed treatment recommendations for your plant.

What would you like to do next?
• **Ask questions** - Any questions about the treatment plan
• **Get monitoring advice** - Learn how to track treatment progress
• **Upload another image** - Analyze a different plant

What's your next step?"""
        
        add_message_to_state(state, "assistant", completion_msg)
        state["next_action"] = "completed"  # End workflow, wait for user's next choice
        state["requires_user_input"] = True
    
    def _show_ongoing_support(self, state: WorkflowState) -> None:
        """Show ongoing support message"""
        state["next_action"] = "general_help"
        help_message = """🤔 I'm here to help with more questions! You can:

• **Upload new plant images** for diagnosis
• **Ask about treatment progress** and monitoring
• **Get seasonal care advice** and tips

What would you like to know more about?"""
        
        add_message_to_state(state, "assistant", help_message)
        state["requires_user_input"] = True
    
    async def _analyze_followup_intent(self, state: WorkflowState) -> Dict[str, Any]:
        """
        Analyze user's followup message to determine intent and action using LLM
        """
        try:
            user_message = state["user_message"]
            
            # Build context about current workflow state
            context_info = []
            if state.get("classification_results"):
                disease_name = state.get("disease_name", "Unknown")
                context_info.append(f"- Already diagnosed disease: {disease_name}")
            
            if state.get("prescription_data"):
                context_info.append(f"- Already have treatment recommendations")
            
            if state.get("insurance_recommendations"):
                context_info.append(f"- Already have insurance recommendations")
            
            if state.get("insurance_premium_details"):
                context_info.append(f"- Already calculated insurance premium")
                
            context_str = "\n".join(context_info) if context_info else "- No previous workflow steps completed"
            
            intent_prompt = self._build_followup_intent_prompt(user_message, context_str, state)
            
            # Get LLM response
            response = await self.llm.ainvoke(intent_prompt)
            response_text = response.content.strip()
            
            logger.debug(f"🧠 LLM followup intent analysis: {response_text}")
            
            # Parse JSON response  
            intent = self._parse_followup_intent_response(response_text, state)
            if intent:
                logger.info(f"🎯 LLM followup intent analysis: {intent}")
                return intent
                    
        except Exception as e:
            logger.error(f"❌ Error in LLM followup intent analysis: {e}")
        
        # Fallback to direct response
        return {
            "action": "direct_response",
            "response": "I'm here to help! What would you like to know about plant disease diagnosis or treatment?",
            "overlay_type": "",
            "confidence": 0.1
        }
    
    def _build_followup_intent_prompt(self, user_message: str, context_str: str, state: WorkflowState) -> str:
        """Build the followup intent analysis prompt"""
        return f"""You are analyzing a user's followup message in a comprehensive agricultural assistance system that provides:
- Plant disease diagnosis and classification
- Treatment recommendations and prescriptions  
- Crop insurance services (premium calculation, policy recommendations, company comparisons)
- General agricultural guidance

Current workflow context:
{context_str}

User's message: "{user_message}"

Analyze the user's intent and respond with ONLY a JSON object containing:
- action: One of ["classify", "prescribe", "insurance", "attention_overlay", "restart", "complete", "direct_response", "out_of_scope"]
- response: (string) If action is "direct_response", provide a helpful answer to their question. Otherwise, leave empty.
- overlay_type: (string) If action is "attention_overlay", specify "show_overlay" or "overlay_info". Otherwise, leave empty.
- confidence: (number 0-1) How confident you are in this classification.
- is_agriculture_related: (boolean) Is this question related to agriculture, farming, crops, plants, or agricultural business?
- scope_confidence: (number 0-1) How confident are you that this is agriculture-related (1=definitely agriculture, 0=definitely not agriculture)?

Action meanings:
- "classify": User wants disease diagnosis/classification
- "prescribe": User wants treatment recommendations, dosage info, application instructions  
- "insurance": User wants crop insurance services (premium calculation, recommendations, companies, coverage) - WE PROVIDE THESE SERVICES
- "attention_overlay": User wants to see diagnostic attention overlay/heatmap
- "restart": User wants to start over with new diagnosis
- "complete": User is done/saying goodbye
- "direct_response": Answer their question directly (for general agriculture questions, clarifications, etc.)
- "out_of_scope": Question is completely outside agricultural/farming domain (technology, medicine, entertainment, etc.)

Guidelines:
1. INSURANCE REQUESTS: If they ask about insurance, premium, coverage, policy, insurance cost, insurance companies - ALWAYS use "insurance" action (WE PROVIDE FULL INSURANCE SERVICES)
2. TREATMENT REQUESTS: If they ask about dosage, application, treatment instructions - use "prescribe" if no prescription exists, otherwise "direct_response" with detailed answer using available prescription data
3. CLASSIFICATION REQUESTS: If they ask about disease diagnosis, upload new image, identify disease - use "classify"
4. General agriculture questions (soil, weather, growing tips) - use "direct_response"  
5. Clarifications about previous results - use "direct_response"
6. Be flexible with natural language - "yes give me dosage" means they want prescription/dosage info
7. IMPORTANT: For insurance keywords (insurance, premium, coverage, cost, policy, companies), ALWAYS route to "insurance" - never use "direct_response"
8. SCOPE DETECTION: 
    - Use "out_of_scope" for questions about: technology, human medicine, entertainment, vehicles, cooking, general weather, etc.
    - is_agriculture_related=false and scope_confidence=0.1-0.3 for clearly non-agricultural topics
    - is_agriculture_related=true and scope_confidence=0.7-1.0 for agricultural topics
    - If out_of_scope, set confidence=0.9+ and response="" (let the system handle the standard response)

Current prescription data available: {bool(state.get("prescription_data"))}

Response (JSON only):"""
    
    def _parse_followup_intent_response(self, response_text: str, state: WorkflowState) -> Dict[str, Any]:
        """Parse the followup intent response"""
        try:
            import json
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                intent = json.loads(json_str)
                
                # Ensure required keys exist
                default_intent = {
                    "action": "direct_response",
                    "response": "I'm here to help! What would you like to know?",
                    "overlay_type": "",
                    "confidence": 0.5
                }
                default_intent.update(intent)
                
                # Special handling for prescription-related requests when we have prescription data
                user_message = state["user_message"]
                if (intent.get("action") == "prescribe" and 
                    state.get("prescription_data") and 
                    any(word in user_message.lower() for word in ["dosage", "dose", "application", "instructions", "how much", "how to"])):
                    
                    # Generate direct response with prescription data
                    dosage_info = self._generate_prescription_dosage_info(state)
                    default_intent["action"] = "direct_response"
                    default_intent["response"] = dosage_info
                
                return default_intent
                        
        except json.JSONDecodeError as e:
            logger.warning(f"🚨 Failed to parse JSON from LLM followup response: {e}")
            
        return None
    
    def _format_classification_message(self, classification_result: Dict[str, Any]) -> str:
        """Format classification result into user message"""
        disease_name = classification_result.get("disease_name", "Unknown Disease")
        confidence = classification_result.get("confidence", 0)
        description = classification_result.get("description", "")
        symptoms = classification_result.get("symptoms", [])
        
        message = f"🔬 **Analysis Complete!**\n\n"
        message += f"**Disease Identified:** {disease_name}\n"
        message += f"**Confidence:** {confidence:.1f}%\n\n"
        
        if description:
            message += f"**Description:** {description}\n\n"
        
        if symptoms:
            message += f"**Symptoms:** {', '.join(symptoms)}\n\n"
        
        message += "Would you like me to provide treatment recommendations for this condition?"
        
        return message
    
    
    def _generate_prescription_dosage_info(self, state: WorkflowState) -> str:
        """Generate dosage information from prescription data"""
        prescription_data = state.get("prescription_data", {})
        treatments = prescription_data.get("treatments", [])
        
        if treatments:
            dosage_info = f"""📋 **HOW TO USE YOUR MEDICINES**

💊 **STEP-BY-STEP INSTRUCTIONS**"""
            
            for i, treatment in enumerate(treatments, 1):
                treatment_name = treatment.get('name', 'Treatment')
                dosage_info += f"""

🔹 **MEDICINE #{i}: {treatment_name}**
• **How much to use:** {treatment.get('dosage', 'Follow bottle label')}
• **How to apply:** {treatment.get('application', 'Mix with water and spray')}
• **How often:** {treatment.get('frequency', 'Check medicine bottle')}
• **For how long:** {treatment.get('duration', 'Until plant gets better')}"""
            
            notes = prescription_data.get("notes")
            if notes:
                dosage_info += f"""

⚠️ **IMPORTANT SAFETY TIPS**
{notes}"""
            
            dosage_info += f"""

✅ **SAFETY FIRST**
• Always read the medicine bottle label
• Wear gloves when spraying
• Watch your plant daily for changes
• Ask local experts if you need help

💚 **Take care of yourself and your plants!**"""
            
            return dosage_info
        
        return "I don't have detailed dosage information available. Please refer to the medicine bottle labels or consult with local agricultural experts."
    
    async def _detect_goodbye_intent(self, state: WorkflowState) -> bool:
        """
        Detect if user wants to end the session using LLM analysis
        """
        try:
            user_message = state.get("user_message", "")
            if not user_message:
                return False
            
            goodbye_prompt = f"""Analyze this user message to determine if they want to END or CLOSE their consultation session.

User message: "{user_message}"

Look for goodbye indicators like:
- Thank you, thanks, thank u
- Bye, goodbye, see you, farewell
- That's all, that's it, I'm done
- End session, close, finish, complete
- No more questions, nothing else
- Perfect, great, awesome (when indicating satisfaction and closure)

Respond with ONLY "YES" if they want to end the session, or "NO" if they want to continue.

Response:"""

            # Get LLM response
            response = await self.llm.ainvoke(goodbye_prompt)
            response_text = response.content.strip().upper()
            
            logger.debug(f"🤖 Goodbye intent analysis: '{user_message}' -> {response_text}")
            
            # Simple check for YES/NO
            wants_to_end = "YES" in response_text and "NO" not in response_text
            
            logger.info(f"👋 User goodbye intent detected: {wants_to_end}")
            return wants_to_end
            
        except Exception as e:
            logger.error(f"❌ Error in goodbye intent detection: {e}")
            # Fallback to simple keyword detection
            user_message_lower = user_message.lower() if user_message else ""
            goodbye_keywords = ["thank you", "thanks", "bye", "goodbye", "that's all", "that's it", "done", "finish", "complete"]
            fallback_result = any(keyword in user_message_lower for keyword in goodbye_keywords)
            logger.info(f"👋 Fallback goodbye intent: {fallback_result}")
            return fallback_result
