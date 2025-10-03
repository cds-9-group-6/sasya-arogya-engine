"""
Initial Node for FSM Agent workflow
Handles user input and determines first action based on user intent
"""

import logging
from typing import Dict, Any, Optional

from .base_node import BaseNode

from ..workflow_state import WorkflowState, add_message_to_state, set_error
from ...tools.context_extractor import ContextExtractorTool

logger = logging.getLogger(__name__)

# Import response configuration and metrics (with error handling)
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


class InitialNode(BaseNode):
    """Initial node - handles user input and determines first action based on user intent"""
    
    @property
    def node_name(self) -> str:
        return "initial"
    
    async def execute(self, state: WorkflowState) -> WorkflowState:
        """
        Execute initial node logic
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        self.update_node_state(state)
        
        try:
            # Check if this is a continuing conversation (loaded from session)
            is_continuing_conversation = self._is_continuing_conversation(state)
            
            if is_continuing_conversation:
                # This is a followup in an existing conversation - route to followup handling
                logger.info(f"🔄 Detected continuing conversation for session {state['session_id']} - routing to followup")
                state["next_action"] = "followup"
                return state
            
            # Analyze user intent for NEW conversations
            user_intent = await self._analyze_user_intent(state["user_message"])
            state["user_intent"] = user_intent
            
            # FIXED: Check for goodbye intent BEFORE processing other intents
            if await self._detect_goodbye_intent(state):
                logger.info("👋 Goodbye intent detected in new message - routing to session_end")
                state["next_action"] = "session_end"
                return state
            
            # Extract context from user message if possible
            context_tool = self.tools["context_extractor"]
            context_input = {"user_message": state["user_message"]}
            context_result = await context_tool.arun(context_input)
            
            if context_result and not context_result.get("error"):
                self._process_context_extraction(state, context_result)
            
            # Store general answer for later use (for hybrid requests)
            general_answer = user_intent.get("general_answer", "")
            if general_answer:
                state["general_answer"] = general_answer
                logger.info(f"🌾 Stored general answer for hybrid request: {general_answer[:100]}...")
            
            # Check for out-of-scope questions first
            if user_intent.get("out_of_scope", False):
                self._handle_out_of_scope_request(state, user_intent)
                return state
            
            # Determine next action based on user intent and input
            self._determine_next_action(state, user_intent, general_answer)
            
        except Exception as e:
            logger.error(f"Error in initial node: {str(e)}", exc_info=True)
            set_error(state, f"Error processing initial request: {str(e)}")
            state["next_action"] = "error"
        
        return state
    
    def _process_context_extraction(self, state: WorkflowState, context_result: Dict[str, Any]) -> None:
        """Process context extraction results and update state"""
        # Debug: Log current state before context processing
        logger.info(f"🔍 BEFORE context processing - plant_type: {state.get('plant_type')}, location: {state.get('location')}, season: {state.get('season')}")
        logger.info(f"🔍 Context extractor result: {context_result}")
        
        # Preserve existing context from API request, only supplement missing values
        existing_context = state.get("user_context", {})
        extracted_context = context_result or {}
        
        # Merge contexts - API context takes precedence, extractor supplements
        merged_context = {**extracted_context, **existing_context}
        state["user_context"] = merged_context
        
        # Only update individual fields if not already set from API request
        context_fields = [
            ("location", "🔄 Updating location from extractor", "✅ Keeping API location"),
            ("season", "🔄 Updating season from extractor", "✅ Keeping API season"),
            ("plant_type", "🔄 Updating plant_type from extractor", "✅ Keeping API plant_type"),
            ("growth_stage", None, None)
        ]
        
        for field, update_msg, keep_msg in context_fields:
            if not state.get(field):
                if update_msg:
                    logger.info(f"{update_msg}: {context_result.get(field)}")
                state[field] = context_result.get(field)
            else:
                if keep_msg:
                    logger.info(f"{keep_msg}: {state.get(field)}")
        
        # Debug: Log final state after context processing
        logger.info(f"✅ AFTER context processing - plant_type: {state.get('plant_type')}, location: {state.get('location')}, season: {state.get('season')}")
    
    def _determine_next_action(self, state: WorkflowState, user_intent: Dict[str, Any], general_answer: str) -> None:
        """Determine the next action based on user intent"""
        # Check for tool requests first, then handle pure general questions
        if state.get("user_image") and user_intent["wants_classification"]:
            # Has image and user wants classification
            state["next_action"] = "classify"
            classification_msg = "🌱 I can see you've uploaded an image of a plant leaf. Let me analyze it for disease detection."
            
            # Add general answer if this is a hybrid request
            if general_answer:
                classification_msg += f"\n\n🌾 **General Agricultural Advice:** {general_answer}"
            
            add_message_to_state(state, "assistant", classification_msg)
            
        elif user_intent["wants_classification"] and not state.get("user_image"):
            # Wants classification but no image
            state["next_action"] = "request_image"
            image_request_msg = "🌱 I'd be happy to help analyze your plant! Please upload a clear photo of the affected leaf showing any symptoms."
            
            # Add general answer if this is a hybrid request
            if general_answer:
                image_request_msg += f"\n\n🌾 **General Agricultural Advice:** {general_answer}"
            
            add_message_to_state(state, "assistant", image_request_msg)
            state["requires_user_input"] = True
            
        elif user_intent.get("wants_insurance", False):
            # User wants insurance services
            state["next_action"] = "insurance"
            insurance_msg = "🏦 I'll help you with crop insurance options."
            
            # Add general answer if this is a hybrid request
            if general_answer:
                insurance_msg += f"\n\n🌾 **General Agricultural Advice:** {general_answer}"
            
            add_message_to_state(state, "assistant", insurance_msg)
            
        elif user_intent.get("is_general_question", False) and not any([
            user_intent["wants_classification"], 
            user_intent["wants_prescription"], 
            user_intent["wants_insurance"]
        ]):
            # Check if this is a plant-related general question that might need clarification
            user_message_lower = state["user_message"].lower()
            
            # Keywords that indicate potential plant disease/diagnosis requests (not general agriculture)
            plant_health_keywords = ["disease", "diagnose", "analyze", "wrong", "problem", "issue", "sick", "dying", "spots", "infection", "symptom"]
            plant_help_keywords = ["help", "what's wrong", "can you help", "need help"]
            
            # Must have plant context AND health/diagnostic intent 
            has_plant_context = any(word in user_message_lower for word in ["plant", "leaf", "leaves", "crop"])
            has_health_intent = any(word in user_message_lower for word in plant_health_keywords)
            has_help_intent = any(phrase in user_message_lower for phrase in plant_help_keywords)
            
            # Plant-related if: (plant context AND health intent) OR (plant context AND help intent)
            is_plant_related = has_plant_context and (has_health_intent or has_help_intent)
            
            if is_plant_related:
                # FIXED: Plant-related general questions should get clarification, not direct completion
                logger.info(f"🌱 Plant-related general question detected, routing to clarification instead of direct completion")
                state["next_action"] = "general_help"
                
                help_msg = "🌱 I can help you with plant disease diagnosis and treatment! "
                if general_answer:
                    help_msg += f"{general_answer}\n\n"
                
                help_msg += """To get started, I can:
• **Analyze plant diseases** - Upload a photo of your plant for diagnosis
• **Recommend treatments** - Get specific treatment plans after diagnosis  
• **Provide crop insurance** - Calculate premiums and get insurance recommendations

What would you like me to help you with? Please share more details or upload a plant image."""
                
                add_message_to_state(state, "assistant", help_msg)
                state["requires_user_input"] = True
                
            else:
                # Pure non-plant general question (agriculture advice, weather, etc.)
                # FIXED: Keep session active - only end on explicit user intent
                state["next_action"] = "general_help"  # Changed from "completed" to keep session active
                if general_answer:
                    add_message_to_state(
                        state,
                        "assistant", 
                        f"🌾 {general_answer}\n\nIs there anything else I can help you with regarding plant disease diagnosis or treatment?"
                    )
                else:
                    add_message_to_state(
                        state,
                        "assistant", 
                        "🌾 I understand you have a general farming question. I can provide basic guidance on agricultural topics, but I specialize in plant disease diagnosis and treatment. Feel free to ask about specific plant issues or upload a photo for disease analysis!"
                    )
                state["requires_user_input"] = True  # FIXED: Keep session active for user response
        else:
            # General greeting or unclear intent
            state["next_action"] = "general_help"
            help_msg = "🌱 Hello! I'm your plant disease diagnosis assistant. I can help you:\n\n" + \
                      "• **Identify diseases** - Upload a photo for analysis\n" + \
                      "• **Get treatment recommendations** - Get prescription after diagnosis\n" + \
                      "• **Crop insurance** - Calculate premiums and get insurance recommendations\n\n" + \
                      "What would you like me to help you with today?"
            
            # Add general answer if available
            if general_answer:
                help_msg = f"🌾 {general_answer}\n\n" + help_msg
            
            add_message_to_state(state, "assistant", help_msg)
            state["requires_user_input"] = True
    
    async def _analyze_user_intent(self, user_message: str) -> Dict[str, Any]:
        """
        Analyze user intent using LLM to determine what they want from the agent.
        This provides much more robust intent recognition than keyword matching.
        Handles both specialized tool requests and general agricultural questions.
        """
        try:
            intent_prompt = self._build_intent_analysis_prompt(user_message)
            
            # Get LLM response
            response = await self.llm.ainvoke(intent_prompt)
            response_text = response.content.strip()
            
            logger.debug(f"🧠 LLM intent analysis raw response: {response_text}")
            
            # Parse JSON response
            intent = self._parse_intent_response(response_text)
            if intent:
                logger.info(f"🎯 LLM-driven user intent analysis: {intent}")
                return intent
                    
        except Exception as e:
            logger.error(f"❌ Error in LLM intent analysis: {e}, using fallback analysis")
        
        # Fallback to simple keyword-based analysis if LLM fails
        logger.info("🔄 Using fallback keyword-based intent analysis")
        return await self._fallback_intent_analysis(user_message)
    
    async def _detect_goodbye_intent(self, state) -> bool:
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
- Thank you, thanks, thank u (when expressing gratitude for completion)
- Bye, goodbye, see you, farewell, adios, ciao
- That's all, that's it, I'm done, finished, complete
- End session, close, finish, stop, quit, exit
- No more questions, nothing else, all set
- Perfect, great, awesome (when indicating satisfaction and closure)

Respond with ONLY "YES" if they want to end the session, or "NO" if they want to continue.

Response:"""

            # Get LLM response
            response = await self.llm.ainvoke(goodbye_prompt)
            response_text = response.content.strip().upper()
            
            logger.debug(f"🤖 Goodbye intent analysis: '{user_message}' -> {response_text}")
            
            # Simple check for YES/NO
            wants_to_end = "YES" in response_text and "NO" not in response_text
            
            return wants_to_end
            
        except Exception as e:
            logger.error(f"❌ Error in goodbye intent detection: {e}")
            # Fallback to simple keyword detection
            user_message_lower = user_message.lower()
            goodbye_keywords = [
                "thank you", "thanks", "bye", "goodbye", "farewell", 
                "that's all", "that's it", "done", "finished", "complete",
                "end session", "quit", "exit", "stop", "no more"
            ]
            fallback_result = any(keyword in user_message_lower for keyword in goodbye_keywords)
            logger.info(f"👋 Fallback goodbye intent detection: {fallback_result}")
            return fallback_result
    
    def _handle_out_of_scope_request(self, state: WorkflowState, user_intent: Dict[str, Any]) -> None:
        """Handle out-of-scope requests with appropriate response and metrics"""
        
        # Record metrics if available
        if METRICS_AVAILABLE:
            try:
                metrics = get_metrics()
                scope_confidence = user_intent.get("scope_confidence", 0.0)
                
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
                    intent_type="non_agricultural", 
                    user_message_category=category
                )
                metrics.record_intent_confidence("out_of_scope", scope_confidence)
                metrics.record_response_type_usage(ResponseType.OUT_OF_SCOPE.value, "initial")
                
            except Exception as e:
                logger.warning(f"Failed to record out-of-scope metrics: {e}")
        
        # Generate appropriate response
        if RESPONSE_CONFIG_AVAILABLE:
            try:
                response = response_config.get_response(ResponseType.OUT_OF_SCOPE)
                logger.info(f"🚫 Generated out-of-scope response for non-agricultural question")
            except Exception as e:
                logger.warning(f"Failed to get response from config: {e}")
                response = "I'm sorry, but I can only help with crop care and agricultural questions. Could you please ask me something related to plant diseases, farming, or crop management?"
        else:
            response = "I'm sorry, but I can only help with crop care and agricultural questions. Could you please ask me something related to plant diseases, farming, or crop management?"
        
        # Set state for completion  
        add_message_to_state(state, response, "assistant")
        state["assistant_response"] = response
        state["next_action"] = "completed"
        state["is_complete"] = True
        
        logger.info(f"🚫 Out-of-scope request handled. Confidence: {user_intent.get('scope_confidence', 0.0)}")
    
    def _build_intent_analysis_prompt(self, user_message: str) -> str:
        """Build the intent analysis prompt"""
        return f"""You are an expert at understanding user intent for a plant disease diagnosis and treatment system.

Analyze the following user message and determine their intent by responding with ONLY a JSON object containing these fields:
- wants_classification: (boolean) Does the user want disease diagnosis/identification?
- wants_prescription: (boolean) Does the user want treatment recommendations?  
- wants_full_workflow: (boolean) Does the user want the complete process (diagnosis + treatment)?
- wants_insurance: (boolean) Does the user want crop insurance services (premium calculation, recommendations, companies, coverage)?
- wants_insurance_premium: (boolean) Specifically wants to calculate insurance premium/cost?
- wants_insurance_companies: (boolean) Specifically wants to find insurance companies/providers?
- wants_insurance_recommendation: (boolean) Specifically wants insurance recommendation based on crop/disease?
- wants_insurance_purchase: (boolean) Specifically wants to buy/apply/purchase insurance or generate certificate?
- is_general_question: (boolean) Does the message contain general agricultural/farming questions (soil tips, weather advice, growing tips, etc.)?
- is_agriculture_related: (boolean) Is this question related to agriculture, farming, crops, plants, or agricultural business at all?
- out_of_scope: (boolean) Is this question completely outside agricultural/farming/crop care domain?
- scope_confidence: (number 0-1) How confident are you that this is agriculture-related (1=definitely agriculture, 0=definitely not agriculture)?
- general_answer: (string) If is_general_question=true, provide helpful answers to the general agriculture questions. Otherwise, leave as empty string.

Rules:
1. If they want prescription OR full workflow, they automatically need classification first
2. Insurance requests can work independently or with other services (diagnosis + insurance is common)
3. CRITICAL - ANALYZE keyword disambiguation:
   - "analyze disease/plant/leaf/crop" → wants_classification=true, wants_prescription=false (diagnosis only)
   - "analyze AND treat/cure/fix" → wants_classification=true, wants_prescription=true
   - "analyze my disease and get treatment" → wants_classification=true, wants_prescription=true
   - When user says "analyze" without treatment keywords, default to classification ONLY
4. Use natural language understanding, not just keyword matching
5. Consider context and implied meaning
6. IMPORTANT: Tool requests (wants_*) and general questions (is_general_question) are NOT mutually exclusive
7. A message can contain BOTH tool requests AND general questions - analyze each part independently
8. If any part asks for general advice (soil health, weather, growing tips, timing, etc.), set is_general_question=true
9. Answer the general questions even if there are also tool requests in the same message
10. Insurance keywords: premium, insurance, coverage, protect, policy, claim, insure, risk management
11. SCOPE DETECTION RULES:
    - is_agriculture_related=true: Questions about crops, plants, farming, agriculture, rural business, food production, etc.
    - out_of_scope=true: Questions about technology, medicine (human), entertainment, vehicles, cooking recipes, general weather, etc.
    - scope_confidence: Be very confident (0.9+) for clear agricultural topics, less confident (0.3-0.7) for ambiguous cases
    - If out_of_scope=true, set all wants_* fields to false and is_general_question to false
    - Agricultural topics include: plant diseases, crop management, farming techniques, agricultural insurance, farm equipment, pesticides, fertilizers, irrigation, soil management, harvest, seeds, livestock, rural economics

Examples:
- "What's wrong with my plant?" → {{"wants_classification": true, "wants_prescription": false, "wants_full_workflow": false, "wants_insurance": false, "wants_insurance_premium": false, "wants_insurance_companies": false, "wants_insurance_recommendation": false, "wants_insurance_purchase": false, "is_general_question": false, "is_agriculture_related": true, "out_of_scope": false, "scope_confidence": 0.95, "general_answer": ""}}
- "Analyze this plant disease" → {{"wants_classification": true, "wants_prescription": false, "wants_full_workflow": false, "wants_insurance": false, "wants_insurance_premium": false, "wants_insurance_companies": false, "wants_insurance_recommendation": false, "wants_insurance_purchase": false, "is_general_question": false, "is_agriculture_related": true, "out_of_scope": false, "scope_confidence": 0.98, "general_answer": ""}}
- "Please analyze what's wrong with this leaf" → {{"wants_classification": true, "wants_prescription": false, "wants_full_workflow": false, "wants_insurance": false, "wants_insurance_premium": false, "wants_insurance_companies": false, "wants_insurance_recommendation": false, "wants_insurance_purchase": false, "is_general_question": false, "is_agriculture_related": true, "out_of_scope": false, "scope_confidence": 0.97, "general_answer": ""}}
- "Can you analyze and identify the disease in my plant?" → {{"wants_classification": true, "wants_prescription": false, "wants_full_workflow": false, "wants_insurance": false, "wants_insurance_premium": false, "wants_insurance_companies": false, "wants_insurance_recommendation": false, "wants_insurance_purchase": false, "is_general_question": false, "is_agriculture_related": true, "out_of_scope": false, "scope_confidence": 0.96, "general_answer": ""}}
- "Analyze my crop disease" → {{"wants_classification": true, "wants_prescription": false, "wants_full_workflow": false, "wants_insurance": false, "wants_insurance_premium": false, "wants_insurance_companies": false, "wants_insurance_recommendation": false, "wants_insurance_purchase": false, "is_general_question": false, "is_agriculture_related": true, "out_of_scope": false, "scope_confidence": 0.98, "general_answer": ""}}
- "Help my tomato plant get better" → {{"wants_classification": true, "wants_prescription": true, "wants_full_workflow": true, "wants_insurance": false, "wants_insurance_premium": false, "wants_insurance_companies": false, "wants_insurance_recommendation": false, "wants_insurance_purchase": false, "is_general_question": false, "is_agriculture_related": true, "out_of_scope": false, "scope_confidence": 0.98, "general_answer": ""}}
- "Analyze and treat my plant disease" → {{"wants_classification": true, "wants_prescription": true, "wants_full_workflow": false, "wants_insurance": false, "wants_insurance_premium": false, "wants_insurance_companies": false, "wants_insurance_recommendation": false, "wants_insurance_purchase": false, "is_general_question": false, "is_agriculture_related": true, "out_of_scope": false, "scope_confidence": 0.99, "general_answer": ""}}
- "I need crop insurance for my wheat farm" → {{"wants_classification": false, "wants_prescription": false, "wants_full_workflow": false, "wants_insurance": true, "wants_insurance_premium": false, "wants_insurance_companies": false, "wants_insurance_recommendation": true, "wants_insurance_purchase": false, "is_general_question": false, "is_agriculture_related": true, "out_of_scope": false, "scope_confidence": 0.99, "general_answer": ""}}
- "What's the best smartphone to buy?" → {{"wants_classification": false, "wants_prescription": false, "wants_full_workflow": false, "wants_insurance": false, "wants_insurance_premium": false, "wants_insurance_companies": false, "wants_insurance_recommendation": false, "wants_insurance_purchase": false, "is_general_question": false, "is_agriculture_related": false, "out_of_scope": true, "scope_confidence": 0.1, "general_answer": ""}}
- "How do I fix my car engine?" → {{"wants_classification": false, "wants_prescription": false, "wants_full_workflow": false, "wants_insurance": false, "wants_insurance_premium": false, "wants_insurance_companies": false, "wants_insurance_recommendation": false, "wants_insurance_purchase": false, "is_general_question": false, "is_agriculture_related": false, "out_of_scope": true, "scope_confidence": 0.05, "general_answer": ""}}
- "How much will insurance cost for 5 hectares of rice?" → {{"wants_classification": false, "wants_prescription": false, "wants_full_workflow": false, "wants_insurance": true, "wants_insurance_premium": true, "wants_insurance_companies": false, "wants_insurance_recommendation": false, "wants_insurance_purchase": false, "is_general_question": false, "general_answer": ""}}
- "Which insurance companies are available in Karnataka?" → {{"wants_classification": false, "wants_prescription": false, "wants_full_workflow": false, "wants_insurance": true, "wants_insurance_premium": false, "wants_insurance_companies": true, "wants_insurance_recommendation": false, "wants_insurance_purchase": false, "is_general_question": false, "general_answer": ""}}
- "My cotton has disease, need treatment and insurance" → {{"wants_classification": true, "wants_prescription": true, "wants_full_workflow": false, "wants_insurance": true, "wants_insurance_premium": false, "wants_insurance_companies": false, "wants_insurance_recommendation": true, "wants_insurance_purchase": false, "is_general_question": false, "general_answer": ""}}
- "What's the best time to plant tomatoes?" → {{"wants_classification": false, "wants_prescription": false, "wants_full_workflow": false, "wants_insurance": false, "wants_insurance_premium": false, "wants_insurance_companies": false, "wants_insurance_recommendation": false, "wants_insurance_purchase": false, "is_general_question": true, "general_answer": "The best time to plant tomatoes depends on your location. Generally, plant tomatoes after the last frost date in your area. In most regions, this is 2-3 weeks after the last frost when soil temperature reaches 60-65°F (15-18°C). For warm climates, plant in early spring or fall. For cooler climates, start seeds indoors 6-8 weeks before the last frost date."}}
- "Analyze my plant disease and also give me watering tips" → {{"wants_classification": true, "wants_prescription": false, "wants_full_workflow": false, "wants_insurance": false, "wants_insurance_premium": false, "wants_insurance_companies": false, "wants_insurance_recommendation": false, "wants_insurance_purchase": false, "is_general_question": true, "general_answer": "For proper watering: Water deeply but less frequently to encourage deep root growth. Check soil moisture 2-3 inches deep - if dry, it's time to water. Most crops need 1-2 inches of water per week including rainfall. Water early morning to reduce evaporation and disease risk."}}
- "Diagnose this leaf, get treatment, and tell me about soil health" → {{"wants_classification": true, "wants_prescription": true, "wants_full_workflow": false, "wants_insurance": false, "wants_insurance_premium": false, "wants_insurance_companies": false, "wants_insurance_recommendation": false, "wants_insurance_purchase": false, "is_general_question": true, "general_answer": "For healthy soil: Test pH regularly (most crops prefer 6.0-7.0). Add organic matter like compost to improve structure and nutrients. Ensure good drainage while retaining moisture. Rotate crops to prevent nutrient depletion. Consider cover crops during off-season to maintain soil health."}}
- "I want to buy crop insurance for my wheat farm" → {{"wants_classification": false, "wants_prescription": false, "wants_full_workflow": false, "wants_insurance": true, "wants_insurance_premium": false, "wants_insurance_companies": false, "wants_insurance_recommendation": false, "wants_insurance_purchase": true, "is_general_question": false, "general_answer": ""}}
- "Help me apply for crop insurance with these premium details" → {{"wants_classification": false, "wants_prescription": false, "wants_full_workflow": false, "wants_insurance": true, "wants_insurance_premium": false, "wants_insurance_companies": false, "wants_insurance_recommendation": false, "wants_insurance_purchase": true, "is_general_question": false, "general_answer": ""}}

User message: "{user_message}"

Response (JSON only):"""
    
    def _parse_intent_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse the LLM intent response"""
        try:
            import json
            # Extract JSON from response (in case there's extra text)
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                intent = json.loads(json_str)
                
                # Ensure all required keys exist with defaults
                default_intent = {
                    "wants_classification": False,
                    "wants_prescription": False,
                    "wants_vendors": False,
                    "wants_full_workflow": False,
                    "wants_insurance": False,
                    "wants_insurance_premium": False,
                    "wants_insurance_companies": False,
                    "wants_insurance_recommendation": False,
                    "wants_insurance_purchase": False,
                    "is_general_question": False,
                    "general_answer": ""
                }
                default_intent.update(intent)
                intent = default_intent
                
                # Apply dependency rules (ensure logical consistency)
                # Only apply tool dependency rules if it's not a general question
                if not intent.get("is_general_question", False):
                    if intent.get("wants_prescription") or intent.get("wants_vendors") or intent.get("wants_full_workflow"):
                        intent["wants_classification"] = True
                    
                    if intent.get("wants_vendors") or intent.get("wants_full_workflow"):
                        intent["wants_prescription"] = True
                        intent["wants_classification"] = True
                    
                    if intent.get("wants_full_workflow"):
                        intent["wants_vendors"] = True
                        intent["wants_prescription"] = True
                        intent["wants_classification"] = True
                
                return intent
                
            else:
                logger.warning("🚨 Could not find valid JSON in LLM response, using fallback analysis")
                
        except json.JSONDecodeError as e:
            logger.warning(f"🚨 Failed to parse JSON from LLM response: {e}, using fallback analysis")
            
        return None
    
    async def _fallback_intent_analysis(self, user_message: str) -> Dict[str, Any]:
        """
        Fallback intent analysis using simple keyword matching.
        Used when LLM-based analysis fails.
        """
        user_message_lower = user_message.lower()
        
        intent = {
            "wants_classification": False,
            "wants_prescription": False,
            "wants_vendors": False,
            "wants_full_workflow": False,
            "is_general_question": False,
            "general_answer": ""
        }
        
        # Classification keywords
        classification_keywords = ["analyze", "detect", "identify", "classify", "disease", "what", "wrong", "issue", "problem"]
        if any(word in user_message_lower for word in classification_keywords):
            intent["wants_classification"] = True
        
        # Prescription keywords
        prescription_keywords = ["treatment", "cure", "fix", "help", "recommend", "prescription", "medicine", "spray"]
        if any(word in user_message_lower for word in prescription_keywords):
            intent["wants_prescription"] = True
            intent["wants_classification"] = True  # Need classification first
        
        # Use centralized intent analyzer for better maintainability
        from ..intent_analyzer import intent_analyzer
        detected_intents = intent_analyzer.analyze_intent(user_message)
        
        # Map detected intents to workflow flags
        if detected_intents.get("vendor", 0) > 0.5:
            intent["wants_vendors"] = True
            intent["wants_prescription"] = True  # Need prescription first
            intent["wants_classification"] = True  # Need classification first
        
        # Full workflow keywords
        full_keywords = ["complete", "full", "everything", "all", "comprehensive"]
        if any(word in user_message_lower for word in full_keywords):
            intent["wants_full_workflow"] = True
            intent["wants_vendors"] = True
            intent["wants_prescription"] = True
            intent["wants_classification"] = True
        
        # Check for general questions (fallback has limited capability)
        general_keywords = ["how", "when", "why", "what", "where", "best time", "tips", "advice", "weather", "climate"]
        farming_keywords = ["plant", "grow", "crop", "farm", "soil", "water", "fertilizer", "seed"]
        
        # If it contains general question words + farming context but no specific tool requests
        if (any(word in user_message_lower for word in general_keywords) and 
            any(word in user_message_lower for word in farming_keywords) and 
            not any([intent["wants_classification"], intent["wants_prescription"], intent["wants_vendors"]])):
            
            intent["is_general_question"] = True
            intent["general_answer"] = "I understand you have a general farming question. For the best answer, please try again when the LLM system is available, or feel free to ask about specific plant diseases or issues that I can help diagnose and treat."
        
        logger.info(f"📝 Fallback intent analysis: {intent}")
        return intent
    
    def _is_continuing_conversation(self, state: WorkflowState) -> bool:
        """
        Detect if this is a continuing conversation (loaded from session) rather than a new one
        
        Args:
            state: Current workflow state
            
        Returns:
            True if this is a continuing conversation, False if it's a new conversation
        """
        # CRITICAL: Check if session has ended - if so, treat as NEW conversation regardless of history
        session_ended = state.get("session_ended", False)
        if session_ended:
            logger.info(f"🔄 Session {state['session_id']} has ended - treating as NEW conversation despite history")
            return False
        
        # Check for indicators that this is a loaded session with previous conversation history
        has_previous_results = bool(
            state.get("classification_results") or 
            state.get("prescription_data") or
            state.get("vendor_options") or
            state.get("disease_name")
        )
        
        # Check if there is meaningful conversation history from loaded session
        # NOTE: Assistant messages are in the loaded session state, not in the current request
        messages = state.get("messages", [])
        
        # Count conversation turns from loaded session history
        assistant_messages = [msg for msg in messages if msg.get("role") == "assistant"]
        user_messages = [msg for msg in messages if msg.get("role") == "user"]
        
        # Real conversation = Assistant has participated (responded to user messages)
        has_meaningful_conversation = len(assistant_messages) > 0
        
        # Additional check: Do we have workflow results indicating previous successful interactions?
        has_workflow_results = bool(
            state.get("classification_results") or 
            state.get("prescription_data") or
            state.get("vendor_options")
        )
        
        # Conversation history = meaningful conversation OR workflow results
        has_conversation_history = has_meaningful_conversation or has_workflow_results
        
        # Debug logging for session analysis
        current_user_message = state.get("user_message", "")
        logger.info(f"🔍 Session conversation analysis:")
        logger.info(f"   - Current message: '{current_user_message[:50]}...'")
        logger.info(f"   - Total messages in session: {len(messages)}")
        logger.info(f"   - Assistant messages: {len(assistant_messages)}")
        logger.info(f"   - User messages: {len(user_messages)}")
        logger.info(f"   - Has workflow results: {has_workflow_results}")
        logger.info(f"   - Has meaningful conversation: {has_meaningful_conversation}")
        
        # Check for potential app duplicate pattern
        if len(user_messages) > 1 and len(assistant_messages) == 0:
            recent_user_contents = [msg.get("content", "") for msg in user_messages[-3:]]
            duplicate_count = recent_user_contents.count(current_user_message)
            if duplicate_count > 1:
                logger.warning(f"⚠️ Detected {duplicate_count} identical user messages with no assistant responses - possible app duplicate issue")
                # But don't override has_conversation_history if we have workflow results
                if not has_workflow_results:
                    has_conversation_history = False
        
        # Check if current node indicates this came from a previous workflow state
        current_node = state.get("current_node", "initial")
        was_in_middle_of_workflow = current_node != "initial"
        
        # Additional check for completed state handling
        # IMPORTANT: Users asking followup questions after completing a workflow should still be treated as continuing conversation
        # Only treat as "new" if there's no meaningful history at all
        is_in_completed_state = current_node == "completed" and not state.get("requires_user_input", False)
        
        # Modified logic: Completed state doesn't automatically mean "new conversation" 
        # if we have meaningful history (assistant messages or workflow results)
        should_treat_completed_as_new = is_in_completed_state and not (has_meaningful_conversation or has_workflow_results)
        
        is_continuing = (has_previous_results or has_conversation_history or was_in_middle_of_workflow) and not should_treat_completed_as_new
        
        if is_continuing:
            logger.info(f"🔍 Continuing conversation detected:")
            logger.info(f"   - Has previous results: {has_previous_results}")
            logger.info(f"   - Has conversation history: {has_conversation_history} ({len(assistant_messages)} assistant, {len(user_messages)} user messages)")
            logger.info(f"   - Was in middle of workflow: {was_in_middle_of_workflow} (node: {current_node})")
            logger.info(f"   - Is in completed state: {is_in_completed_state}")
            logger.info(f"   - Should treat completed as new: {should_treat_completed_as_new}")
        else:
            logger.info(f"🆕 New conversation detected for session {state['session_id']}")
            logger.info(f"   - Session ended: {session_ended}")
            logger.info(f"   - In completed state: {is_in_completed_state}")
            logger.info(f"   - Should treat completed as new: {should_treat_completed_as_new}")
            logger.info(f"   - Assistant messages: {len(assistant_messages)}")
            logger.info(f"   - User messages: {len(user_messages)}")
            if len(user_messages) > 0 and len(assistant_messages) == 0:
                logger.info(f"   - ⚠️ User messages without assistant responses detected (possible app duplicate)")
        
        return is_continuing
