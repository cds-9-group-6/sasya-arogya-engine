"""
Insurance Tool for LangGraph Workflow

This tool integrates with Sasya Arogya MCP server to provide crop insurance functionality.
"""

import asyncio
import logging
import os
from typing import Dict, Any, Optional

import requests
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class InsuranceInput(BaseModel):
    """Input schema for insurance tool"""
    disease: Optional[str] = Field(default=None, description="Name of the plant disease affecting the crop (optional)")
    farmer_name: Optional[str] = Field(default="Farmer", description="Name of the farmer (optional)")
    state: str = Field(description="State where the farmer is located")
    area_hectare: float = Field(description="Area of cultivation in hectares")
    crop: str = Field(description="Name of the crop being cultivated")
    action: str = Field(description="Insurance action: 'calculate_premium', 'get_companies', 'recommend', 'generate_certificate'")
    session_id: Optional[str] = Field(default="unknown", description="Session ID for tracking")


class InsuranceTool(BaseTool):
    """
    Tool for handling crop insurance operations using Sasya Arogya MCP server
    """
    name: str = "crop_insurance_manager"
    description: str = "Manages crop insurance operations including premium calculation, recommendations, and certificate generation"
    args_schema: type[BaseModel] = InsuranceInput
    
    # Declare the MCP server URL field properly
    mcp_server_url: str = Field(default_factory=lambda: os.getenv("SASYA_AROGYA_MCP_URL", "http://localhost:8001"), exclude=True)
    
    def __init__(self, **data):
        super().__init__(**data)
        self._init_mcp_client()
    
    def _init_mcp_client(self):
        """Initialize MCP client and validate server connection"""
        try:
            # Test connection to MCP server
            response = requests.get(f"{self.mcp_server_url}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                logger.info(f"✅ Sasya Arogya MCP server connection established successfully: {health_data.get('status', 'healthy')}")
            else:
                logger.warning(f"Sasya Arogya MCP server responded with status {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to Sasya Arogya MCP server at {self.mcp_server_url}: {str(e)}")
            logger.error("💡 Suggestion: Ensure Sasya Arogya MCP server is running and accessible, or set SASYA_AROGYA_MCP_URL environment variable")
    
    async def _arun(self, mlflow_manager=None, **kwargs) -> Dict[str, Any]:
        """Async implementation"""
        return await asyncio.to_thread(self._run, mlflow_manager=mlflow_manager, **kwargs)
    
    def _run(self, mlflow_manager=None, **kwargs) -> Dict[str, Any]:
        """
        Run the insurance tool with MLflow tracking
        
        Args:
            mlflow_manager: MLflow manager instance (passed by node)
            **kwargs: Tool input parameters
        
        Returns:
            Dictionary containing insurance operation result or error
        """
        session_id = kwargs.get("session_id", "unknown")
        
        try:
            # Verify MLflow manager is available (but don't start/end runs)
            if mlflow_manager and not mlflow_manager.is_available():
                logger.warning("MLflow manager not available for metrics logging")
                mlflow_manager = None
            
            # Validate required parameters
            action = kwargs.get("action")
            if not action:
                error_msg = "No action specified for insurance operation"
                if mlflow_manager:
                    mlflow_manager.log_error(session_id, "validation_error", error_msg)
                return {"error": error_msg}
            
            # Test MCP server availability
            try:
                requests.get(f"{self.mcp_server_url}/health", timeout=2)
            except requests.exceptions.RequestException:
                error_msg = "Sasya Arogya MCP server not available"
                if mlflow_manager:
                    mlflow_manager.log_error(session_id, "mcp_server_unavailable", error_msg)
                return {"error": error_msg}
            
            # Log insurance context to MLflow
            if mlflow_manager:
                try:
                    import mlflow
                    mlflow.log_param("insurance_action", action)
                    mlflow.log_param("insurance_crop", kwargs.get("crop", "unknown"))
                    mlflow.log_param("insurance_state", kwargs.get("state", "unknown"))
                    mlflow.log_param("insurance_area", kwargs.get("area_hectare", 0))
                except Exception as e:
                    logger.warning(f"Failed to log insurance context: {e}")
            
            # Execute the appropriate insurance operation
            result = None
            if action == "calculate_premium":
                result = self._calculate_premium(**kwargs)
            elif action == "get_companies":
                result = self._get_insurance_companies(**kwargs)
            elif action == "recommend":
                result = self._recommend_insurance(**kwargs)
            elif action == "generate_certificate":
                result = self._generate_certificate(**kwargs)
            else:
                return {"error": f"Unknown insurance action: {action}"}
            
            # Log success to MLflow
            if mlflow_manager and result and not result.get("error"):
                try:
                    import mlflow
                    mlflow.log_metric("insurance_operation_success", 1)
                    mlflow.log_param("insurance_final_source", "mcp_server")
                except Exception as e:
                    logger.warning(f"Failed to log insurance success: {e}")
            
            logger.info(f"Insurance operation '{action}' completed for session {session_id}")
            return result
                
        except Exception as e:
            error_msg = f"Insurance operation error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            # Log error to MLflow if available
            if mlflow_manager:
                try:
                    mlflow_manager.log_error(session_id, "insurance_error", error_msg)
                except:
                    pass
            
            return {"error": error_msg}
    
    def _calculate_premium(self, **kwargs) -> Dict[str, Any]:
        """Calculate insurance premium for crop"""
        try:
            # Prepare MCP tool call payload
            mcp_payload = {
                "name": "calculate_crop_premium",
                "arguments": {
                    "crop": kwargs.get("crop"),
                    "area_hectare": kwargs.get("area_hectare"),
                    "state": kwargs.get("state")
                }
            }
            
            logger.info(f"🔍 Calculating premium via MCP server for crop: {kwargs.get('crop')}, area: {kwargs.get('area_hectare')} hectares, state: {kwargs.get('state')}")
            
            # Make HTTP request to MCP server
            response = requests.post(
                f"{self.mcp_server_url}/tools/call",
                json=mcp_payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code != 200:
                raise Exception(f"MCP server HTTP {response.status_code}: {response.text}")
            
            # Process MCP response
            mcp_response = response.json()
            
            if mcp_response.get("isError"):
                error_msg = "MCP server returned error"
                if mcp_response.get("content"):
                    error_msg = mcp_response["content"][0].get("text", error_msg)
                raise Exception(error_msg)
            
            # Extract response content
            content = mcp_response.get("content", [])
            if content and content[0].get("type") == "text":
                premium_text = content[0]["text"]
                
                return {
                    "action": "calculate_premium",
                    "success": True,
                    "premium_details": premium_text,
                    "crop": kwargs.get("crop"),
                    "area_hectare": kwargs.get("area_hectare"),
                    "state": kwargs.get("state"),
                    "raw_mcp_response": mcp_response
                }
            else:
                raise Exception("Invalid response format from MCP server")
                
        except Exception as e:
            logger.error(f"Premium calculation failed: {str(e)}")
            return {"error": f"Premium calculation failed: {str(e)}"}
    
    def _get_insurance_companies(self, **kwargs) -> Dict[str, Any]:
        """Get available insurance companies"""
        try:
            # Prepare MCP tool call payload
            mcp_payload = {
                "name": "get_insurance_companies",
                "arguments": {
                    "state": kwargs.get("state")
                }
            }
            
            logger.info(f"🔍 Getting insurance companies via MCP server for state: {kwargs.get('state')}")
            
            # Make HTTP request to MCP server
            response = requests.post(
                f"{self.mcp_server_url}/tools/call",
                json=mcp_payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code != 200:
                raise Exception(f"MCP server HTTP {response.status_code}: {response.text}")
            
            # Process MCP response
            mcp_response = response.json()
            
            if mcp_response.get("isError"):
                error_msg = "MCP server returned error"
                if mcp_response.get("content"):
                    error_msg = mcp_response["content"][0].get("text", error_msg)
                raise Exception(error_msg)
            
            # Extract response content
            content = mcp_response.get("content", [])
            if content and content[0].get("type") == "text":
                companies_text = content[0]["text"]
                
                return {
                    "action": "get_companies",
                    "success": True,
                    "companies": companies_text,
                    "state": kwargs.get("state"),
                    "raw_mcp_response": mcp_response
                }
            else:
                raise Exception("Invalid response format from MCP server")
                
        except Exception as e:
            logger.error(f"Getting insurance companies failed: {str(e)}")
            return {"error": f"Getting insurance companies failed: {str(e)}"}
    
    def _recommend_insurance(self, **kwargs) -> Dict[str, Any]:
        """Recommend insurance for farmer based on crop and optional disease"""
        try:
            # Prepare MCP tool call payload
            disease = kwargs.get("disease")
            farmer_name = kwargs.get("farmer_name") or "Farmer"
            
            arguments = {
                "farmer_name": farmer_name,
                "state": kwargs.get("state"),
                "area_hectare": kwargs.get("area_hectare"),
                "crop": kwargs.get("crop")
            }
            
            # Only include disease if it's provided and not empty
            if disease and disease.strip():
                arguments["disease"] = disease
                
            mcp_payload = {
                "name": "recommend_insurance",
                "arguments": arguments
            }
            
            disease_info = disease if disease else "general coverage"
            logger.info(f"🔍 Getting insurance recommendation via MCP server for farmer: {farmer_name}, crop: {kwargs.get('crop')}, coverage: {disease_info}")
            
            # Make HTTP request to MCP server
            response = requests.post(
                f"{self.mcp_server_url}/tools/call",
                json=mcp_payload,
                headers={"Content-Type": "application/json"},
                timeout=60  # Longer timeout for PDF generation
            )
            
            if response.status_code != 200:
                raise Exception(f"MCP server HTTP {response.status_code}: {response.text}")
            
            # Process MCP response
            mcp_response = response.json()
            
            if mcp_response.get("isError"):
                error_msg = "MCP server returned error"
                if mcp_response.get("content"):
                    error_msg = mcp_response["content"][0].get("text", error_msg)
                raise Exception(error_msg)
            
            # Extract response content
            content = mcp_response.get("content", [])
            result = {
                "action": "recommend",
                "success": True,
                "farmer_name": kwargs.get("farmer_name"),
                "crop": kwargs.get("crop"),
                "disease": kwargs.get("disease"),
                "state": kwargs.get("state"),
                "area_hectare": kwargs.get("area_hectare"),
                "recommendation_text": "",
                "pdf_generated": False,
                "raw_mcp_response": mcp_response
            }
            
            # Process both text and PDF resources
            for item in content:
                if item.get("type") == "text":
                    result["recommendation_text"] = item["text"]
                elif item.get("type") == "resource" and item.get("mimeType") == "application/pdf":
                    result["pdf_generated"] = True
                    result["pdf_uri"] = item.get("uri")
                    result["pdf_size"] = len(item.get("uri", "").encode()) if item.get("uri") else 0
            
            return result
                
        except Exception as e:
            logger.error(f"Insurance recommendation failed: {str(e)}")
            return {"error": f"Insurance recommendation failed: {str(e)}"}
    
    def _generate_certificate(self, **kwargs) -> Dict[str, Any]:
        """Generate insurance certificate PDF via MCP server"""
        try:
            # Extract required parameters
            farmer_name = kwargs.get("farmer_name", "Farmer")
            crop = kwargs.get("crop")
            area_hectare = kwargs.get("area_hectare")
            state = kwargs.get("state")
            disease = kwargs.get("disease")
            
            # Validate required parameters
            if not all([farmer_name, crop, area_hectare, state]):
                raise ValueError("Missing required parameters: farmer_name, crop, area_hectare, state")
            
            # Prepare MCP tool call payload
            mcp_payload = {
                "name": "generate_insurance_certificate",
                "arguments": {
                    "farmer_name": farmer_name,
                    "state": state,
                    "area_hectare": area_hectare,
                    "crop": crop,
                    "disease": disease
                }
            }
            
            logger.info(f"🔍 Generating insurance certificate via MCP server for farmer: {farmer_name}, crop: {crop}, state: {state}")
            
            # Make HTTP request to MCP server
            response = requests.post(
                f"{self.mcp_server_url}/tools/call",
                json=mcp_payload,
                headers={"Content-Type": "application/json"},
                timeout=60  # Longer timeout for PDF generation
            )
            
            if response.status_code != 200:
                raise Exception(f"MCP server HTTP {response.status_code}: {response.text}")
            
            # Process MCP response
            mcp_response = response.json()
            
            if mcp_response.get("isError"):
                error_msg = "MCP server returned error"
                if mcp_response.get("content"):
                    error_msg = mcp_response["content"][0].get("text", error_msg)
                raise Exception(error_msg)
            
            # Extract response content
            content = mcp_response.get("content", [])
            result = {
                "action": "generate_certificate",
                "success": True,
                "farmer_name": farmer_name,
                "crop": crop,
                "area_hectare": area_hectare,
                "state": state,
                "disease": disease,
                "pdf_generated": False,
                "premium_details": "",  # Initialize premium_details
                "raw_mcp_response": mcp_response
            }
            
            # Process both text and PDF resources from MCP response
            for item in content:
                if item.get("type") == "text":
                    # Include any additional text response from the server
                    result["server_response"] = item["text"]
                    # Extract premium details from text response if available
                    if "premium" in item["text"].lower() or "₹" in item["text"]:
                        result["premium_details"] = item["text"]
                elif item.get("type") == "resource":
                    if item.get("mimeType") == "application/pdf":
                        result["pdf_generated"] = True
                        result["pdf_uri"] = item.get("uri")
                        result["pdf_name"] = item.get("name", f"insurance_certificate_{farmer_name}_{crop}.pdf")
                        # Calculate approximate size
                        if item.get("uri"):
                            result["pdf_size"] = len(item["uri"].encode()) if isinstance(item["uri"], str) else 0
                    
                    # Extract premium details from resource metadata or description
                    resource_text = item.get("text", "") or item.get("description", "") or item.get("name", "")
                    if resource_text and ("premium" in resource_text.lower() or "₹" in resource_text):
                        result["premium_details"] = resource_text
            
            # If no premium details found, provide a fallback message
            if not result["premium_details"]:
                result["premium_details"] = f"Premium details for {crop} in {state} - Contact insurance provider for specific rates"
            
            return result
                
        except Exception as e:
            logger.error(f"Certificate generation failed: {str(e)}")
            return {
                "action": "generate_certificate", 
                "success": False,
                "error": f"Certificate generation failed: {str(e)}",
                "suggestion": "Please ensure you have completed premium calculation first, and that all required information (farmer name, crop, area, state) is provided."
            }


# Async wrapper for compatibility
async def run_insurance_tool(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Async wrapper for the insurance tool
    
    Args:
        input_data: Dictionary containing insurance operation parameters
    
    Returns:
        Insurance operation result or error
    """
    tool = InsuranceTool()
    return await tool._arun(**input_data)
