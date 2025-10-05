"""
OpenTelemetry Metrics for Sasya Arogya Engine

This module provides a clean interface for collecting system, ML, and LangGraph metrics
using OpenTelemetry, complementing the existing MLflow integration.
"""

import logging
import time
from typing import Dict, Any, Optional
from contextlib import contextmanager

try:
    from opentelemetry import metrics
    from opentelemetry.metrics import MeterProvider, set_meter_provider
    from opentelemetry.sdk.metrics import MeterProvider as SDKMeterProvider
    from opentelemetry.sdk.metrics.export import (
        MetricExporter,
        PeriodicExportingMetricReader,
    )
    from opentelemetry.exporter.prometheus import PrometheusMetricReader
    from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
    from opentelemetry.sdk.resources import Resource
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False

logger = logging.getLogger(__name__)


class SasyaMetrics:
    """
    OpenTelemetry metrics collector for Sasya Arogya Engine
    
    Provides clean instrumentation for:
    - HTTP request metrics
    - CNN/ML model performance metrics  
    - LangGraph node execution metrics
    - System performance metrics
    """
    
    def __init__(self, service_name: str = "sasya-arogya-engine", 
                 service_version: str = "1.0.0", 
                 otlp_endpoint: str = "http://localhost:4317"):
        """
        Initialize metrics collection
        
        Args:
            service_name: Name of the service
            service_version: Version of the service
            otlp_endpoint: OTLP endpoint for metrics export
        """
        self.service_name = service_name
        self.service_version = service_version
        self.otlp_endpoint = otlp_endpoint
        self._meter = None
        self._metrics = {}
        self._initialized = False
        
        if not OTEL_AVAILABLE:
            logger.warning("OpenTelemetry not available - metrics collection disabled")
            return
            
        self._initialize_metrics()
    
    def _initialize_metrics(self):
        """Initialize OpenTelemetry metrics"""
        try:
            # Create resource with service information
            resource = Resource.create({
                "service.name": self.service_name,
                "service.version": self.service_version,
                "service.instance.id": f"{self.service_name}-local",
            })
            
            # Set up metric readers
            readers = []
            
            # Prometheus reader for local metrics endpoint
            prometheus_reader = PrometheusMetricReader()
            readers.append(prometheus_reader)
            
            # OTLP reader for sending to collector (optional)
            try:
                # Test connection first
                import socket
                host, port = self.otlp_endpoint.replace("http://", "").replace("https://", "").split(":")
                port = int(port)
                
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)  # 2 second timeout
                result = sock.connect_ex((host, port))
                sock.close()
                
                if result == 0:  # Connection successful
                    otlp_reader = PeriodicExportingMetricReader(
                        OTLPMetricExporter(endpoint=self.otlp_endpoint, insecure=True),
                        export_interval_millis=30000  # 30 seconds to reduce spam
                    )
                    readers.append(otlp_reader)
                    logger.info(f"✅ OTLP metrics export configured to {self.otlp_endpoint}")
                else:
                    logger.info(f"⏭️ OTLP collector not available at {self.otlp_endpoint} - metrics will be available via Prometheus only")
                    
            except Exception as e:
                logger.info(f"⏭️ OTLP metrics export unavailable: {e} - metrics will be available via Prometheus only")
            
            # Create meter provider
            provider = SDKMeterProvider(resource=resource, metric_readers=readers)
            set_meter_provider(provider)
            
            # Get meter (compatible with different OpenTelemetry versions)
            try:
                # Try newer API first
                self._meter = metrics.get_meter(
                    name=__name__,
                    version="1.0.0"
                )
            except TypeError:
                try:
                    # Try older API with different parameter names
                    self._meter = metrics.get_meter(
                        instrumenting_module_name=__name__,
                        instrumenting_library_version="1.0.0"
                    )
                except TypeError:
                    # Fallback to simplest form
                    self._meter = metrics.get_meter(__name__)
            
            # Initialize metric instruments
            self._create_instruments()
            self._initialized = True
            
            logger.info("OpenTelemetry metrics initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenTelemetry metrics: {e}")
            self._initialized = False
    
    def _create_instruments(self):
        """Create metric instruments"""
        if not self._meter:
            return
            
        # HTTP Request metrics
        self._metrics["http_requests"] = self._meter.create_counter(
            name="http_requests_total",
            description="Total number of HTTP requests",
            unit="1"
        )
        
        self._metrics["http_request_duration"] = self._meter.create_histogram(
            name="http_request_duration_seconds",
            description="HTTP request duration in seconds",
            unit="s"
        )
        
        # ML Model metrics
        self._metrics["cnn_confidence"] = self._meter.create_histogram(
            name="cnn_confidence",
            description="CNN model confidence scores",
            unit="1"
        )
        
        self._metrics["sme_confidence"] = self._meter.create_histogram(
            name="sme_confidence", 
            description="SME (LLaVA) model confidence scores",
            unit="1"
        )
        
        self._metrics["cnn_entropy"] = self._meter.create_histogram(
            name="cnn_entropy",
            description="CNN model prediction entropy",
            unit="1"
        )
        
        self._metrics["cnn_uncertainty"] = self._meter.create_histogram(
            name="cnn_uncertainty",
            description="CNN model uncertainty (1 - confidence)",
            unit="1"
        )
        
        self._metrics["classification_count"] = self._meter.create_counter(
            name="classification_count",
            description="Number of classifications performed",
            unit="1"
        )
        
        self._metrics["model_inference_duration"] = self._meter.create_histogram(
            name="model_inference_duration_seconds",
            description="Model inference duration in seconds",
            unit="s"
        )
        
        # LangGraph workflow metrics
        self._metrics["node_executions"] = self._meter.create_counter(
            name="node_executions_total",
            description="Total number of node executions",
            unit="1"
        )
        
        self._metrics["node_execution_duration"] = self._meter.create_histogram(
            name="node_execution_duration_seconds",
            description="Node execution duration in seconds",
            unit="s"
        )
        
        self._metrics["workflow_executions"] = self._meter.create_counter(
            name="workflow_executions_total",
            description="Total number of workflow executions",
            unit="1"
        )
        
        # Enhanced LangGraph node metrics
        self._metrics["node_transitions"] = self._meter.create_counter(
            name="node_transitions_total",
            description="Node-to-node transitions in workflows",
            unit="1"
        )
        
        self._metrics["node_input_count"] = self._meter.create_counter(
            name="node_input_total",
            description="Node input processing counts by characteristics",
            unit="1"
        )
        
        self._metrics["node_output_count"] = self._meter.create_counter(
            name="node_output_total",
            description="Node output generation counts by characteristics", 
            unit="1"
        )
        
        self._metrics["node_message_length"] = self._meter.create_histogram(
            name="node_message_length_chars",
            description="Length of messages processed by nodes",
            unit="chars"
        )
        
        self._metrics["node_output_length"] = self._meter.create_histogram(
            name="node_output_length_chars",
            description="Length of output generated by nodes",
            unit="chars"
        )
        
        self._metrics["node_context_keys"] = self._meter.create_histogram(
            name="node_context_keys_count",
            description="Number of context keys processed by nodes",
            unit="1"
        )
        
        self._metrics["node_messages_generated"] = self._meter.create_histogram(
            name="node_messages_generated_count",
            description="Number of messages generated by nodes",
            unit="1"
        )
        
        self._metrics["node_tools_used"] = self._meter.create_histogram(
            name="node_tools_used_count", 
            description="Number of tools used by nodes",
            unit="1"
        )
        
        self._metrics["node_tool_usage"] = self._meter.create_counter(
            name="node_tool_usage_total",
            description="Tool usage within nodes",
            unit="1"
        )
        
        self._metrics["node_tool_duration"] = self._meter.create_histogram(
            name="node_tool_duration_seconds",
            description="Duration of tool usage within nodes",
            unit="s"
        )
        
        self._metrics["workflow_progression"] = self._meter.create_counter(
            name="workflow_progression_total",
            description="Workflow progression through different phases",
            unit="1"
        )
        
        self._metrics["workflow_step_number"] = self._meter.create_histogram(
            name="workflow_step_number",
            description="Current step number in workflow progression",
            unit="1"
        )
        
        self._metrics["state_complexity"] = self._meter.create_histogram(
            name="workflow_state_complexity",
            description="Complexity measure of workflow state",
            unit="1"
        )
        
        self._metrics["workflow_duration"] = self._meter.create_histogram(
            name="workflow_duration_seconds",
            description="Complete workflow execution duration in seconds",
            unit="s"
        )
        
        # Session metrics
        self._metrics["active_sessions"] = self._meter.create_up_down_counter(
            name="active_sessions",
            description="Number of active sessions",
            unit="1"
        )
        
        # Error metrics
        self._metrics["errors"] = self._meter.create_counter(
            name="errors_total",
            description="Total number of errors",
            unit="1"
        )
        
        # Intent handling metrics
        self._metrics["out_of_scope_requests"] = self._meter.create_counter(
            name="out_of_scope_requests_total",
            description="Total number of out-of-scope requests",
            unit="1"
        )
        
        self._metrics["unhandled_intents"] = self._meter.create_counter(
            name="unhandled_intents_total", 
            description="Total number of intents that could not be handled",
            unit="1"
        )
        
        self._metrics["intent_confidence"] = self._meter.create_histogram(
            name="intent_confidence_score",
            description="Confidence score distribution for intent analysis",
            unit="1"
        )
        
        self._metrics["response_type_usage"] = self._meter.create_counter(
            name="response_type_usage_total",
            description="Usage count of different response types",
            unit="1"
        )
        
        logger.info("OpenTelemetry metric instruments created")
    
    def is_initialized(self) -> bool:
        """Check if metrics are properly initialized"""
        return self._initialized and OTEL_AVAILABLE
    
    # HTTP Metrics
    def record_http_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics"""
        if not self.is_initialized():
            return
            
        labels = {
            "method": method,
            "endpoint": endpoint,
            "status_code": str(status_code)
        }
        
        self._metrics["http_requests"].add(1, labels)
        self._metrics["http_request_duration"].record(duration, labels)
    
    @contextmanager
    def http_request_timer(self, method: str, endpoint: str, status_code: int = 200):
        """Context manager for timing HTTP requests"""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.record_http_request(method, endpoint, status_code, duration)
    
    # ML Model Metrics
    def record_cnn_metrics(self, confidence: float, entropy: float, uncertainty: float, 
                          inference_duration: float):
        """Record CNN model metrics"""
        if not self.is_initialized():
            return
            
        self._metrics["cnn_confidence"].record(confidence)
        self._metrics["cnn_entropy"].record(entropy)
        self._metrics["cnn_uncertainty"].record(uncertainty)
        self._metrics["model_inference_duration"].record(inference_duration, {"model": "cnn"})
        self._metrics["classification_count"].add(1, {"model": "cnn"})
    
    def record_sme_metrics(self, confidence: float, inference_duration: float):
        """Record SME (LLaVA) model metrics"""
        if not self.is_initialized():
            return
            
        self._metrics["sme_confidence"].record(confidence)
        self._metrics["model_inference_duration"].record(inference_duration, {"model": "sme"})
        self._metrics["classification_count"].add(1, {"model": "sme"})
    
    def record_classification_result(self, cnn_result: Dict[str, Any], 
                                   sme_result: Dict[str, Any],
                                   final_result: Dict[str, Any],
                                   durations: Dict[str, float]):
        """
        Record comprehensive classification metrics
        
        Args:
            cnn_result: CNN classification results
            sme_result: SME classification results
            final_result: Final classification decision
            durations: Processing durations for different components
        """
        if not self.is_initialized():
            return
            
        # Record CNN metrics if available
        if not cnn_result.get("error"):
            confidence = cnn_result.get("confidence", 0.0)
            # Calculate entropy and uncertainty (matching MLflow logic)
            entropy = self._calculate_entropy(confidence)
            uncertainty = 1.0 - confidence
            
            self.record_cnn_metrics(
                confidence=confidence,
                entropy=entropy,
                uncertainty=uncertainty,
                inference_duration=durations.get("cnn_duration", 0.0)
            )
        
        # Record SME metrics if available
        if not sme_result.get("error"):
            confidence = sme_result.get("confidence", 0.0)
            self.record_sme_metrics(
                confidence=confidence,
                inference_duration=durations.get("sme_duration", 0.0)
            )
        
        # Record final decision metrics
        final_confidence = final_result.get("confidence", 0.0)
        source = final_result.get("source", "unknown")
        
        self._metrics["classification_count"].add(1, {
            "source": source,
            "final_confidence_range": self._get_confidence_range(final_confidence)
        })
    
    def _calculate_entropy(self, confidence: float) -> float:
        """Calculate entropy from confidence score (matching MLflow implementation)"""
        import math
        
        if confidence <= 0.001 or confidence >= 0.999:
            return 0.0
            
        # Binary entropy: -[p*log2(p) + (1-p)*log2(1-p)]
        p1 = max(0.001, min(0.999, confidence))
        p2 = 1.0 - p1
        
        entropy = -(p1 * math.log2(p1) + p2 * math.log2(p2))
        return entropy
    
    def _get_confidence_range(self, confidence: float) -> str:
        """Get confidence range label"""
        if confidence < 0.3:
            return "low"
        elif confidence < 0.7:
            return "medium"
        else:
            return "high"
    
    # Enhanced LangGraph Metrics
    def record_node_execution(self, node_name: str, duration: float, status: str = "success", 
                            session_id: str = None, additional_labels: Dict[str, str] = None):
        """Record enhanced LangGraph node execution metrics"""
        if not self.is_initialized():
            return
            
        labels = {
            "node": node_name,
            "status": status,
            "node_type": self._get_node_type(node_name)
        }
        
        if session_id:
            labels["session_id"] = session_id[:8]  # Truncate for cardinality control
            
        if additional_labels:
            labels.update(additional_labels)
        
        self._metrics["node_executions"].add(1, labels)
        self._metrics["node_execution_duration"].record(duration, labels)
    
    def record_node_transition(self, from_node: str, to_node: str, session_id: str = None):
        """Record node-to-node transitions for workflow analysis"""
        if not self.is_initialized():
            return
            
        labels = {
            "from_node": from_node,
            "to_node": to_node,
            "transition": f"{from_node}→{to_node}"
        }
        
        if session_id:
            labels["session_id"] = session_id[:8]
            
        self._metrics["node_transitions"].add(1, labels)
    
    def record_node_input_metrics(self, node_name: str, has_image: bool = False, 
                                 message_length: int = 0, has_context: bool = False,
                                 context_keys: int = 0):
        """Record node input characteristics"""
        if not self.is_initialized():
            return
            
        labels = {
            "node": node_name,
            "has_image": str(has_image).lower(),
            "has_context": str(has_context).lower(),
            "message_size": self._get_size_bucket(message_length)
        }
        
        self._metrics["node_input_count"].add(1, labels)
        self._metrics["node_message_length"].record(message_length, {"node": node_name})
        
        if has_context:
            self._metrics["node_context_keys"].record(context_keys, {"node": node_name})
    
    def record_node_output_metrics(self, node_name: str, output_length: int = 0,
                                  messages_generated: int = 0, tools_used: int = 0,
                                  has_classification: bool = False, has_prescription: bool = False):
        """Record node output characteristics"""
        if not self.is_initialized():
            return
            
        labels = {
            "node": node_name,
            "output_size": self._get_size_bucket(output_length),
            "has_classification": str(has_classification).lower(),
            "has_prescription": str(has_prescription).lower()
        }
        
        self._metrics["node_output_count"].add(1, labels)
        self._metrics["node_output_length"].record(output_length, {"node": node_name})
        self._metrics["node_messages_generated"].record(messages_generated, {"node": node_name})
        self._metrics["node_tools_used"].record(tools_used, {"node": node_name})
    
    def record_node_tool_usage(self, node_name: str, tool_name: str, duration: float = 0.0, 
                              success: bool = True):
        """Record tool usage within nodes"""
        if not self.is_initialized():
            return
            
        labels = {
            "node": node_name,
            "tool": tool_name,
            "status": "success" if success else "error"
        }
        
        self._metrics["node_tool_usage"].add(1, labels)
        if duration > 0:
            self._metrics["node_tool_duration"].record(duration, labels)
    
    def record_node_state_progression(self, node_name: str, state_complexity: int = 0,
                                    workflow_step: int = 0, is_retry: bool = False):
        """Record workflow state progression metrics"""
        if not self.is_initialized():
            return
            
        labels = {
            "node": node_name,
            "is_retry": str(is_retry).lower(),
            "workflow_phase": self._get_workflow_phase(node_name)
        }
        
        self._metrics["workflow_progression"].add(1, labels)
        self._metrics["workflow_step_number"].record(workflow_step, {"node": node_name})
        self._metrics["state_complexity"].record(state_complexity, {"node": node_name})
    
    def _get_node_type(self, node_name: str) -> str:
        """Classify node into type categories"""
        if node_name in ["initial"]:
            return "entry"
        elif node_name in ["classifying"]:
            return "ml_processing"
        elif node_name in ["prescribing"]:
            return "decision_making"
        elif node_name in ["vendor_query", "show_vendors", "order_booking"]:
            return "commerce"
        elif node_name in ["insurance"]:
            return "insurance"
        elif node_name in ["followup"]:
            return "interaction"
        elif node_name in ["completed", "session_end"]:
            return "completion"
        elif node_name in ["error"]:
            return "error_handling"
        else:
            return "unknown"
    
    def _get_size_bucket(self, size: int) -> str:
        """Bucket sizes for better cardinality control"""
        if size == 0:
            return "empty"
        elif size < 100:
            return "small"
        elif size < 500:
            return "medium"
        elif size < 2000:
            return "large"
        else:
            return "xlarge"
    
    def _get_workflow_phase(self, node_name: str) -> str:
        """Determine workflow phase for progression analysis"""
        phase_map = {
            "initial": "initiation",
            "classifying": "analysis", 
            "prescribing": "recommendation",
            "vendor_query": "commerce",
            "show_vendors": "commerce",
            "order_booking": "commerce",
            "insurance": "insurance",
            "followup": "engagement",
            "completed": "completion",
            "session_end": "completion",
            "error": "error"
        }
        return phase_map.get(node_name, "unknown")
    
    @contextmanager
    def node_execution_timer(self, node_name: str):
        """Context manager for timing node executions"""
        start_time = time.time()
        status = "success"
        try:
            yield
        except Exception:
            status = "error"
            raise
        finally:
            duration = time.time() - start_time
            self.record_node_execution(node_name, duration, status)
    
    def record_workflow_execution(self, duration: float, session_id: str, status: str = "success"):
        """Record complete workflow execution"""
        if not self.is_initialized():
            return
            
        labels = {
            "status": status,
            "session_type": "streaming" if "stream" in session_id else "regular"
        }
        
        self._metrics["workflow_executions"].add(1, labels)
        self._metrics["workflow_duration"].record(duration, labels)
    
    # Session Metrics
    def increment_active_sessions(self, delta: int = 1):
        """Increment active session count"""
        if not self.is_initialized():
            return
            
        self._metrics["active_sessions"].add(delta)
    
    def decrement_active_sessions(self, delta: int = 1):
        """Decrement active session count"""
        if not self.is_initialized():
            return
            
        self._metrics["active_sessions"].add(-delta)
    
    # Error Metrics
    def record_error(self, error_type: str, component: str = "unknown"):
        """Record error occurrence"""
        if not self.is_initialized():
            return
            
        labels = {
            "error_type": error_type,
            "component": component
        }
        
        self._metrics["errors"].add(1, labels)
    
    # Intent Handling Metrics
    def record_out_of_scope_request(self, intent_type: str = "unknown", 
                                   user_message_category: str = "general"):
        """Record an out-of-scope request"""
        if not self.is_initialized():
            return
            
        labels = {
            "intent_type": intent_type,
            "message_category": user_message_category
        }
        
        self._metrics["out_of_scope_requests"].add(1, labels)
    
    def record_unhandled_intent(self, intent: str, confidence: float = 0.0, 
                               reason: str = "unknown"):
        """Record an intent that could not be handled"""
        if not self.is_initialized():
            return
            
        labels = {
            "intent": intent,
            "reason": reason,
            "confidence_bucket": self._get_confidence_bucket(confidence)
        }
        
        self._metrics["unhandled_intents"].add(1, labels)
    
    def record_intent_confidence(self, intent: str, confidence: float):
        """Record intent analysis confidence score"""
        if not self.is_initialized():
            return
            
        labels = {
            "intent": intent,
            "confidence_bucket": self._get_confidence_bucket(confidence)
        }
        
        self._metrics["intent_confidence"].record(confidence, labels)
    
    def record_response_type_usage(self, response_type: str, node: str = "unknown", 
                                  success: bool = True):
        """Record usage of different response types"""
        if not self.is_initialized():
            return
            
        labels = {
            "response_type": response_type,
            "node": node,
            "status": "success" if success else "failure"
        }
        
        self._metrics["response_type_usage"].add(1, labels)
    
    def _get_confidence_bucket(self, confidence: float) -> str:
        """Get confidence bucket for categorization"""
        if confidence >= 0.8:
            return "high"
        elif confidence >= 0.6:
            return "medium"
        elif confidence >= 0.3:
            return "low"
        else:
            return "very_low"
    
    def get_metrics_endpoint_url(self) -> Optional[str]:
        """Get the Prometheus metrics endpoint URL"""
        if not self.is_initialized():
            return None
            
        # Prometheus metrics are served on /metrics by default
        return "/metrics"


# Global metrics instance
_sasya_metrics: Optional[SasyaMetrics] = None


def get_metrics() -> SasyaMetrics:
    """Get global metrics instance"""
    global _sasya_metrics
    if _sasya_metrics is None:
        _sasya_metrics = SasyaMetrics()
    return _sasya_metrics


def initialize_metrics(service_name: str = "sasya-arogya-engine", 
                      service_version: str = "1.0.0",
                      otlp_endpoint: str = "http://localhost:4317") -> SasyaMetrics:
    """Initialize global metrics instance"""
    global _sasya_metrics
    _sasya_metrics = SasyaMetrics(service_name, service_version, otlp_endpoint)
    return _sasya_metrics
