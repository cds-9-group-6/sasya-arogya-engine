"""
Response Configuration for FSM Agent
Centralized, configurable response templates for different scenarios
"""

from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass
import random


class ResponseType(Enum):
    """Types of standardized responses"""
    OUT_OF_SCOPE = "out_of_scope"
    NO_GOOD_ANSWER = "no_good_answer"
    INSUFFICIENT_INFO = "insufficient_info"
    ERROR_FALLBACK = "error_fallback"
    AGRICULTURE_REDIRECT = "agriculture_redirect"


@dataclass
class ResponseTemplate:
    """Template for generating responses"""
    templates: List[str]
    tone: str = "helpful"
    include_suggestions: bool = True
    category: str = "general"


class ResponseConfigManager:
    """Manages response templates and generation"""
    
    def __init__(self):
        self.templates = self._load_default_templates()
        self.agriculture_topics = self._load_agriculture_topics()
    
    def _load_default_templates(self) -> Dict[ResponseType, ResponseTemplate]:
        """Load default response templates"""
        return {
            ResponseType.OUT_OF_SCOPE: ResponseTemplate(
                templates=[
                    "I'm sorry, but I can only help with crop care and agricultural questions. Could you please ask me something related to plant diseases, farming, or crop management?",
                    "I apologize, but I'm specialized in agricultural assistance. Please feel free to ask me about plant diseases, crop care, treatment recommendations, or farming-related topics.",
                    "Sorry, I'm only able to answer questions on crop care and agricultural matters. Is there anything related to farming or plant health I can help you with?",
                    "I'm designed to assist with agricultural questions only. Please ask me about plant diseases, farming techniques, crop insurance, or treatment recommendations.",
                    "I can only provide assistance with crop care, plant diseases, and agricultural topics. Could you rephrase your question to focus on farming or plant health?",
                ],
                tone="apologetic_helpful",
                include_suggestions=True,
                category="scope_limitation"
            ),
            
            ResponseType.NO_GOOD_ANSWER: ResponseTemplate(
                templates=[
                    "I don't have enough information to provide a reliable answer about this agricultural topic. Could you provide more details about your specific crop or farming situation?",
                    "I'm unable to give you a confident answer on this particular farming question. Can you share more context about your crops or agricultural needs?",
                    "I don't have sufficient knowledge about this specific agricultural issue. Could you provide more details or ask about a different aspect of crop care?",
                    "This agricultural question is outside my current knowledge base. I'd be happy to help with plant disease diagnosis, treatment recommendations, or general crop care instead.",
                ],
                tone="honest_helpful",
                include_suggestions=True,
                category="knowledge_limitation"
            ),
            
            ResponseType.INSUFFICIENT_INFO: ResponseTemplate(
                templates=[
                    "I need more information to help you effectively. Could you provide details about your specific crop, location, or the farming issue you're experiencing?",
                    "To give you the best agricultural advice, I need more details. What type of crop are you growing, and what specific issue are you facing?",
                    "I'd like to help, but I need more context. Can you tell me more about your plants, farming situation, or the specific problem you're encountering?",
                ],
                tone="helpful",
                include_suggestions=False,
                category="information_request"
            ),
            
            ResponseType.AGRICULTURE_REDIRECT: ResponseTemplate(
                templates=[
                    "I can help you with crop care and agricultural questions! I can assist with plant disease diagnosis, treatment recommendations, crop insurance, and connecting you with agricultural suppliers.",
                    "I specialize in agricultural assistance. I can help diagnose plant diseases, recommend treatments, provide crop insurance information, and find agricultural suppliers for you.",
                    "I'm here to help with farming and crop care! I can identify plant diseases, suggest treatments, calculate crop insurance premiums, and connect you with agricultural vendors.",
                ],
                tone="welcoming",
                include_suggestions=True,
                category="capability_showcase"
            )
        }
    
    def _load_agriculture_topics(self) -> List[str]:
        """Load list of agricultural topics for suggestions"""
        return [
            "plant disease diagnosis",
            "crop treatment recommendations", 
            "farming techniques",
            "soil health",
            "pest management",
            "crop insurance information",
            "agricultural supplier recommendations",
            "fertilizer advice",
            "irrigation guidance",
            "crop rotation planning",
            "seasonal farming tips",
            "organic farming methods",
            "plant nutrition",
            "disease prevention",
            "harvest timing"
        ]
    
    def get_response(self, response_type: ResponseType, 
                    context: Optional[Dict] = None,
                    include_suggestions: Optional[bool] = None) -> str:
        """
        Generate a response based on type and context
        
        Args:
            response_type: Type of response needed
            context: Additional context for response generation
            include_suggestions: Override template suggestion setting
            
        Returns:
            Generated response string
        """
        template = self.templates.get(response_type)
        if not template:
            return self._get_fallback_response()
        
        # Select a random template variation
        base_response = random.choice(template.templates)
        
        # Add suggestions if enabled
        should_include_suggestions = (
            include_suggestions if include_suggestions is not None 
            else template.include_suggestions
        )
        
        if should_include_suggestions and response_type == ResponseType.OUT_OF_SCOPE:
            suggestions = self._get_agriculture_suggestions()
            base_response += f"\n\nI can help you with topics like: {suggestions}"
        
        return base_response
    
    def _get_agriculture_suggestions(self, count: int = 3) -> str:
        """Get a random selection of agriculture topic suggestions"""
        selected_topics = random.sample(self.agriculture_topics, min(count, len(self.agriculture_topics)))
        return ", ".join(selected_topics)
    
    def _get_fallback_response(self) -> str:
        """Fallback response when no template is found"""
        return "I apologize, but I can only assist with agricultural and crop care related questions. Please feel free to ask me about plant diseases, farming techniques, or crop management."
    
    def is_agriculture_related(self, user_message: str) -> Dict[str, any]:
        """
        Determine if a user message is agriculture-related
        
        Args:
            user_message: The user's input message
            
        Returns:
            Dictionary with analysis results
        """
        agriculture_keywords = [
            # Basic farming terms
            "crop", "plant", "farm", "agriculture", "farming", "grow", "growing", 
            "harvest", "seed", "seeds", "soil", "garden", "gardening",
            
            # Disease and health terms
            "disease", "pest", "bug", "insect", "fungus", "infection", "blight",
            "rot", "wilt", "mold", "damage", "sick", "dying", "yellow", "brown",
            "spots", "leaves", "leaf", "stem", "root",
            
            # Treatment terms
            "treatment", "cure", "medicine", "pesticide", "fungicide", "fertilizer",
            "organic", "spray", "application", "dosage",
            
            # Crop types
            "tomato", "potato", "wheat", "rice", "corn", "soybean", "cotton",
            "apple", "grape", "citrus", "vegetable", "fruit", "grain",
            
            # Insurance terms
            "insurance", "premium", "coverage", "policy", "protection",
            
            # Vendor terms
            "supplier", "vendor", "buy", "purchase", "equipment", "tools"
        ]
        
        non_agriculture_indicators = [
            # Technology
            "computer", "software", "app", "website", "internet", "email", "phone",
            "technology", "digital", "online", "programming", "code", "data",
            
            # Medical/Health (human)
            "doctor", "medicine", "hospital", "health", "sick", "pain", "medical",
            "human", "person", "body", "patient",
            
            # Entertainment
            "movie", "music", "game", "entertainment", "sport", "book", "tv",
            
            # Other domains
            "weather", "travel", "cooking", "recipe", "car", "vehicle", "house",
            "finance", "money", "business", "job", "work", "school", "education"
        ]
        
        message_lower = user_message.lower()
        
        # Count agriculture-related terms
        ag_matches = sum(1 for keyword in agriculture_keywords if keyword in message_lower)
        non_ag_matches = sum(1 for keyword in non_agriculture_indicators if keyword in message_lower)
        
        # Calculate confidence
        total_matches = ag_matches + non_ag_matches
        if total_matches == 0:
            confidence = 0.3  # Neutral for unclear messages
            is_agricultural = None
        elif ag_matches > non_ag_matches:
            confidence = ag_matches / (total_matches + 3)  # Boost agriculture
            is_agricultural = True
        else:
            confidence = non_ag_matches / (total_matches + 1)
            is_agricultural = False
        
        return {
            "is_agricultural": is_agricultural,
            "confidence": min(1.0, confidence),
            "agriculture_matches": ag_matches,
            "non_agriculture_matches": non_ag_matches,
            "total_keywords": total_matches
        }
    
    def add_custom_template(self, response_type: ResponseType, template: ResponseTemplate):
        """Add or update a custom response template"""
        self.templates[response_type] = template
    
    def add_agriculture_topics(self, topics: List[str]):
        """Add custom agriculture topics for suggestions"""
        self.agriculture_topics.extend(topics)


# Global instance for easy access
response_config = ResponseConfigManager()
