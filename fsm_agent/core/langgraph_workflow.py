"""
Refactored LangGraph Workflow for Dynamic Planning Agent

This module implements the main LangGraph workflow for plant disease 
diagnosis and prescription using StateGraph with modular node-based architecture.
"""

import logging
import os
import sys
from typing import Dict, Any, Optional

from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END

# Add the parent directories to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

try:
    from .workflow_state import (
        WorkflowState, 
        add_message_to_state, 
        update_state_node, 
        set_error, 
        can_retry, 
        mark_complete
    )
    from .session_manager import SessionManager
    from .nodes import NodeFactory
    from ..tools.classification_tool import ClassificationTool
    from ..tools.prescription_tool import PrescriptionTool
    from ..tools.vendor_tool import VendorTool
    from ..tools.context_extractor import ContextExtractorTool
    from ..tools.attention_overlay_tool import AttentionOverlayTool
    from ..tools.insurance_tool import InsuranceTool
except ImportError:
    # Fallback to absolute imports if relative imports fail
    from fsm_agent.core.workflow_state import (
        WorkflowState, 
        add_message_to_state, 
        update_state_node, 
        set_error, 
        can_retry, 
        mark_complete
    )
    from fsm_agent.core.session_manager import SessionManager
    from fsm_agent.core.nodes import NodeFactory
    from fsm_agent.tools.classification_tool import ClassificationTool
    from fsm_agent.tools.prescription_tool import PrescriptionTool
    from fsm_agent.tools.vendor_tool import VendorTool
    from fsm_agent.tools.context_extractor import ContextExtractorTool
    from fsm_agent.tools.attention_overlay_tool import AttentionOverlayTool
    from fsm_agent.tools.insurance_tool import InsuranceTool

logger = logging.getLogger(__name__)


class DynamicPlanningWorkflow:
    """
    Refactored LangGraph workflow for dynamic plant disease diagnosis and prescription
    Uses modular node-based architecture for better maintainability and extensibility
    """
    
    def __init__(self, llm_config: Dict[str, Any]):
        """
        Initialize the workflow
        
        Args:
            llm_config: Configuration for the LLM (model, base_url, etc.)
        """
        # Initialize LLM
        self.llm = ChatOllama(**llm_config)
        
        # Initialize MLflow manager once for the entire workflow
        self.mlflow_manager = None
        try:
            from core.mlflow_manager import initialize_mlflow, get_mlflow_manager
            mlflow_initialized = initialize_mlflow()
            if mlflow_initialized:
                self.mlflow_manager = get_mlflow_manager()
                logger.info("✅ MLflow tracking initialized in workflow")
            else:
                logger.warning("⚠️ MLflow tracking initialization failed - metrics will not be logged")
        except ImportError:
            logger.warning("MLflow components not available - metrics will not be logged")
        except Exception as e:
            logger.warning(f"MLflow initialization error: {e}")
        
        # Initialize tools with MLflow manager
        self.tools = {
            "classification": ClassificationTool(),
            "prescription": PrescriptionTool(),
            "vendor": VendorTool(),
            "context_extractor": ContextExtractorTool(),
            "attention_overlay": AttentionOverlayTool(),
            "insurance": InsuranceTool(),
        }
        
        # Initialize node factory with tools, LLM, and MLflow manager
        self.node_factory = NodeFactory(self.tools, self.llm, self.mlflow_manager)
        
        # Initialize session manager for state persistence
        self.session_manager = SessionManager()
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
        self.app = self.workflow.compile()
        
        logger.info("Dynamic Planning Workflow initialized with modular node architecture, session persistence, and MLflow tracking")
    
    def _build_workflow(self) -> StateGraph:
        """
        Build the LangGraph StateGraph workflow with modular nodes
        
        Returns:
            Configured StateGraph
        """
        # Create workflow graph
        workflow = StateGraph(WorkflowState)
        
        # Add nodes using the node factory - each node is now a separate class
        node_names = self.node_factory.list_node_names()
        for node_name in node_names:
            workflow.add_node(node_name, self._create_node_executor(node_name))
        
        # Set entry point
        workflow.set_entry_point("initial")
        
        # Add conditional edges (dynamic routing based on state and LLM decisions)
        workflow.add_conditional_edges(
            "initial",
            self._route_from_initial,
            {
                "classifying": "classifying",
                "insurance": "insurance",
                "followup": "followup",
                "error": "error",
                "completed": "completed"
            }
        )
        
        workflow.add_conditional_edges(
            "classifying",
            self._route_from_classifying,
            {
                "prescribing": "prescribing",
                "completed": "completed",
                "followup": "followup",
                "error": "error",
                "retry": "classifying"
            }
        )
        
        workflow.add_conditional_edges(
            "prescribing",
            self._route_from_prescribing,
            {
                "vendor_query": "vendor_query",
                "followup": "followup",
                "completed": "completed",
                "error": "error",
                "retry": "prescribing"
            }
        )
        
        workflow.add_conditional_edges(
            "vendor_query",
            self._route_from_vendor_query,
            {
                "show_vendors": "show_vendors",
                "completed": "completed",
                "followup": "followup",
                "error": "error"
            }
        )
        
        workflow.add_conditional_edges(
            "show_vendors",
            self._route_from_show_vendors,
            {
                "order_booking": "order_booking",
                "followup": "followup",
                "completed": "completed",
                "error": "error"
            }
        )
        
        workflow.add_conditional_edges(
            "order_booking",
            self._route_from_order_booking,
            {
                "completed": "completed",
                "followup": "followup",
                "error": "error"
            }
        )
        
        workflow.add_conditional_edges(
            "insurance",
            self._route_from_insurance,
            {
                "prescribing": "prescribing",
                "vendor_query": "vendor_query",
                "followup": "followup",
                "completed": "completed",
                "error": "error"
            }
        )
        
        workflow.add_conditional_edges(
            "followup",
            self._route_from_followup,
            {
                "initial": "initial",
                "classifying": "classifying",
                "prescribing": "prescribing",
                "vendor_query": "vendor_query",
                "show_vendors": "show_vendors",
                "insurance": "insurance",
                "completed": "completed",
                "session_end": "session_end",
                "error": "error"
            }
        )
        
        # Add conditional edges for completed node to handle session ending  
        workflow.add_conditional_edges(
            "completed",
            self._route_from_completed,
            {
                "session_end": "session_end",
                "completed": END  # FIXED: End current workflow, session stays active at FSMAgent level
            }
        )
        
        # Terminal nodes
        workflow.add_edge("session_end", END)
        workflow.add_edge("error", END)
        
        return workflow
    
    def _create_node_executor(self, node_name: str):
        """
        Create a node executor function for the given node name
        
        Args:
            node_name: Name of the node
            
        Returns:
            Async function that executes the node
        """
        async def node_executor(state: WorkflowState) -> WorkflowState:
            """Execute the node and return updated state with enhanced metrics"""
            import time
            start_time = time.time()
            status = "success"
            tools_used_count = 0
            
            try:
                # OpenTelemetry tracing and enhanced metrics for node execution
                try:
                    from observability.tracing import get_tracing
                    from observability.metrics import get_metrics
                    
                    tracing = get_tracing()
                    metrics = get_metrics()
                    session_id = state.get("session_id", "unknown")
                    previous_node = state.get("current_node", "start")
                    
                    # Collect input metrics
                    input_message = ""
                    if state.get("messages") and len(state["messages"]) > 0:
                        input_message = state["messages"][-1].get("content", "")
                    
                    has_image = bool(state.get("user_image"))
                    has_context = bool(state.get("plant_context"))
                    context_keys = len(state.get("plant_context", {}).keys()) if has_context else 0
                    message_length = len(input_message)
                    
                    if tracing.is_initialized():
                        # Enhanced tracing with more attributes
                        with tracing.trace_node_execution(node_name, session_id) as span:
                            # Set comprehensive span attributes
                            span.set_attribute("node.state.has_image", has_image)
                            span.set_attribute("node.state.has_context", has_context)
                            span.set_attribute("node.state.context_keys", context_keys)
                            span.set_attribute("node.input.message_length", message_length)
                            span.set_attribute("node.previous", previous_node)
                            span.set_attribute("session.id", session_id[:8])
                            
                            # Record input metrics
                            if metrics.is_initialized():
                                metrics.record_node_input_metrics(
                                    node_name=node_name,
                                    has_image=has_image,
                                    message_length=message_length,
                                    has_context=has_context,
                                    context_keys=context_keys
                                )
                                
                                # Record node transition if we have a previous node
                                if previous_node != "start" and previous_node != node_name:
                                    metrics.record_node_transition(previous_node, node_name, session_id)
                            
                            # Execute the actual node
                            node = self.node_factory.get_node(node_name)
                            result_state = await node.execute(state)
                            
                            # Collect output metrics
                            output_messages = result_state.get("messages", [])
                            new_messages = len(output_messages) - len(state.get("messages", []))
                            
                            total_output_length = 0
                            if output_messages:
                                for msg in output_messages[-new_messages:] if new_messages > 0 else []:
                                    total_output_length += len(msg.get("content", ""))
                            
                            has_classification = bool(result_state.get("classification_results"))
                            has_prescription = bool(result_state.get("prescription_data"))
                            
                            # Count tools used (estimate based on state changes)
                            state_changes = 0
                            for key in ["classification_results", "prescription_data", "vendor_options", "plant_context"]:
                                if result_state.get(key) != state.get(key):
                                    state_changes += 1
                                    tools_used_count += 1
                            
                            # Set output span attributes
                            span.set_attribute("node.output.message_count", new_messages)
                            span.set_attribute("node.output.total_length", total_output_length)
                            span.set_attribute("node.output.has_classification", has_classification)
                            span.set_attribute("node.output.has_prescription", has_prescription)
                            span.set_attribute("node.tools.estimated_used", tools_used_count)
                            
                            # Record comprehensive execution metrics
                            if metrics.is_initialized():
                                execution_time = time.time() - start_time
                                
                                # Enhanced node execution metrics
                                metrics.record_node_execution(
                                    node_name=node_name, 
                                    duration=execution_time, 
                                    status=status,
                                    session_id=session_id
                                )
                                
                                # Record output metrics
                                metrics.record_node_output_metrics(
                                    node_name=node_name,
                                    output_length=total_output_length,
                                    messages_generated=new_messages,
                                    tools_used=tools_used_count,
                                    has_classification=has_classification,
                                    has_prescription=has_prescription
                                )
                                
                                # Record workflow progression
                                workflow_step = len(result_state.get("messages", []))
                                is_retry = result_state.get("retry_count", 0) > 0
                                state_complexity = len([k for k, v in result_state.items() if v])
                                
                                metrics.record_node_state_progression(
                                    node_name=node_name,
                                    state_complexity=state_complexity,
                                    workflow_step=workflow_step,
                                    is_retry=is_retry
                                )
                            
                            return result_state
                    else:
                        # Fallback without tracing
                        node = self.node_factory.get_node(node_name)
                        result_state = await node.execute(state)
                        
                        # Record metrics without tracing
                        try:
                            from observability.metrics import get_metrics
                            metrics = get_metrics()
                            if metrics.is_initialized():
                                execution_time = time.time() - start_time
                                metrics.record_node_execution(node_name, execution_time, status)
                        except:
                            pass
                        
                        return result_state
                
                except ImportError:
                    # OpenTelemetry not available - execute normally
                    node = self.node_factory.get_node(node_name)
                    return await node.execute(state)
                    
            except Exception as e:
                status = "error"
                logger.error(f"Error executing node {node_name}: {str(e)}", exc_info=True)
                
                # Record error metrics
                try:
                    from observability.metrics import get_metrics
                    metrics = get_metrics()
                    if metrics.is_initialized():
                        execution_time = time.time() - start_time
                        metrics.record_node_execution(node_name, execution_time, status)
                        metrics.record_error("node_execution_error", node_name)
                except:
                    pass
                
                set_error(state, f"Error in {node_name} node: {str(e)}")
                state["next_action"] = "error"
                return state
    
        return node_executor
    
    # ==================== ROUTING FUNCTIONS ====================
    # These remain the same as they handle the workflow logic
    
    async def _route_from_initial(self, state: WorkflowState) -> str:
        """Route from initial node - FIXED to always go through followup first"""
        next_action = state.get("next_action", "error")
        
        if next_action == "classify":
            return "classifying"
        elif next_action == "insurance":
            return "insurance"
        elif next_action == "error":
            return "error"
        else:
            # FIXED: All other actions (general_help, completed, request_image, followup) should go to followup first
            # This ensures proper workflow flow: initial → followup → completed
            logger.info(f"🔄 Routing from initial to followup for next_action: {next_action}")
            return "followup"
    
    async def _route_from_classifying(self, state: WorkflowState) -> str:
        """Route from classifying node"""
        next_action = state.get("next_action", "error")
        logger.info(f"Routing from classifying node. next_action = '{next_action}'")
        
        if next_action == "prescribe":
            logger.info("Routing to prescribing node")
            return "prescribing"
        elif next_action == "completed":
            logger.info("Routing to completed node")
            return "completed"
        elif next_action == "retry":
            logger.info("Routing to retry (classifying again)")
            return "retry"
        elif next_action == "error":
            logger.info("Routing to error node")
            return "error"
        else:
            logger.info(f"Routing to followup node (unknown next_action: {next_action})")
            return "followup"
    
    async def _route_from_prescribing(self, state: WorkflowState) -> str:
        """Route from prescribing node"""
        next_action = state.get("next_action", "error")
        
        if next_action == "vendor_query":
            return "vendor_query"
        elif next_action == "complete":
            return "completed"
        elif next_action == "retry":
            return "retry"
        elif next_action == "classify":
            return "classifying"
        elif next_action == "error":
            return "error"
        else:
            return "followup"
    
    async def _route_from_vendor_query(self, state: WorkflowState) -> str:
        """Route from vendor query node"""
        # This will be determined by user response
        user_response = state.get("user_message", "").lower()
        
        if any(word in user_response for word in ["yes", "sure", "okay", "show", "vendors"]):
            return "show_vendors"
        elif any(word in user_response for word in ["no", "skip", "later", "not now"]):
            return "completed"
        elif state.get("next_action") == "error":
            return "error"
        else:
            return "followup"
    
    async def _route_from_show_vendors(self, state: WorkflowState) -> str:
        """Route from show vendors node"""
        next_action = state.get("next_action", "complete")
        
        if next_action == "await_vendor_selection":
            return "followup"  # Wait for user to select vendor
        elif next_action == "order" and state.get("selected_vendor"):
            return "order_booking"
        elif next_action == "error":
            return "error"
        else:
            return "completed"
    
    async def _route_from_order_booking(self, state: WorkflowState) -> str:
        """Route from order booking node"""
        next_action = state.get("next_action", "complete")
        
        if next_action == "await_final_input":
            return "followup"
        elif next_action == "error":
            return "error"
        else:
            return "completed"
    
    async def _route_from_insurance(self, state: WorkflowState) -> str:
        """Route from insurance node"""
        next_action = state.get("next_action", "followup")
        
        if next_action == "prescribing":
            return "prescribing"
        elif next_action == "vendor_query":
            return "vendor_query"
        elif next_action == "completed":
            return "completed"
        elif next_action == "error":
            return "error"
        else:
            return "followup"
    
    async def _route_from_followup(self, state: WorkflowState) -> str:
        """Route from followup node - FIXED to end workflow but keep session active"""
        next_action = state.get("next_action", "completed")
        
        # Only specific actions should start new workflow nodes
        routing_map = {
            "restart": "initial",
            "classify": "classifying",
            "prescribe": "prescribing",
            "show_vendors": "show_vendors",
            "insurance": "insurance",
            "session_end": "session_end",  # Only explicit user goodbye ends session
            "error": "error",
            "await_user_input": "completed"  # FIXED: Direct responses should go to completed but preserve the answer
        }
        
        # Check if it's a mapped action that starts a new workflow node
        if next_action in routing_map:
            target_node = routing_map[next_action]
            logger.info(f"🔄 Routing from followup: {next_action} → {target_node}")
            return target_node
        else:
            # FIXED: All other actions end current workflow but keep session active
            # Session continuity is managed at session manager level, not workflow level
            logger.info(f"🔄 Ending workflow, session stays active: {next_action} → completed")
            return "completed"
    
    async def _route_from_completed(self, state: WorkflowState) -> str:
        """Route from completed node - FIXED to end workflow but keep session active"""
        # FIXED: Don't check goodbye intent in original message - that's wrong!
        # The completed node should end the current workflow execution.
        # Session continuity and goodbye detection should happen when user sends
        # a NEW message, not when checking the original workflow request.
        
        # Always end the current workflow execution, but session stays active
        # The FSMAgent will handle starting new workflows for subsequent user messages
        logger.info("🔄 Completed workflow execution, ending current workflow (session stays active)")
        return "completed"
    
    # ==================== PUBLIC METHODS ====================
    
    async def process_message(self, session_id: str, user_message: str, user_image: Optional[str] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a user message through the workflow
        
        Args:
            session_id: Unique session identifier
            user_message: User's input message
            user_image: Optional base64 encoded image
            context: Optional context dict
        
        Returns:
            Dictionary containing response and state information
        """
        try:
            # Get or create workflow state with session persistence
            state = self.session_manager.get_or_create_state(session_id, user_message, user_image, context)
            
            # Run workflow
            result = await self.app.ainvoke(state)
            
            # Save state after workflow execution
            self.session_manager.save_state(result)
            
            return {
                "success": True,
                "session_id": session_id,
                "messages": result.get("messages", []),
                "state": result.get("current_node"),
                "is_complete": result.get("is_complete", False),
                "requires_user_input": result.get("requires_user_input", False),
                "classification_results": result.get("classification_results"),
                "prescription_data": result.get("prescription_data"),
                "vendor_options": result.get("vendor_options"),
                "order_details": result.get("order_details")
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id
            }
    
    async def stream_process_message(self, session_id: str, user_message: str, user_image: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        """
        Stream process a user message through the workflow
        
        Args:
            session_id: Unique session identifier
            user_message: User's input message
            user_image: Optional base64 encoded image
            context: Optional context dict with plant_type, location, season, etc.
        
        Yields:
            Stream of INCREMENTAL state updates and responses (no duplication)
        """
        try:
            # Get or create workflow state with session persistence
            state = self.session_manager.get_or_create_state(session_id, user_message, user_image, context)
            
            logger.info(f"Starting refactored workflow stream for session {session_id} with message: {user_message[:50]}...")
            if user_image:
                logger.info(f"Session {session_id} includes image data: {len(user_image)} characters")
            if context:
                logger.info(f"Session {session_id} includes context: {context}")
            
            # Debug: Check initial state context
            logger.info(f"Initial state context - plant_type: {state.get('plant_type')}, location: {state.get('location')}, season: {state.get('season')}")
            
            # Track previous state to implement delta-based streaming
            previous_state = {}
            streamed_messages = set()
            last_node = None
            final_state = None  # Track final complete state for saving
            
            # Stream workflow execution - LangGraph will manage state flow between nodes
            async for chunk in self.app.astream(state, stream_mode='updates'):
                # Log the chunk for debugging (without sensitive data)
                # Extract current node from LangGraph updates format for logging
                current_node_for_log = "unknown"
                has_messages_for_log = False
                for node_name, state_data in chunk.items():
                    if isinstance(state_data, dict):
                        current_node_for_log = state_data.get("current_node", node_name)
                        has_messages_for_log = bool(state_data.get("messages"))
                        break
                logger.debug(f"Refactored workflow chunk for {session_id}: current_node={current_node_for_log}, has_messages={has_messages_for_log}")
                
                # Extract actual state data from LangGraph updates format FIRST
                actual_state_data = {}
                for node_name, state_data in chunk.items():
                    if isinstance(state_data, dict):
                        actual_state_data.update(state_data)
                
                # Calculate DELTA - only what's NEW/CHANGED from previous state
                delta_chunk = self._calculate_state_delta(chunk, previous_state)
                
                # FIRST: Check for attention overlay in delta before filtering (temporary data only)
                temp_attention_overlay = None
                source_node = actual_state_data.get("current_node", "unknown")
                
                # Look for attention overlay in delta chunk (before filtering removes it)
                if delta_chunk:
                    logger.debug(f"🔍 DEBUG: Checking delta chunk for attention overlay in node {source_node}")
                    for key, value in delta_chunk.items():
                        if isinstance(value, dict):
                            logger.debug(f"🔍 DEBUG: Checking delta dict {key} with keys: {list(value.keys()) if value else 'None'}")
                            if value.get("attention_overlay"):
                                temp_attention_overlay = value["attention_overlay"]
                                logger.info(f"✅ Found attention overlay in DELTA {key} from node {source_node}")
                                break
                
                # Stream attention overlay if found (before it gets filtered out)
                if temp_attention_overlay:
                    # Prevent duplicate streaming using overlay content hash + session + node
                    overlay_hash = hash(temp_attention_overlay[:100] + session_id + source_node)
                    overlay_hash_key = f"_overlay_hashes_{session_id}"
                    streamed_overlays = getattr(self, overlay_hash_key, set())
                    
                    if overlay_hash not in streamed_overlays:
                        # Stream attention overlay as separate event (temporary, not persisted)
                        yield {
                            "type": "attention_overlay",
                            "session_id": session_id,
                            "data": {
                                "attention_overlay": temp_attention_overlay,
                                "disease_name": actual_state_data.get("disease_name"),
                                "confidence": actual_state_data.get("confidence"),
                                "source_node": source_node
                            }
                        }
                        
                        # Track streamed overlay to prevent duplicates within session
                        streamed_overlays.add(overlay_hash)
                        setattr(self, overlay_hash_key, streamed_overlays)
                        
                        logger.info(f"🎯 Streamed attention overlay from node '{source_node}' for session {session_id}")
                    else:
                        logger.debug(f"🔄 Skipped duplicate attention overlay from node '{source_node}' for session {session_id}")
                
                # THEN: Filter and stream regular state updates
                if delta_chunk:
                    # Remove problematic data from delta (images, attention_overlay)  
                    filtered_delta = self._filter_chunk_for_streaming(delta_chunk)
                    
                    if filtered_delta:  # Only stream non-empty deltas
                        yield {
                            "type": "state_update",
                            "session_id": session_id,
                            "data": filtered_delta
                        }
                
                # CRITICAL FIX: Only stream NEW assistant_response, not old accumulated data
                previous_node = actual_state_data.get("previous_node", "")
                current_node = actual_state_data.get("current_node", "unknown")
                logger.debug(f"🔍 DEBUG: actual_state_data keys: {list(actual_state_data.keys())}")
                
                # Check for assistant_response that needs immediate streaming
                if "assistant_response" in actual_state_data:
                    assistant_response = actual_state_data["assistant_response"]
                    logger.info(f"🔍 FOUND assistant_response: '{assistant_response[:50]}...'" if assistant_response else "🔍 FOUND empty assistant_response")
                    if assistant_response and assistant_response.strip():
                        # GENERIC ARCHITECTURAL FIX: Node-controlled streaming
                        should_stream = True
                        
                        # 1. Generic duplicate prevention using robust content hashing
                        response_hash = hash(assistant_response)  # Full content hash
                        session_hash_key = f"_response_hashes_{session_id}"
                        recent_hashes = getattr(self, session_hash_key, [])
                        
                        if response_hash in recent_hashes:
                            logger.debug(f"🚫 Skipping duplicate response (content hash match) for session {session_id}")
                            should_stream = False
                        
                        # 2. Node-controlled streaming: Nodes can prevent immediate streaming
                        stream_immediately = actual_state_data.get("stream_immediately", True)
                        if not stream_immediately:
                            logger.debug(f"🚫 Node requested delayed streaming for session {session_id} from {current_node}")
                            should_stream = False
                        
                        # 3. Stream control based on response finality
                        response_status = actual_state_data.get("response_status", "final")
                        if response_status == "intermediate":
                            logger.debug(f"🚫 Skipping intermediate response for session {session_id} from {current_node}")
                            should_stream = False
                        
                        if should_stream:
                            logger.info(f"🔄 Streaming assistant response for session {session_id} from {current_node}")
                            # Update hash tracking (keep last 3 hashes to prevent immediate duplicates)
                            recent_hashes.append(response_hash)
                            if len(recent_hashes) > 3:
                                recent_hashes.pop(0)
                            setattr(self, session_hash_key, recent_hashes)
                            
                            logger.info(f"🚀 YIELDING assistant_response: {assistant_response[:30]}...")
                            yield {
                                "type": "assistant_response", 
                                "session_id": session_id,
                                "data": {"assistant_response": assistant_response}
                            }
                        else:
                            logger.debug(f"🚫 Skipped streaming response for session {session_id} from {current_node}")
                
                # Only track state transitions for logging purposes
                if current_node and current_node != last_node:
                    last_node = current_node
                    logger.info(f"Refactored state transition: {previous_state.get('current_node', 'None')} → {current_node}")
                
                # Update previous state for next iteration (CLEAN COPY - no images/overlays)
                previous_state = self._create_clean_state_copy_from_actual_data(actual_state_data)
            
                # Track the final state (don't save every intermediate state)
                if actual_state_data:
                    final_state = actual_state_data
            
            # Save the final complete state (only once, after workflow completes)
            if final_state:
                # FINAL CLEANUP: Ensure no duplicates before saving final state
                final_state = self.session_manager.deduplicate_messages(final_state)
                self.session_manager.save_state(final_state)
                logger.info(f"💾 Saved final workflow state for session {session_id}")
            
            logger.info(f"Workflow stream completed for session {session_id} with state persistence")
            
        except Exception as e:
            logger.error(f"Error in refactored stream processing: {str(e)}", exc_info=True)
            yield {
                "type": "error",
                "session_id": session_id,
                "error": str(e)
            }
    
    # ==================== STREAMING HELPER METHODS ====================
    # These remain the same as they handle streaming logic
    
    def _filter_chunk_for_streaming(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter chunk data to remove images, verbose data, but keep essential state results
        
        Args:
            chunk: Original state chunk
            
        Returns:
            Clean chunk suitable for streaming (essential results only)
        """
        if not isinstance(chunk, dict):
            return chunk
            
        # Create filtered copy - start with everything and remove problematic data
        filtered = chunk.copy()
        
        # 1. Remove large base64 image data
        for img_key in ["user_image", "image"]:
            if img_key in filtered:
                del filtered[img_key]
            
        # 2. Remove attention_overlay (auto-streaming issue)
        if "attention_overlay" in filtered:
            del filtered["attention_overlay"]
            
        # GENERIC ARCHITECTURAL FIX: Remove assistant_response from state_update based on node metadata
        # This prevents duplicate streaming in state_update events when dedicated streaming exists
        if "assistant_response" in filtered:
            # Generic approach: Check if node marked response as "stream_in_state_update"
            stream_in_state = chunk.get("stream_in_state_update", False)
            response_status = chunk.get("response_status", "final")
            
            # Only keep in state_update if explicitly requested or it's marked for state streaming
            if not stream_in_state and response_status != "state_only":
                logger.debug("Removing assistant_response from state_update (handled by dedicated streaming)")
                del filtered["assistant_response"]
        
        # 3. Remove messages (handled separately to prevent duplication)    
        if "messages" in filtered:
            del filtered["messages"]
            
        # 4. Clean up verbose data in classification_results
        if "classification_results" in filtered and isinstance(filtered["classification_results"], dict):
            classification = filtered["classification_results"]
            
            # Remove verbose fields but keep essential results
            verbose_fields = ["raw_predictions", "plant_context", "attention_overlay"]
            for verbose_field in verbose_fields:
                if verbose_field in classification:
                    del classification[verbose_field]
            
            filtered["classification_results"] = classification
        
        # 5. Remove verbose timestamps that change constantly
        if "last_update_time" in filtered:
            del filtered["last_update_time"]
        
        return filtered
    
    def _calculate_state_delta(self, current_state: Dict[str, Any], previous_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate the delta (new/changed data) between current and previous state
        
        Args:
            current_state: Current state chunk from LangGraph (format: {node_name: {state_data}})
            previous_state: Previous state chunk (flattened state data)
            
        Returns:
            Dictionary containing only NEW/CHANGED data
        """
        if not isinstance(current_state, dict):
            return current_state
        
        # Extract actual state data from LangGraph updates format: {node_name: {state_data}}
        actual_state_data = {}
        for node_name, state_data in current_state.items():
            if isinstance(state_data, dict):
                actual_state_data.update(state_data)
            
        if not previous_state:
            # First state - everything is new, but exclude problematic data
            return {k: v for k, v in actual_state_data.items() 
                   if k not in ["user_image", "image", "attention_overlay", "messages", "last_update_time"]}
        
        delta = {}
        
        # Check each key for changes in the actual state data
        for key, value in actual_state_data.items():
            # Skip problematic data that we never want to stream
            if key in ["user_image", "image", "attention_overlay", "messages", "last_update_time"]:
                continue
                
            # Include if key is new or value has changed
            if key not in previous_state or previous_state[key] != value:
                delta[key] = value
        
        return delta
    
    def _create_clean_state_copy_from_actual_data(self, actual_state_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a clean copy of actual state data for tracking (no images/overlays)
        
        Args:
            actual_state_data: Already extracted/flattened state data
            
        Returns:
            Clean copy without problematic data
        """
        if not isinstance(actual_state_data, dict):
            return {}
            
        clean_copy = {}
        
        for key, value in actual_state_data.items():
            # Exclude problematic data from state tracking
            if key in ["user_image", "image", "attention_overlay", "messages", "last_update_time"]:
                continue
            
            clean_copy[key] = value
                
        return clean_copy
