"""
Completed Node for FSM Agent workflow
Final state with follow-up questions
"""

import logging
from typing import Dict, Any, List, Tuple
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
        
        # Generate relevant follow-ups based on actual services used
        follow_ups = self._generate_contextual_follow_ups(state, services_used)
        
        # Create contextual completion message based on what actually happened
        if existing_response and existing_response.strip() and previous_node == "followup":
            # Direct followup response - use as-is, just add minimal follow-up options
            completion_message = self._create_clean_followup_response(existing_response, follow_ups)
        elif existing_response and existing_response.strip():
            # Tool workflow completed - add follow-up options without ugly formatting
            completion_message = self._create_clean_workflow_completion(existing_response, follow_ups)
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
                           or state.get("insurance_recommendations") or state.get("insurance_companies")),
            "vendors": bool(state.get("vendor_options") or state.get("selected_vendor"))
        }
    
    def _create_completion_context(self, state: WorkflowState, services_used: Dict[str, bool]) -> Dict[str, Any]:
        """Create context summary of what happened in this session"""
        context = {
            "services_count": sum(services_used.values()),
            "services_list": [service for service, used in services_used.items() if used]
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
            
        if services_used["vendors"]:
            vendors = state.get("vendor_options", [])
            context["vendor_count"] = len(vendors)
        
        return context
    
    def _create_contextual_completion_message(self, services_used: Dict[str, bool], context: Dict[str, Any], follow_ups: List[str]) -> str:
        """Create appropriate completion message based on services actually used"""
        services_list = context["services_list"]
        services_count = context["services_count"]
        
        if services_count == 0:
            # No specific services used - general help
            title = "✅ **HOW CAN I HELP YOU?**"
            summary = "I'm here to help with plant disease diagnosis, treatment recommendations, crop insurance, and finding suppliers."
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
        """Get title and summary for single service completion"""
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
            
        elif service == "vendors":
            vendor_count = context.get("vendor_count", 0)
            return "✅ **YOUR SUPPLIER SEARCH COMPLETE**", f"We found {vendor_count} suppliers for your agricultural needs with contact information and pricing."
            
        else:
            return "✅ **SERVICE COMPLETED**", "We've completed your request and provided the information you needed."
    
    def _get_multiple_services_summary(self, services_list: List[str], context: Dict[str, Any]) -> str:
        """Get summary for multiple services completion"""
        summaries = []
        
        if "classification" in services_list:
            disease = context.get("disease_name", "disease")
            summaries.append(f"diagnosed {disease}")
            
        if "prescription" in services_list:
            treatment_count = context.get("treatment_count", 0)
            summaries.append(f"provided {treatment_count} treatments")
            
        if "insurance" in services_list:
            insurance_type = context.get("insurance_type", "insurance services")
            summaries.append(f"handled crop {insurance_type}")
            
        if "vendors" in services_list:
            vendor_count = context.get("vendor_count", 0)
            summaries.append(f"found {vendor_count} suppliers")
        
        if len(summaries) > 1:
            return f"We {', '.join(summaries[:-1])} and {summaries[-1]} for you."
        else:
            return f"We {summaries[0]} for you."
    
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
            
        if services_used["vendors"]:
            help_items.extend([
                "Find suppliers in different locations",
                "Get pricing for other products"
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
            clean_message += f"\n\n💡 **Next steps**: {', '.join(follow_ups[:2])}"
        else:
            clean_message += "\n\n💡 **Ask me anything else about your plants!**"
            
        return clean_message
    
    def _create_clean_workflow_completion(self, workflow_response: str, follow_ups: List[str]) -> str:
        """Create clean completion for workflow tools (classification, prescription) without ugly formatting"""
        
        # FIXED: No ugly horizontal lines - just clean completion
        clean_message = workflow_response.strip()
        
        # Add clean next steps for workflow completions
        clean_message += "\n\n**What would you like to do next?**"
        if follow_ups:
            for i, follow_up in enumerate(follow_ups[:3], 1):
                clean_message += f"\n• {follow_up}"
        else:
            clean_message += """
• 📸 Upload another image for analysis
• 💊 Get treatment recommendations 
• 🛒 Find suppliers for treatments"""
            
        return clean_message
    
    def _generate_contextual_follow_ups(self, state: WorkflowState, services_used: Dict[str, bool]) -> List[str]:
        """
        Generate relevant follow-up questions based on services actually used
        
        Args:
            state: Current workflow state
            services_used: Dictionary of which services were used
            
        Returns:
            List of follow-up questions/suggestions (max 3)
        """
        follow_ups = []
        
        # Extract previous user messages to avoid duplicating questions
        messages = state.get("messages", [])
        user_messages = [msg.get("content", "").lower() for msg in messages if msg.get("role") == "user"]
        all_user_text = " ".join(user_messages)
        
        # Helper function to check if topic was already discussed
        def already_asked(keywords: List[str]) -> bool:
            return any(keyword.lower() in all_user_text for keyword in keywords)
        
        # Generate service-specific follow-ups based on what was actually used
        if services_used["classification"]:
            follow_ups.extend(self._get_classification_follow_ups(state, already_asked))
            
        if services_used["prescription"]:
            follow_ups.extend(self._get_prescription_follow_ups(state, already_asked))
            
        if services_used["insurance"]:
            follow_ups.extend(self._get_insurance_follow_ups(state, already_asked))
            
        if services_used["vendors"]:
            follow_ups.extend(self._get_vendor_follow_ups(state, already_asked))
        
        # Add general follow-ups if no specific services or limited specific follow-ups
        if len(follow_ups) < 2:
            follow_ups.extend(self._get_general_follow_ups(state, services_used, already_asked))
        
        # Return max 3 unique follow-ups
        return list(dict.fromkeys(follow_ups))[:3]
    
    def _get_classification_follow_ups(self, state: WorkflowState, already_asked) -> List[str]:
        """Generate follow-ups for plant disease classification"""
        follow_ups = []
        disease_name = state.get("disease_name", "")
        classification_results = state.get("classification_results", {})
        confidence = classification_results.get("confidence", 0) * 100 if classification_results else 0
        
        if disease_name and disease_name.lower() != "healthy":
            if not already_asked(["treatment", "medicine", "prescription"]):
                follow_ups.append("💊 Get treatment recommendations for this disease")
            if not already_asked(["vendor", "supplier", "buy"]) and confidence >= 75:
                follow_ups.append("🛒 Find suppliers for treatments")
        else:
            if not already_asked(["prevention", "care", "maintenance"]):
                follow_ups.append("🌱 Get preventive care tips")
                
        return follow_ups
    
    def _get_prescription_follow_ups(self, state: WorkflowState, already_asked) -> List[str]:
        """Generate follow-ups for prescription/treatment"""
        follow_ups = []
        treatments = state.get("treatment_recommendations", [])
        
        if not already_asked(["vendor", "supplier", "buy"]):
            follow_ups.append("🛒 Find suppliers for these treatments")
        if not already_asked(["application", "dosage", "how to apply"]):
            follow_ups.append("📋 Get application instructions")
        if not already_asked(["monitor", "track", "effectiveness"]):
            follow_ups.append("📊 Learn about treatment monitoring")
            
        return follow_ups
    
    def _get_insurance_follow_ups(self, state: WorkflowState, already_asked) -> List[str]:
        """Generate follow-ups for insurance services"""
        follow_ups = []
        farmer_name = state.get("farmer_name", "Farmer")
        crop = state.get("plant_type", "crop")
        
        if not already_asked(["more insurance", "other crops", "additional"]):
            follow_ups.append("🛡️ Get insurance for other crops")
        if not already_asked(["companies", "compare", "rates"]):
            follow_ups.append("🏢 Compare insurance companies")
        if not already_asked(["certificate", "document", "policy"]):
            follow_ups.append("📄 Generate insurance certificate")
            
        return follow_ups
    
    def _get_vendor_follow_ups(self, state: WorkflowState, already_asked) -> List[str]:
        """Generate follow-ups for vendor/supplier services"""
        follow_ups = []
        vendor_count = len(state.get("vendor_options", []))
        
        if not already_asked(["pricing", "cost", "price"]):
            follow_ups.append("💰 Compare vendor pricing")
        if not already_asked(["location", "nearby", "delivery"]):
            follow_ups.append("📍 Find vendors in other locations")
        if not already_asked(["contact", "order", "purchase"]):
            follow_ups.append("📞 Get vendor contact information")
            
        return follow_ups
    
    def _get_general_follow_ups(self, state: WorkflowState, services_used: Dict[str, bool], already_asked) -> List[str]:
        """Generate general follow-ups based on context and services not yet used"""
        follow_ups = []
        plant_type = state.get("plant_type", "")
        location = state.get("location", "")
        
        # Suggest services not yet used
        if not services_used["classification"] and not already_asked(["analyze", "diagnose", "disease"]):
            follow_ups.append("📸 Upload plant image for disease diagnosis")
        if not services_used["insurance"] and not already_asked(["insurance", "protection"]):
            follow_ups.append("🛡️ Get crop insurance quotes")
        if not services_used["prescription"] and plant_type and not already_asked(["treatment", "care"]):
            follow_ups.append(f"💊 Get care recommendations for {plant_type}")
        if not services_used["vendors"] and not already_asked(["supplier", "buy"]):
            follow_ups.append("🛒 Find agricultural suppliers")
        
        # General agricultural topics
        if not already_asked(["weather", "season", "climate"]):
            follow_ups.append("🌤️ Get weather-based farming advice")
        if not already_asked(["soil", "nutrients", "fertilizer"]):
            follow_ups.append("🧪 Learn about soil health")
            
        return follow_ups
