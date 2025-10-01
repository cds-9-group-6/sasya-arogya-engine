"""
Base node class for FSM Agent workflow nodes
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

try:
    from ..workflow_state import WorkflowState, update_state_node
except ImportError:
    from ..workflow_state import WorkflowState, update_state_node

logger = logging.getLogger(__name__)


class BaseNode(ABC):
    """Base class for all workflow nodes"""
    
    def __init__(self, tools: Dict[str, Any], llm: Any, mlflow_manager=None):
        """
        Initialize the node
        
        Args:
            tools: Dictionary of available tools
            llm: The language model instance
            mlflow_manager: Optional MLflow manager instance for metrics tracking
        """
        self.tools = tools
        self.llm = llm
        self.mlflow_manager = mlflow_manager
        self.logger = logger
    
    @abstractmethod
    async def execute(self, state: WorkflowState) -> WorkflowState:
        """
        Execute the node logic
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        pass
    
    @property
    @abstractmethod
    def node_name(self) -> str:
        """Return the name of this node"""
        pass
    
    def update_node_state(self, state: WorkflowState) -> None:
        """Update the state to reflect this node is executing"""
        self.logger.info(f"Executing {self.node_name} node for session {state['session_id']}")
        update_state_node(state, self.node_name)
    
    def record_tool_usage(self, tool_name: str, duration: float = 0.0, success: bool = True):
        """Record tool usage metrics for this node"""
        try:
            from observability.metrics import get_metrics
            metrics = get_metrics()
            if metrics.is_initialized():
                metrics.record_node_tool_usage(
                    node_name=self.node_name,
                    tool_name=tool_name,
                    duration=duration,
                    success=success
                )
        except ImportError:
            # Gracefully handle if observability is not available
            pass
    
    async def execute_with_tool_tracking(self, tool, tool_name: str, *args, **kwargs):
        """Execute a tool with automatic tracking"""
        import time
        start_time = time.time()
        success = True
        
        try:
            if hasattr(tool, 'execute') and callable(tool.execute):
                result = await tool.execute(*args, **kwargs)
            elif callable(tool):
                result = await tool(*args, **kwargs)
            else:
                # Synchronous tool
                result = tool(*args, **kwargs)
            
            return result
            
        except Exception as e:
            success = False
            self.logger.error(f"Tool {tool_name} failed in {self.node_name}: {e}")
            raise
        
        finally:
            duration = time.time() - start_time
            self.record_tool_usage(tool_name, duration, success)

