"""
Prescription Tool for LangGraph Workflow

This tool generates treatment prescriptions using Prescription Engine HTTP API for recommendations.
"""

import asyncio
import logging
import os
import sys
from typing import Dict, Any, Optional, List

import requests
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

# Add the parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "../../.."))

logger = logging.getLogger(__name__)


class PrescriptionInput(BaseModel):
    """Input schema for prescription tool"""
    disease_name: str = Field(description="Name of the diagnosed disease")
    plant_type: Optional[str] = Field(default=None, description="Type of plant")
    location: Optional[str] = Field(default=None, description="Location for regional recommendations")
    season: Optional[str] = Field(default=None, description="Current season")
    severity: Optional[str] = Field(default="Medium", description="Disease severity level")
    user_context: Optional[Dict[str, Any]] = Field(default={}, description="Additional user context")
    session_id: Optional[str] = Field(default="unknown", description="Session ID for MLflow tracking")


class PrescriptionTool(BaseTool):
    """
    Tool for generating treatment prescriptions using Ollama via HTTP API
    """
    name: str = "prescription_generator"
    description: str = "Generates treatment prescriptions and recommendations for plant diseases using Ollama HTTP API"
    args_schema: type[BaseModel] = PrescriptionInput
    
    # Declare the ollama_base_url field properly
    prescription_engine_url: str = Field(default_factory=lambda: os.getenv("PRESCRIPTION_ENGINE_URL", "http://localhost:8081"), exclude=True)
    
    def __init__(self, **data):
        super().__init__(**data)
        self._init_http_client()
    
    def _init_http_client(self):
        """Initialize HTTP client and validate Ollama connection"""
        try:
            # Test connection to Ollama server
            response = requests.get(f"{self.prescription_engine_url}/health", timeout=5)
            if response.status_code == 200:
                logger.info("✅ Prescription Engine HTTP connection established successfully")
            else:
                logger.warning(f"Prescription Engine responded with status {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to Prescription Engine  at {self.prescription_engine_url}: {str(e)}")
            logger.error("💡 Suggestion: Ensure Prescription Engine is running and accessible, or set PRESCRIPTION_ENGINE_URL environment variable")
    
    async def _arun(self, mlflow_manager=None, **kwargs) -> Dict[str, Any]:
        """Async implementation"""
        return await asyncio.to_thread(self._run, mlflow_manager=mlflow_manager, **kwargs)
    
    def _run(self, mlflow_manager=None, **kwargs) -> Dict[str, Any]:
        """
        Run the prescription tool with MLflow tracking
        
        Args:
            mlflow_manager: MLflow manager instance (passed by node)
            **kwargs: Tool input parameters
        
        Returns:
            Dictionary containing prescription data or error
        """
        session_id = kwargs.get("session_id", "unknown")
        
        try:
            # Verify MLflow manager is available (but don't start/end runs)
            if mlflow_manager and not mlflow_manager.is_available():
                logger.warning("MLflow manager not available for metrics logging")
                mlflow_manager = None
            # Validate input
            disease_name = kwargs.get("disease_name")
            if not disease_name:
                error_msg = "No disease name provided"
                if mlflow_manager:
                    mlflow_manager.log_error(session_id, "validation_error", error_msg)
                return {"error": error_msg}
            
            # Test Ollama connection availability
            try:
                requests.get(f"{self.prescription_engine_url}/api/tags", timeout=2)
            except requests.exceptions.RequestException:
                error_msg = "Prescription Engine not available"
                if mlflow_manager:
                    mlflow_manager.log_error(session_id, "prescription_engine_unavailable", error_msg)
                # Fallback to rule-based recommendations
                return self._generate_fallback_prescription(**kwargs)
            
            # Build query for RAG system
            plant_type = kwargs.get("plant_type", "general")
            location = kwargs.get("location", "")
            season = kwargs.get("season", "")
            severity = kwargs.get("severity", "medium")
            
            # Log plant context to MLflow
            if mlflow_manager:
                try:
                    import mlflow
                    mlflow.log_param("prescription_disease", disease_name)
                    mlflow.log_param("prescription_plant_type", plant_type)
                    if location:
                        mlflow.log_param("prescription_location", location)
                    if season:
                        mlflow.log_param("prescription_season", season)
                    mlflow.log_param("prescription_severity", severity)
                except Exception as e:
                    logger.warning(f"Failed to log prescription context: {e}")
            
            query = f"""
            Disease: {disease_name}
            Plant: {plant_type}
            Location: {location}
            Season: {season}
            Severity: {severity}
            
            Provide comprehensive treatment recommendations including:
            1. Chemical treatments with dosages and application methods
            2. Organic/natural treatment alternatives
            3. Preventive measures
            4. Application timing and frequency
            5. Safety precautions
            6. Expected recovery timeline
            """
            
            # Query Ollama via HTTP API
            try:
                logger.info(f"🔍 Querying Prescription Engine with metadata - plant: {plant_type}, season: {season}, location: {location}, disease: {disease_name}")
                
                # Prepare the request payload for /query/treatment endpoint
                request_payload = {
                    "query": query,
                    "plant_type": plant_type,
                    "season": season,
                    "location": location,
                    "disease": disease_name,
                    "session_id": session_id
                }
                
                # Make HTTP request to /query/treatment endpoint
                response = requests.post(
                    f"{self.prescription_engine_url}/query/metrics",
                    json=request_payload,
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
                
                if response.status_code != 200:
                    raise Exception(f"HTTP {response.status_code}: {response.text}")
                
                # Extract response content
                response_data = response.json()
                
                # Check if the response was successful
                if not response_data.get("success", False):
                    raise Exception(f"Prescription Engine returned unsuccessful response: {response_data}")
                
                # Extract the treatment data
                treatment_data = response_data.get("treatment", {})
                if not treatment_data:
                    raise Exception("No treatment data found in response")
                
                # Use the structured response directly instead of parsing text
                prescription_data = self._parse_structured_response(treatment_data, response_data, **kwargs)
                rag_response = response_data.get("raw_response", str(response_data))  # Keep for debugging
                
                # Log prescription generation success
                if mlflow_manager:
                    try:
                        import mlflow
                        mlflow.log_metric("prescription_generation_success", 1)
                        mlflow.log_param("prescription_final_source", "prescription_engine_http")
                    except Exception as e:
                        logger.warning(f"Failed to log prescription success: {e}")
                
                logger.info(f"Prescription generated for {disease_name}")
                return prescription_data
                
            except Exception as e:
                logger.warning(f"Prescription Engine HTTP query failed: {str(e)}. Using fallback prescription.")
                if mlflow_manager:
                    try:
                        import mlflow
                        mlflow_manager.log_error(session_id, "prescription_engine_query_failed", str(e))
                        mlflow.log_metric("prescription_generation_success", 0)
                        mlflow.log_param("prescription_final_source", "fallback")
                    except Exception as log_e:
                        logger.warning(f"Failed to log Prescription Engine failure: {log_e}")
                return self._generate_fallback_prescription(**kwargs)
                
        except Exception as e:
            error_msg = f"Prescription generation error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            # Log error to MLflow if available
            if mlflow_manager:
                try:
                    mlflow_manager.log_error(session_id, "prescription_error", error_msg)
                except:
                    pass
            
            return {"error": error_msg}
    
    def _parse_rag_response(self, rag_response: str, **kwargs) -> Dict[str, Any]:
        """
        Parse RAG response into structured prescription data
        
        Args:
            rag_response: Raw response from RAG system
            **kwargs: Original input parameters
        
        Returns:
            Structured prescription data
        """
        try:
            # Basic parsing - in production, use more sophisticated NLP parsing
            lines = rag_response.split('\n')
            
            treatments = []
            preventive_measures = []
            notes = ""
            
            current_section = None
            current_treatment = {}
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Identify sections
                if "treatment" in line.lower() and ("chemical" in line.lower() or "organic" in line.lower()):
                    current_section = "treatment"
                    if current_treatment:
                        treatments.append(current_treatment)
                        current_treatment = {}
                elif "preventive" in line.lower() or "prevention" in line.lower():
                    current_section = "prevention"
                    if current_treatment:
                        treatments.append(current_treatment)
                        current_treatment = {}
                elif "note" in line.lower() or "important" in line.lower():
                    current_section = "notes"
                
                # Parse content
                if current_section == "treatment":
                    if line.startswith(('•', '-', '*')) or line[0].isdigit():
                        # Treatment item
                        treatment_text = line.lstrip('•-*0123456789. ')
                        if not current_treatment:
                            current_treatment = {
                                "name": treatment_text,
                                "type": "Chemical" if "chemical" in line.lower() else "Organic",
                                "application": "Spray application",
                                "dosage": "As per label instructions",
                                "frequency": "Weekly until recovery"
                            }
                        else:
                            # Additional details
                            if "dosage" in line.lower() or "dose" in line.lower():
                                current_treatment["dosage"] = treatment_text
                            elif "application" in line.lower() or "apply" in line.lower():
                                current_treatment["application"] = treatment_text
                            elif "frequency" in line.lower() or "repeat" in line.lower():
                                current_treatment["frequency"] = treatment_text
                
                elif current_section == "prevention":
                    if line.startswith(('•', '-', '*')) or line[0].isdigit():
                        preventive_measures.append(line.lstrip('•-*0123456789. '))
                
                elif current_section == "notes":
                    notes += line + " "
            
            # Add final treatment if exists
            if current_treatment:
                treatments.append(current_treatment)
            
            # Ensure we have at least some treatments
            if not treatments:
                treatments = self._get_default_treatments(kwargs.get("disease_name", ""))
            
            if not preventive_measures:
                preventive_measures = self._get_default_preventive_measures()
            
            return {
                "treatments": treatments,
                "preventive_measures": preventive_measures,
                "notes": notes.strip(),
                "disease_name": kwargs.get("disease_name"),
                "plant_type": kwargs.get("plant_type"),
                "severity": kwargs.get("severity", "Medium"),
                "location": kwargs.get("location"),
                "season": kwargs.get("season"),
                "rag_response": rag_response  # Include raw response for debugging
            }
            
        except Exception as e:
            logger.error(f"Error parsing RAG response: {str(e)}")
            return self._generate_fallback_prescription(**kwargs)
    
    def _parse_structured_response(self, treatment_data: Dict[str, Any], response_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Parse structured response from Prescription Engine into prescription data
        
        Args:
            treatment_data: Structured treatment data from the response
            response_data: Full response data for metadata
            **kwargs: Original input parameters
        
        Returns:
            Structured prescription data compatible with existing interface
        """
        try:
            # Extract diagnosis information
            diagnosis = treatment_data.get("diagnosis", {})
            
            # Extract medicine recommendations and convert to treatments format
            medicine_recs = treatment_data.get("medicine_recommendations", {})
            treatments = []
            
            # Add primary treatment
            primary = medicine_recs.get("primary_treatment", {})
            if primary:
                treatments.append({
                    "name": primary.get("medicine_name", "Unknown Medicine"),
                    "type": "Chemical",
                    "application": primary.get("application_method", "As directed"),
                    "dosage": primary.get("dosage", "As per label"),
                    "frequency": primary.get("frequency", "As needed"),
                    "duration": primary.get("duration", "Until improvement"),
                    "precautions": primary.get("precautions", [])
                })
            
            # Add secondary treatment
            secondary = medicine_recs.get("secondary_treatment", {})
            if secondary:
                treatments.append({
                    "name": secondary.get("medicine_name", "Secondary Medicine"),
                    "type": "Chemical",
                    "application": secondary.get("application_method", "As directed"),
                    "dosage": secondary.get("dosage", "As per label"),
                    "frequency": secondary.get("frequency", "As needed"),
                    "duration": secondary.get("duration", "Until improvement"),
                    "when_to_use": secondary.get("when_to_use")
                })
            
            # Add organic alternatives
            organic_alts = medicine_recs.get("organic_alternatives", [])
            for organic in organic_alts:
                treatments.append({
                    "name": organic.get("name", "Organic Treatment"),
                    "type": "Organic",
                    "application": organic.get("application", "As directed"),
                    "dosage": organic.get("preparation", "As per instructions"),
                    "frequency": "As needed"
                })
            
            # Extract prevention measures
            prevention = treatment_data.get("prevention", {})
            preventive_measures = []
            preventive_measures.extend(prevention.get("cultural_practices", []))
            preventive_measures.extend(prevention.get("crop_management", []))
            preventive_measures.extend(prevention.get("environmental_controls", []))
            
            # Extract additional notes
            additional_notes = treatment_data.get("additional_notes", {})
            notes_parts = []
            if additional_notes.get("weather_considerations"):
                notes_parts.append(f"Weather: {additional_notes['weather_considerations']}")
            if additional_notes.get("crop_stage_specific"):
                notes_parts.append(f"Crop Stage: {additional_notes['crop_stage_specific']}")
            if additional_notes.get("regional_considerations"):
                notes_parts.append(f"Regional: {additional_notes['regional_considerations']}")
            if additional_notes.get("follow_up"):
                notes_parts.append(f"Follow-up: {additional_notes['follow_up']}")
            
            notes = ". ".join(notes_parts)
            
            return {
                # Core data compatible with existing interface
                "treatments": treatments,
                "preventive_measures": preventive_measures,
                "notes": notes,
                "disease_name": diagnosis.get("disease_name", kwargs.get("disease_name")),
                "plant_type": kwargs.get("plant_type"),
                "severity": diagnosis.get("severity", kwargs.get("severity", "Medium")),
                "location": kwargs.get("location"),
                "season": kwargs.get("season"),
                
                # Extended structured data from new response
                "diagnosis": diagnosis,
                "immediate_treatment": treatment_data.get("immediate_treatment", {}),
                "weekly_treatment_plan": treatment_data.get("weekly_treatment_plan", {}),
                "medicine_recommendations": medicine_recs,
                "prevention": prevention,
                "additional_notes": additional_notes,
                
                # Metadata from response
                "collection_used": response_data.get("collection_used"),
                "query_time": response_data.get("query_time"),
                "parsing_success": response_data.get("parsing_success", True),
                "raw_response": response_data.get("raw_response"),
                "structured_response": True  # Flag to indicate this is structured data
            }
            
        except Exception as e:
            logger.error(f"Error parsing structured response: {str(e)}")
            # Fallback to basic structure with available data
            return {
                "treatments": self._get_default_treatments(kwargs.get("disease_name", "")),
                "preventive_measures": self._get_default_preventive_measures(),
                "notes": f"Error parsing response: {str(e)}",
                "disease_name": kwargs.get("disease_name"),
                "plant_type": kwargs.get("plant_type"),
                "severity": kwargs.get("severity", "Medium"),
                "location": kwargs.get("location"),
                "season": kwargs.get("season"),
                "error": str(e),
                "structured_response": False
            }
    
    def _generate_fallback_prescription(self, **kwargs) -> Dict[str, Any]:
        """
        Generate fallback prescription when RAG is not available
        
        Returns:
            Basic prescription data
        """
        disease_name = kwargs.get("disease_name", "Unknown Disease")
        plant_type = kwargs.get("plant_type", "plant")
        severity = kwargs.get("severity", "Medium")
        
        # Basic treatments based on common patterns
        treatments = self._get_default_treatments(disease_name)
        preventive_measures = self._get_default_preventive_measures()
        
        notes = f"These are general recommendations for {disease_name}. Consult with a local agricultural expert for specific guidance based on your location and conditions."
        
        return {
            "treatments": treatments,
            "preventive_measures": preventive_measures,
            "notes": notes,
            "disease_name": disease_name,
            "plant_type": plant_type,
            "severity": severity,
            "location": kwargs.get("location"),
            "season": kwargs.get("season"),
            "fallback": True
        }
    
    def _get_default_treatments(self, disease_name: str) -> List[Dict[str, str]]:
        """Get default treatments based on disease type"""
        disease_lower = disease_name.lower()
        
        if "bacterial" in disease_lower:
            return [
                {
                    "name": "Copper-based Bactericide",
                    "type": "Chemical",
                    "application": "Foliar spray",
                    "dosage": "2-3 ml per liter of water",
                    "frequency": "Every 7-10 days until symptoms reduce"
                },
                {
                    "name": "Streptomycin Solution",
                    "type": "Antibiotic",
                    "application": "Spray on affected areas",
                    "dosage": "1g per liter of water", 
                    "frequency": "Weekly for 3-4 weeks"
                }
            ]
        
        elif "fungal" in disease_lower or "blight" in disease_lower:
            return [
                {
                    "name": "Copper Sulfate Fungicide",
                    "type": "Chemical",
                    "application": "Foliar spray",
                    "dosage": "3-5 ml per liter of water",
                    "frequency": "Every 5-7 days until recovery"
                },
                {
                    "name": "Neem Oil Solution",
                    "type": "Organic",
                    "application": "Spray on leaves and stems",
                    "dosage": "5-10 ml per liter of water",
                    "frequency": "Twice weekly"
                }
            ]
        
        elif "viral" in disease_lower:
            return [
                {
                    "name": "Remove Infected Parts",
                    "type": "Cultural",
                    "application": "Manual removal and disposal",
                    "dosage": "Remove all affected leaves and stems",
                    "frequency": "Immediately and monitor regularly"
                },
                {
                    "name": "Imidacloprid Insecticide",
                    "type": "Chemical", 
                    "application": "Soil drench or spray",
                    "dosage": "1-2 ml per liter of water",
                    "frequency": "Monthly to control vectors"
                }
            ]
        
        else:
            # General treatment
            return [
                {
                    "name": "Broad Spectrum Fungicide",
                    "type": "Chemical",
                    "application": "Foliar spray",
                    "dosage": "As per manufacturer instructions",
                    "frequency": "Weekly until improvement"
                },
                {
                    "name": "Organic Compost Tea",
                    "type": "Organic",
                    "application": "Soil application and foliar spray",
                    "dosage": "Dilute 1:10 with water",
                    "frequency": "Bi-weekly"
                }
            ]
    
    def _get_default_preventive_measures(self) -> List[str]:
        """Get default preventive measures"""
        return [
            "Ensure proper drainage to avoid waterlogging",
            "Maintain adequate spacing between plants for air circulation",
            "Remove and dispose of infected plant debris properly",
            "Avoid overhead watering; water at the base of plants",
            "Apply balanced fertilizer to maintain plant health",
            "Inspect plants regularly for early detection of diseases",
            "Use disease-resistant plant varieties when available",
            "Practice crop rotation to break disease cycles",
            "Sanitize gardening tools between plants",
            "Avoid working with plants when they are wet"
        ]


# Async wrapper for compatibility
async def run_prescription_tool(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Async wrapper for the prescription tool
    
    Args:
        input_data: Dictionary containing disease info and context
    
    Returns:
        Prescription data or error
    """
    tool = PrescriptionTool()
    return await tool._arun(**input_data)
