"""
OpenTelemetry Tracing for Sasya Arogya Engine

This module provides distributed tracing capabilities for tracking requests
through the LangGraph workflow and ML model operations.
"""

import logging
from typing import Dict, Any, Optional
from contextlib import contextmanager

try:
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter  
    from opentelemetry.sdk.resources import Resource
    OTEL_AVAILABLE = True
    
    # Jaeger is optional
    try:
        from opentelemetry.exporter.jaeger.thrift import JaegerExporter
        JAEGER_AVAILABLE = True
    except ImportError:
        JAEGER_AVAILABLE = False
        
except ImportError as e:
    logger.warning(f"OpenTelemetry tracing imports failed: {e}")
    OTEL_AVAILABLE = False
    JAEGER_AVAILABLE = False

logger = logging.getLogger(__name__)


class SasyaTracing:
    """
    OpenTelemetry tracing for Sasya Arogya Engine
    
    Provides distributed tracing for:
    - HTTP request flows
    - LangGraph workflow execution
    - ML model inference operations
    - Inter-service communication
    """
    
    def __init__(self, service_name: str = "sasya-arogya-engine",
                 service_version: str = "1.0.0",
                 otlp_endpoint: str = "http://localhost:4317",
                 jaeger_endpoint: str = "http://localhost:14268/api/traces"):
        """
        Initialize tracing
        
        Args:
            service_name: Name of the service
            service_version: Version of the service  
            otlp_endpoint: OTLP endpoint for trace export
            jaeger_endpoint: Jaeger endpoint for trace export
        """
        self.service_name = service_name
        self.service_version = service_version
        self.otlp_endpoint = otlp_endpoint
        self.jaeger_endpoint = jaeger_endpoint
        self._tracer = None
        self._initialized = False
        
        if not OTEL_AVAILABLE:
            logger.warning("OpenTelemetry not available - tracing disabled")
            return
            
        self._initialize_tracing()
    
    def _initialize_tracing(self):
        """Initialize OpenTelemetry tracing"""
        try:
            # Create resource with service information
            resource = Resource.create({
                "service.name": self.service_name,
                "service.version": self.service_version,
                "service.instance.id": f"{self.service_name}-local",
            })
            
            # Create tracer provider
            tracer_provider = TracerProvider(resource=resource)
            trace.set_tracer_provider(tracer_provider)
            
            # Add span processors/exporters
            
            # OTLP exporter
            try:
                otlp_exporter = OTLPSpanExporter(
                    endpoint=self.otlp_endpoint,
                    insecure=True
                )
                otlp_processor = BatchSpanProcessor(otlp_exporter)
                tracer_provider.add_span_processor(otlp_processor)
                logger.info(f"OTLP trace export configured to {self.otlp_endpoint}")
            except Exception as e:
                logger.warning(f"OTLP trace export unavailable: {e}")
            
            # Jaeger exporter (optional)
            if JAEGER_AVAILABLE:
                try:
                    jaeger_exporter = JaegerExporter(
                        agent_host_name="localhost",
                        agent_port=6831,
                    )
                    jaeger_processor = BatchSpanProcessor(jaeger_exporter)
                    tracer_provider.add_span_processor(jaeger_processor)
                    logger.info("✅ Jaeger trace export configured")
                except Exception as e:
                    logger.warning(f"Jaeger trace export unavailable: {e}")
            else:
                logger.info("⏭️ Jaeger exporter not available - using OTLP only")
            
            # Get tracer (compatible with different OpenTelemetry versions)
            try:
                # Try newer API first
                self._tracer = trace.get_tracer(
                    name=__name__,
                    version="1.0.0"
                )
            except TypeError:
                try:
                    # Try older API with different parameter names
                    self._tracer = trace.get_tracer(
                        instrumenting_module_name=__name__,
                        instrumenting_library_version="1.0.0"
                    )
                except TypeError:
                    # Fallback to simplest form
                    self._tracer = trace.get_tracer(__name__)
            
            self._initialized = True
            logger.info("OpenTelemetry tracing initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenTelemetry tracing: {e}")
            self._initialized = False
    
    def is_initialized(self) -> bool:
        """Check if tracing is properly initialized"""
        return self._initialized and OTEL_AVAILABLE
    
    @contextmanager 
    def trace_operation(self, operation_name: str, 
                       attributes: Optional[Dict[str, Any]] = None,
                       set_status_on_exception: bool = True):
        """
        Context manager for tracing an operation
        
        Args:
            operation_name: Name of the operation being traced
            attributes: Additional attributes to add to the span
            set_status_on_exception: Whether to set error status on exception
        """
        if not self.is_initialized():
            yield
            return
            
        with self._tracer.start_as_current_span(operation_name) as span:
            try:
                # Add attributes if provided
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(str(key), str(value))
                
                yield span
                
                # Mark as successful
                span.set_status(Status(StatusCode.OK))
                
            except Exception as e:
                if set_status_on_exception:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                raise
    
    def trace_http_request(self, method: str, endpoint: str, status_code: int = 200):
        """Trace HTTP request"""
        attributes = {
            "http.method": method,
            "http.url": endpoint,
            "http.status_code": status_code
        }
        return self.trace_operation(f"HTTP {method} {endpoint}", attributes)
    
    def trace_node_execution(self, node_name: str, session_id: str):
        """Trace LangGraph node execution"""
        attributes = {
            "langgraph.node": node_name,
            "session.id": session_id,
            "component": "langgraph"
        }
        return self.trace_operation(f"node.{node_name}", attributes)
    
    def trace_workflow_execution(self, workflow_type: str, session_id: str):
        """Trace complete workflow execution"""
        attributes = {
            "workflow.type": workflow_type,
            "session.id": session_id,
            "component": "workflow"
        }
        return self.trace_operation(f"workflow.{workflow_type}", attributes)
    
    def trace_ml_inference(self, model_name: str, model_type: str = "unknown"):
        """Trace ML model inference"""
        attributes = {
            "ml.model.name": model_name,
            "ml.model.type": model_type,
            "component": "ml"
        }
        return self.trace_operation(f"ml.inference.{model_name}", attributes)
    
    def trace_classification(self, session_id: str, has_image: bool = False):
        """Trace plant disease classification"""
        attributes = {
            "classification.session_id": session_id,
            "classification.has_image": has_image,
            "component": "classification"
        }
        return self.trace_operation("classification.classify", attributes)
    
    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """Add event to current span"""
        if not self.is_initialized():
            return
            
        current_span = trace.get_current_span()
        if current_span:
            current_span.add_event(name, attributes or {})
    
    def set_attribute(self, key: str, value: Any):
        """Set attribute on current span"""
        if not self.is_initialized():
            return
            
        current_span = trace.get_current_span()
        if current_span:
            current_span.set_attribute(key, str(value))
    
    def record_exception(self, exception: Exception):
        """Record exception in current span"""
        if not self.is_initialized():
            return
            
        current_span = trace.get_current_span()
        if current_span:
            current_span.record_exception(exception)


# Global tracing instance
_sasya_tracing: Optional[SasyaTracing] = None


def get_tracing() -> SasyaTracing:
    """Get global tracing instance"""
    global _sasya_tracing
    if _sasya_tracing is None:
        _sasya_tracing = SasyaTracing()
    return _sasya_tracing


def initialize_tracing(service_name: str = "sasya-arogya-engine",
                      service_version: str = "1.0.0", 
                      otlp_endpoint: str = "http://localhost:4317",
                      jaeger_endpoint: str = "http://localhost:14268/api/traces") -> SasyaTracing:
    """Initialize global tracing instance"""
    global _sasya_tracing
    _sasya_tracing = SasyaTracing(service_name, service_version, otlp_endpoint, jaeger_endpoint)
    return _sasya_tracing
