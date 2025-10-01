#!/usr/bin/env python3
"""
Test script to demonstrate enhanced LangGraph node metrics
"""

import asyncio
import time
import sys
import os
sys.path.append(os.getcwd())

from observability.metrics import get_metrics

async def test_enhanced_metrics():
    """Test the enhanced metrics functionality"""
    
    print("🚀 Testing Enhanced LangGraph Node Metrics")
    print("=" * 50)
    
    metrics = get_metrics()
    if not metrics.is_initialized():
        print("❌ Metrics not initialized!")
        return
    
    print("✅ Metrics system initialized")
    
    # Test 1: Basic node execution metrics
    print("\n📊 Test 1: Basic Node Execution Metrics")
    metrics.record_node_execution("test_initial", 0.15, "success", "test_session", {"workflow_step": "1"})
    metrics.record_node_execution("test_classifying", 2.34, "success", "test_session", {"has_ml": "true"})
    metrics.record_node_execution("test_prescribing", 1.87, "success", "test_session", {"has_recommendation": "true"})
    metrics.record_node_execution("test_completed", 0.05, "success", "test_session")
    print("   ✓ Recorded node executions with enhanced labels")
    
    # Test 2: Node transitions  
    print("\n🔄 Test 2: Node Transitions")
    metrics.record_node_transition("initial", "classifying", "test_session")
    metrics.record_node_transition("classifying", "prescribing", "test_session")
    metrics.record_node_transition("prescribing", "completed", "test_session")
    print("   ✓ Recorded workflow transitions")
    
    # Test 3: Node input/output metrics
    print("\n📥 Test 3: Node Input/Output Metrics")
    metrics.record_node_input_metrics("classifying", has_image=True, message_length=145, has_context=True, context_keys=3)
    metrics.record_node_input_metrics("prescribing", has_image=False, message_length=67, has_context=True, context_keys=5)
    print("   ✓ Recorded input characteristics")
    
    metrics.record_node_output_metrics("classifying", output_length=890, messages_generated=2, tools_used=1, has_classification=True)
    metrics.record_node_output_metrics("prescribing", output_length=1245, messages_generated=3, tools_used=1, has_prescription=True)
    print("   ✓ Recorded output characteristics")
    
    # Test 4: Tool usage metrics
    print("\n🛠️ Test 4: Tool Usage Metrics")
    metrics.record_node_tool_usage("classifying", "classification_tool", 2.1, True)
    metrics.record_node_tool_usage("prescribing", "prescription_tool", 1.6, True)
    metrics.record_node_tool_usage("show_vendors", "vendor_tool", 0.8, True)
    metrics.record_node_tool_usage("insurance", "insurance_tool", 3.2, True)
    print("   ✓ Recorded tool usage with durations")
    
    # Test 5: Workflow progression
    print("\n📈 Test 5: Workflow Progression")
    metrics.record_node_state_progression("initial", state_complexity=8, workflow_step=1, is_retry=False)
    metrics.record_node_state_progression("classifying", state_complexity=12, workflow_step=2, is_retry=False)
    metrics.record_node_state_progression("prescribing", state_complexity=18, workflow_step=3, is_retry=False)
    metrics.record_node_state_progression("completed", state_complexity=20, workflow_step=4, is_retry=False)
    print("   ✓ Recorded workflow progression")
    
    # Test 6: Simulate some variety
    print("\n🎭 Test 6: Simulate Workflow Variety")
    
    # Different node types and outcomes
    for i in range(3):
        session = f"test_variety_{i}"
        
        # Vary the workflow paths
        if i == 0:
            # Normal workflow
            metrics.record_node_execution("initial", 0.12, "success", session)
            metrics.record_node_execution("classifying", 1.95, "success", session)
            metrics.record_node_execution("prescribing", 1.43, "success", session)
            metrics.record_node_execution("completed", 0.03, "success", session)
            metrics.record_node_tool_usage("classifying", "classification_tool", 1.8, True)
            
        elif i == 1:
            # Insurance workflow
            metrics.record_node_execution("initial", 0.08, "success", session)
            metrics.record_node_execution("insurance", 4.2, "success", session)
            metrics.record_node_execution("completed", 0.02, "success", session)
            metrics.record_node_tool_usage("insurance", "insurance_tool", 4.0, True)
            
        else:
            # Error workflow
            metrics.record_node_execution("initial", 0.15, "success", session)
            metrics.record_node_execution("classifying", 0.5, "error", session)
            metrics.record_node_execution("error", 0.1, "success", session)
            metrics.record_node_tool_usage("classifying", "classification_tool", 0.45, False)
    
    print("   ✓ Simulated diverse workflow scenarios")
    
    print(f"\n🎉 Enhanced metrics test completed!")
    print(f"📊 Check your Grafana dashboards:")
    print(f"   • LangGraph Node Analytics: http://localhost:3000/d/langgraph-nodes")
    print(f"   • ML Performance: http://localhost:3000/d/sasya-ml-performance") 
    print(f"   • System Overview: http://localhost:3000/d/sasya-engine-overview")
    print(f"\n🔍 Or query Prometheus directly: http://localhost:9090")
    
    # Show some key metrics to query
    print(f"\n📈 Key Metrics to Explore:")
    print(f"   • node_executions_total - Node execution counts by type")
    print(f"   • node_execution_duration_seconds - Node execution times")
    print(f"   • node_transitions_total - Workflow transitions")
    print(f"   • node_tool_usage_total - Tool usage by node and tool")
    print(f"   • node_tool_duration_seconds - Tool execution times")
    print(f"   • workflow_progression_total - Workflow phase progression")
    
if __name__ == "__main__":
    asyncio.run(test_enhanced_metrics())
