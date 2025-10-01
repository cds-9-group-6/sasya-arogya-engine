"""
OpenTelemetry Instrumentation Setup for Sasya Arogya Engine

This module provides the main setup and integration functions for OpenTelemetry
instrumentation, designed to cleanly integrate with existing MLflow metrics.
"""

import logging
import os
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

from .metrics import initialize_metrics, get_metrics, SasyaMetrics
from .tracing import initialize_tracing, get_tracing, SasyaTracing

try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    from opentelemetry.instrumentation.logging import LoggingInstrumentor
    from opentelemetry.instrumentation.system_metrics import SystemMetricsInstrumentor
    OTEL_AVAILABLE = True
except ImportError as e:
    logger.warning(f"OpenTelemetry instrumentation imports failed: {e}")
    OTEL_AVAILABLE = False


class ObservabilityConfig:
    """Configuration for observability setup"""
    
    def __init__(self):
        # Service configuration
        self.service_name = os.getenv("OTEL_SERVICE_NAME", "sasya-arogya-engine")
        self.service_version = os.getenv("OTEL_SERVICE_VERSION", "1.0.0")
        
        # Export endpoints
        self.otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
        self.jaeger_endpoint = os.getenv("JAEGER_ENDPOINT", "http://localhost:14268/api/traces")
        
        # Feature flags
        self.enable_tracing = os.getenv("OTEL_ENABLE_TRACING", "true").lower() == "true"
        self.enable_metrics = os.getenv("OTEL_ENABLE_METRICS", "true").lower() == "true"
        self.enable_auto_instrumentation = os.getenv("OTEL_ENABLE_AUTO_INSTRUMENTATION", "true").lower() == "true"
        
        # Environment
        self.environment = os.getenv("ENVIRONMENT", "local")


def setup_observability(config: Optional[ObservabilityConfig] = None) -> Dict[str, Any]:
    """
    Setup OpenTelemetry observability for the Sasya Arogya Engine
    
    Args:
        config: Optional observability configuration
        
    Returns:
        Dictionary with initialized components
    """
    if not OTEL_AVAILABLE:
        logger.warning("OpenTelemetry not available - observability setup skipped")
        return {"metrics": None, "tracing": None, "success": False}
    
    if config is None:
        config = ObservabilityConfig()
    
    logger.info(f"Setting up observability for {config.service_name} v{config.service_version}")
    
    components = {"success": True}
    
    # Initialize metrics
    if config.enable_metrics:
        try:
            metrics = initialize_metrics(
                service_name=config.service_name,
                service_version=config.service_version,
                otlp_endpoint=config.otlp_endpoint
            )
            components["metrics"] = metrics
            logger.info("✅ Metrics collection initialized")
        except Exception as e:
            logger.error(f"Failed to initialize metrics: {e}")
            components["metrics"] = None
            components["success"] = False
    else:
        components["metrics"] = None
        logger.info("⏭️ Metrics collection disabled")
    
    # Initialize tracing
    if config.enable_tracing:
        try:
            tracing = initialize_tracing(
                service_name=config.service_name,
                service_version=config.service_version,
                otlp_endpoint=config.otlp_endpoint,
                jaeger_endpoint=config.jaeger_endpoint
            )
            components["tracing"] = tracing
            logger.info("✅ Distributed tracing initialized")
        except Exception as e:
            logger.error(f"Failed to initialize tracing: {e}")
            components["tracing"] = None
            components["success"] = False
    else:
        components["tracing"] = None
        logger.info("⏭️ Distributed tracing disabled")
    
    # Setup automatic instrumentation
    if config.enable_auto_instrumentation:
        try:
            setup_auto_instrumentation()
            logger.info("✅ Automatic instrumentation enabled")
        except Exception as e:
            logger.error(f"Failed to setup automatic instrumentation: {e}")
            components["success"] = False
    
    return components


def setup_auto_instrumentation():
    """Setup automatic instrumentation for common libraries"""
    if not OTEL_AVAILABLE:
        return
    
    # HTTP requests instrumentation
    try:
        RequestsInstrumentor().instrument()
        HTTPXClientInstrumentor().instrument()
        logger.debug("HTTP client instrumentation enabled")
    except Exception as e:
        logger.warning(f"Failed to setup HTTP instrumentation: {e}")
    
    # Logging instrumentation
    try:
        LoggingInstrumentor().instrument(set_logging_format=True)
        logger.debug("Logging instrumentation enabled")
    except Exception as e:
        logger.warning(f"Failed to setup logging instrumentation: {e}")
    
    # System metrics
    try:
        SystemMetricsInstrumentor().instrument()
        logger.debug("System metrics instrumentation enabled")
    except Exception as e:
        logger.warning(f"Failed to setup system metrics instrumentation: {e}")


def instrument_fastapi(app):
    """
    Instrument FastAPI application with OpenTelemetry
    
    Args:
        app: FastAPI application instance
    """
    if not OTEL_AVAILABLE:
        logger.warning("OpenTelemetry not available - FastAPI instrumentation skipped")
        return
    
    try:
        # Add Prometheus metrics endpoint
        try:
            from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
            
            @app.get("/metrics")
            async def metrics():
                """Prometheus metrics endpoint"""
                from fastapi.responses import Response
                return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
            
            logger.info("Prometheus /metrics endpoint added")
        except ImportError:
            logger.warning("prometheus_client not available - /metrics endpoint not created")
        
        # Instrument FastAPI
        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI instrumentation enabled")
        
    except Exception as e:
        logger.error(f"Failed to instrument FastAPI: {e}")


class MLflowOTelBridge:
    """
    Bridge between existing MLflow metrics and OpenTelemetry
    
    This allows the existing MLflow metrics to also be exported to OpenTelemetry
    without duplicating instrumentation code.
    """
    
    def __init__(self, metrics: Optional[SasyaMetrics] = None):
        self.metrics = metrics or get_metrics()
        self.enabled = self.metrics and self.metrics.is_initialized()
        
        if self.enabled:
            logger.info("MLflow-OTel bridge initialized")
    
    def bridge_classification_metrics(self, session_id: str,
                                    cnn_result: Dict[str, Any],
                                    sme_result: Dict[str, Any], 
                                    final_result: Dict[str, Any],
                                    durations: Optional[Dict[str, float]] = None):
        """
        Bridge classification metrics from MLflow format to OpenTelemetry
        
        Args:
            session_id: Session identifier
            cnn_result: CNN classification results
            sme_result: SME classification results  
            final_result: Final classification decision
            durations: Processing durations
        """
        if not self.enabled:
            return
        
        try:
            # Use default durations if not provided
            if durations is None:
                durations = {"cnn_duration": 0.0, "sme_duration": 0.0}
            
            # Record metrics using OpenTelemetry
            self.metrics.record_classification_result(
                cnn_result=cnn_result,
                sme_result=sme_result,
                final_result=final_result,
                durations=durations
            )
            
        except Exception as e:
            logger.warning(f"Failed to bridge classification metrics to OTel: {e}")
    
    def bridge_error_metrics(self, error_type: str, component: str, session_id: str):
        """
        Bridge error metrics from MLflow format to OpenTelemetry
        
        Args:
            error_type: Type of error
            component: Component where error occurred
            session_id: Session identifier
        """
        if not self.enabled:
            return
        
        try:
            self.metrics.record_error(error_type, component)
        except Exception as e:
            logger.warning(f"Failed to bridge error metrics to OTel: {e}")


def cleanup_observability():
    """Cleanup observability components on shutdown"""
    if not OTEL_AVAILABLE:
        return
    
    try:
        # Shutdown tracing
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry import trace
        
        tracer_provider = trace.get_tracer_provider()
        if isinstance(tracer_provider, TracerProvider):
            tracer_provider.shutdown()
        
        # Shutdown metrics
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry import metrics
        
        meter_provider = metrics.get_meter_provider()
        if isinstance(meter_provider, MeterProvider):
            meter_provider.shutdown()
        
        logger.info("OpenTelemetry components shutdown successfully")
        
    except Exception as e:
        logger.error(f"Error during observability cleanup: {e}")


# Global bridge instance
_mlflow_otel_bridge: Optional[MLflowOTelBridge] = None


def get_mlflow_bridge() -> MLflowOTelBridge:
    """Get global MLflow-OTel bridge instance"""
    global _mlflow_otel_bridge
    if _mlflow_otel_bridge is None:
        _mlflow_otel_bridge = MLflowOTelBridge()
    return _mlflow_otel_bridge
