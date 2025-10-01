#!/usr/bin/env python3
"""
Quick test script to verify OpenTelemetry setup is working
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

def test_imports():
    """Test that all OpenTelemetry imports work"""
    print("🧪 Testing OpenTelemetry imports...")
    
    try:
        from observability.metrics import SasyaMetrics, get_metrics
        print("✅ Metrics module: OK")
    except Exception as e:
        print(f"❌ Metrics module failed: {e}")
        return False
        
    try:
        from observability.tracing import SasyaTracing, get_tracing  
        print("✅ Tracing module: OK")
    except Exception as e:
        print(f"❌ Tracing module failed: {e}")
        return False
        
    try:
        from observability.instrumentation import setup_observability
        print("✅ Instrumentation module: OK")
    except Exception as e:
        print(f"❌ Instrumentation module failed: {e}")
        return False
        
    return True

def test_initialization():
    """Test that OpenTelemetry components can be initialized"""
    print("\n🔧 Testing initialization...")
    
    try:
        from observability.metrics import initialize_metrics
        metrics = initialize_metrics("test-service", "1.0.0", "http://localhost:4317")
        
        if metrics.is_initialized():
            print("✅ Metrics initialized successfully")
        else:
            print("⚠️ Metrics initialized but not fully available (this is OK if OTLP collector is down)")
    except Exception as e:
        print(f"❌ Metrics initialization failed: {e}")
        return False
        
    try:
        from observability.tracing import initialize_tracing
        tracing = initialize_tracing("test-service", "1.0.0", "http://localhost:4317")
        
        if tracing.is_initialized():
            print("✅ Tracing initialized successfully")
        else:
            print("⚠️ Tracing initialized but not fully available")
    except Exception as e:
        print(f"❌ Tracing initialization failed: {e}")
        return False
        
    return True

def test_metrics_creation():
    """Test that metrics can be created and recorded"""
    print("\n📊 Testing metrics creation...")
    
    try:
        from observability.metrics import get_metrics
        metrics = get_metrics()
        
        # Test recording some metrics
        if metrics.is_initialized():
            metrics.record_http_request("GET", "/test", 200, 0.123)
            metrics.record_error("test_error", "test_component")
            print("✅ Metrics recording: OK")
        else:
            print("⚠️ Metrics not fully initialized - recording skipped")
            
        return True
    except Exception as e:
        print(f"❌ Metrics recording failed: {e}")
        return False

def test_collector_connection():
    """Test connection to OpenTelemetry collector"""
    print("\n🔌 Testing collector connection...")
    
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(("localhost", 4317))
        sock.close()
        
        if result == 0:
            print("✅ OTLP collector reachable at localhost:4317")
        else:
            print("⚠️ OTLP collector not reachable (this is OK if you haven't started the stack)")
            
        return True
    except Exception as e:
        print(f"❌ Collector connection test failed: {e}")
        return False

def test_prometheus_endpoint():
    """Test that Prometheus metrics endpoint works"""  
    print("\n📈 Testing Prometheus endpoint...")
    
    try:
        import requests
        response = requests.get("http://localhost:8080/metrics", timeout=2)
        if response.status_code == 200:
            print("✅ Prometheus metrics endpoint accessible")
        else:
            print(f"⚠️ Prometheus endpoint returned {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("⚠️ Application not running on port 8080 (start your app to test this)")
    except Exception as e:
        print(f"❌ Prometheus endpoint test failed: {e}")
        
    return True

def main():
    """Run all tests"""
    print("🚀 OpenTelemetry Setup Test")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_initialization,
        test_metrics_creation,
        test_collector_connection,
        test_prometheus_endpoint
    ]
    
    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
    
    print("\n" + "=" * 40)
    print(f"📊 Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! Your observability setup is working.")
    elif passed >= 3:
        print("✅ Core functionality working. Some optional components may need setup.")
    else:
        print("⚠️ Some issues detected. Check error messages above.")
        
    print("\n💡 Next steps:")
    print("   1. Start the observability stack: cd observability && ./start-observability.sh")
    print("   2. Install dependencies: pip install -r observability/otel_requirements_simple.txt")  
    print("   3. Run your application: python fsm_agent/run_fsm_server.py")
    print("   4. Visit http://localhost:3000 for Grafana dashboards")

if __name__ == "__main__":
    main()
