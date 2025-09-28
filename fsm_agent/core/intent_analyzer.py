"""
Centralized Intent Analyzer for Agricultural Services

This module provides a configurable, extensible way to analyze user intents
without coupling specific service logic to individual nodes.
"""

import re
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class IntentRule:
    """Configuration for intent detection rules"""
    service: str
    keywords: List[str]
    exclusions: List[str]
    context_required: List[str]
    priority: int = 0


class AgricultureIntentAnalyzer:
    """
    Centralized intent analyzer that can be configured and extended
    without modifying individual nodes.
    """
    
    def __init__(self):
        self.intent_rules = self._load_default_rules()
    
    def _load_default_rules(self) -> List[IntentRule]:
        """Load default intent detection rules"""
        return [
            # Insurance intent rules
            IntentRule(
                service="insurance",
                keywords=["insurance", "premium", "coverage", "policy", "crop insurance"],
                exclusions=[],
                context_required=[],
                priority=10
            ),
            IntentRule(
                service="insurance", 
                keywords=["buy", "purchase"],
                exclusions=["pesticide", "fungicide", "fertilizer", "equipment", "supplies"],
                context_required=["insurance", "policy", "coverage", "crop"],
                priority=8
            ),
            
            # Vendor intent rules  
            IntentRule(
                service="vendor",
                keywords=["buy", "purchase", "shop", "vendor"],
                exclusions=["insurance", "policy", "coverage"],
                context_required=["pesticide", "fungicide", "fertilizer", "equipment", "supplies", "chemical"],
                priority=7
            ),
            
            # Treatment intent rules
            IntentRule(
                service="treatment",
                keywords=["treatment", "cure", "medicine", "prescription"],
                exclusions=["buy", "purchase", "vendor"],
                context_required=[],
                priority=9
            ),
            
            # Classification intent rules
            IntentRule(
                service="classification", 
                keywords=["diagnose", "identify", "disease", "classify"],
                exclusions=[],
                context_required=[],
                priority=9
            )
        ]
    
    def analyze_intent(self, user_message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze user intent using configurable rules
        
        Args:
            user_message: User's input message
            context: Additional context (state, previous actions, etc.)
            
        Returns:
            Dictionary with detected intents and confidence scores
        """
        user_message_lower = user_message.lower()
        detected_intents = {}
        
        for rule in sorted(self.intent_rules, key=lambda r: r.priority, reverse=True):
            confidence = self._evaluate_rule(rule, user_message_lower)
            
            if confidence > 0:
                if rule.service not in detected_intents or confidence > detected_intents[rule.service]:
                    detected_intents[rule.service] = confidence
        
        return detected_intents
    
    def _evaluate_rule(self, rule: IntentRule, user_message: str) -> float:
        """Evaluate a single intent rule against user message"""
        confidence = 0.0
        
        # Check for required keywords
        keyword_matches = sum(1 for keyword in rule.keywords if keyword in user_message)
        if keyword_matches == 0:
            return 0.0
        
        confidence += keyword_matches * 0.3
        
        # Check exclusions (reduce confidence)
        exclusion_matches = sum(1 for exclusion in rule.exclusions if exclusion in user_message)
        confidence -= exclusion_matches * 0.2
        
        # Check context requirements (boost confidence)
        if rule.context_required:
            context_matches = sum(1 for context in rule.context_required if context in user_message)
            if context_matches > 0:
                confidence += context_matches * 0.2
            else:
                # If context is required but not found, reduce confidence significantly
                confidence *= 0.5
        
        return max(0.0, min(1.0, confidence))
    
    def get_primary_intent(self, user_message: str, context: Dict[str, Any] = None) -> str:
        """Get the primary (highest confidence) intent"""
        intents = self.analyze_intent(user_message, context)
        
        if not intents:
            return "general"
        
        return max(intents.items(), key=lambda x: x[1])[0]
    
    def add_custom_rule(self, rule: IntentRule):
        """Add a custom intent rule for extensibility"""
        self.intent_rules.append(rule)
    
    def should_route_to_vendor(self, user_message: str) -> bool:
        """
        Determine if user wants vendor services
        (Keeping this method for backward compatibility, but it's now rule-based)
        """
        intents = self.analyze_intent(user_message)
        return intents.get("vendor", 0) > intents.get("insurance", 0)


# Global instance for easy access
intent_analyzer = AgricultureIntentAnalyzer()
