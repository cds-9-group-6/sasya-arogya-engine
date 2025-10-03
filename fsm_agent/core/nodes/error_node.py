"""
Error Node for FSM Agent workflow
Handles errors
"""

import logging

from .base_node import BaseNode

try:
    from ..workflow_state import WorkflowState, add_message_to_state, mark_complete
except ImportError:
    from ..workflow_state import WorkflowState, add_message_to_state, mark_complete

logger = logging.getLogger(__name__)


class ErrorNode(BaseNode):
    """Error node - handles errors"""
    
    @property
    def node_name(self) -> str:
        return "error"
    
    async def execute(self, state: WorkflowState) -> WorkflowState:
        """
        Execute error node logic with improved error messages
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        self.update_node_state(state)
        
        error_msg = state.get("error_message", "An unknown error occurred")
        
        # Provide user-friendly error messages for specific error types
        user_message = self._format_user_friendly_error(error_msg)
        
        add_message_to_state(state, "assistant", user_message)
        
        mark_complete(state)
        return state
    
    def _format_user_friendly_error(self, error_msg: str) -> str:
        """Format error messages to be more user-friendly"""
        error_lower = error_msg.lower()
        
        # MCP server errors (insurance service)
        if "mcp" in error_lower and ("server" in error_lower or "not available" in error_lower):
            return ("⚠️ **INSURANCE SERVICE TEMPORARILY UNAVAILABLE**\n\n"
                   "Our crop insurance service is currently experiencing technical difficulties. "
                   "Please try again in a few minutes, or feel free to ask about plant diagnosis "
                   "and treatment recommendations in the meantime.")
        
        # Classification/ML model errors
        elif "model" in error_lower and ("loading" in error_lower or "unavailable" in error_lower):
            return ("⚠️ **PLANT DIAGNOSIS TEMPORARILY UNAVAILABLE**\n\n"
                   "Our plant disease detection system is currently being updated. "
                   "Please try uploading your plant image again in a few minutes.")
        
        # Image processing errors
        elif "image" in error_lower and ("processing" in error_lower or "failed" in error_lower):
            return ("⚠️ **IMAGE PROCESSING ISSUE**\n\n"
                   "We had trouble analyzing your plant image. Please try uploading a clearer photo "
                   "with good lighting, or try a different image.")
        
        # Network/connection errors
        elif any(keyword in error_lower for keyword in ["connection", "timeout", "network", "unreachable"]):
            return ("⚠️ **CONNECTION ISSUE**\n\n"
                   "We're experiencing connectivity issues. Please check your internet connection "
                   "and try again. If the problem persists, our services may be temporarily unavailable.")
        
        # LLM/AI service errors
        elif "llm" in error_lower or "ai" in error_lower or "generation" in error_lower:
            return ("⚠️ **AI SERVICE TEMPORARILY UNAVAILABLE**\n\n"
                   "Our AI-powered recommendation system is currently experiencing issues. "
                   "Please try again in a few minutes.")
        
        # Tool/service specific errors
        elif "tool" in error_lower and "not available" in error_lower:
            return ("⚠️ **SERVICE TEMPORARILY UNAVAILABLE**\n\n"
                   "One of our services is currently undergoing maintenance. "
                   "Please try again shortly or contact support if the issue continues.")
        
        # Generic technical errors
        elif any(keyword in error_lower for keyword in ["failed", "error", "exception", "unable"]):
            return ("⚠️ **TEMPORARY SERVICE ISSUE**\n\n"
                   f"We encountered a technical issue: {error_msg}\n\n"
                   "Please try your request again. If the problem continues, "
                   "please contact our support team for assistance.")
        
        # Fallback for unknown errors
        else:
            return ("❌ **UNEXPECTED ERROR**\n\n"
                   f"An unexpected issue occurred: {error_msg}\n\n"
                   "Please try again or contact support if the issue persists.")
