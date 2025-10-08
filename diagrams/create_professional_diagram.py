#!/usr/bin/env python3
"""
Create professional architecture diagrams using matplotlib and networkx
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import numpy as np

def create_architecture_diagram():
    """Create a professional architecture diagram"""
    
    # Create figure with high DPI
    fig, ax = plt.subplots(1, 1, figsize=(16, 20), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 20)
    ax.axis('off')
    
    # Define colors
    colors = {
        'client': '#E3F2FD',      # Light blue
        'api': '#F3E5F5',         # Light purple
        'core': '#E8F5E8',        # Light green
        'ml': '#FFF3E0',          # Light orange
        'external': '#FCE4EC',    # Light pink
        'observability': '#F1F8E9', # Light green
        'infrastructure': '#FFF8E1' # Light yellow
    }
    
    # Define layers with proper spacing
    layers = [
        {
            'name': 'CLIENT APPLICATIONS',
            'y': 18,
            'color': colors['client'],
            'boxes': [
                {'name': 'Android Mobile App', 'x': 1},
                {'name': 'Web Dashboard', 'x': 3},
                {'name': 'API Clients', 'x': 5},
                {'name': 'Third-party Integrations', 'x': 7}
            ]
        },
        {
            'name': 'API GATEWAY LAYER',
            'y': 15,
            'color': colors['api'],
            'boxes': [
                {'name': 'FastAPI Server :8080', 'x': 2},
                {'name': 'CORS & Security', 'x': 4},
                {'name': 'Rate Limiting', 'x': 6},
                {'name': 'Authentication', 'x': 8}
            ]
        },
        {
            'name': 'CORE ENGINE',
            'y': 12,
            'color': colors['core'],
            'boxes': [
                {'name': 'LangGraph FSM Workflow', 'x': 1.5},
                {'name': 'Intent Analysis Engine', 'x': 3.5},
                {'name': 'Session Management', 'x': 5.5},
                {'name': 'State Persistence', 'x': 7.5}
            ]
        },
        {
            'name': 'AI/ML SERVICES',
            'y': 9,
            'color': colors['ml'],
            'boxes': [
                {'name': 'CNN Disease Classifier', 'x': 1},
                {'name': 'LLaVA Vision Model', 'x': 3},
                {'name': 'Ollama LLM Server', 'x': 5},
                {'name': 'RAG Prescription System', 'x': 7}
            ]
        },
        {
            'name': 'EXTERNAL SERVICES',
            'y': 6,
            'color': colors['external'],
            'boxes': [
                {'name': 'Insurance MCP Server', 'x': 1.5},
                {'name': 'Vendor Database', 'x': 3.5},
                {'name': 'ChromaDB Vector Store', 'x': 5.5},
                {'name': 'MLflow Tracking', 'x': 7.5}
            ]
        },
        {
            'name': 'OBSERVABILITY STACK',
            'y': 3,
            'color': colors['observability'],
            'boxes': [
                {'name': 'OpenTelemetry Collector', 'x': 2},
                {'name': 'Prometheus Metrics', 'x': 4},
                {'name': 'Grafana Dashboards', 'x': 6},
                {'name': 'Jaeger Tracing', 'x': 8}
            ]
        },
        {
            'name': 'INFRASTRUCTURE',
            'y': 0.5,
            'color': colors['infrastructure'],
            'boxes': [
                {'name': 'Docker Containers', 'x': 1.5},
                {'name': 'Redis Cache', 'x': 3.5},
                {'name': 'File Storage', 'x': 5.5},
                {'name': 'Configuration Management', 'x': 7.5}
            ]
        }
    ]
    
    # Draw layers and boxes
    for layer in layers:
        # Draw layer background
        layer_rect = FancyBboxPatch(
            (0.2, layer['y'] - 0.8), 9.6, 1.6,
            boxstyle="round,pad=0.1",
            facecolor=layer['color'],
            edgecolor='black',
            linewidth=2
        )
        ax.add_patch(layer_rect)
        
        # Add layer title
        ax.text(5, layer['y'], layer['name'], 
                ha='center', va='center', fontsize=14, fontweight='bold')
        
        # Draw boxes in layer
        for box in layer['boxes']:
            box_rect = FancyBboxPatch(
                (box['x'] - 0.8, layer['y'] - 0.4), 1.6, 0.8,
                boxstyle="round,pad=0.05",
                facecolor='white',
                edgecolor='black',
                linewidth=1
            )
            ax.add_patch(box_rect)
            
            # Add box text
            ax.text(box['x'], layer['y'], box['name'], 
                    ha='center', va='center', fontsize=10, wrap=True)
    
    # Draw main flow arrows (straight vertical)
    main_flow_x = 5
    for i in range(len(layers) - 1):
        y_start = layers[i]['y'] - 0.8
        y_end = layers[i + 1]['y'] + 0.8
        
        # Main flow arrow
        ax.annotate('', xy=(main_flow_x, y_end), xytext=(main_flow_x, y_start),
                   arrowprops=dict(arrowstyle='->', lw=3, color='#1976D2'))
    
    # Draw side connections for observability
    obs_boxes = [2, 4, 6, 8]
    for box_x in obs_boxes:
        # Arrow from main flow to observability
        ax.annotate('', xy=(box_x, 3.8), xytext=(main_flow_x, 12.2),
                   arrowprops=dict(arrowstyle='->', lw=2, color='#4CAF50', linestyle='--'))
    
    # Draw infrastructure support arrows
    infra_boxes = [1.5, 3.5, 5.5, 7.5]
    for i, box_x in enumerate(infra_boxes):
        # Arrow from main flow to infrastructure
        ax.annotate('', xy=(box_x, 1.3), xytext=(main_flow_x, 12.2),
                   arrowprops=dict(arrowstyle='->', lw=2, color='#FF9800', linestyle=':'))
    
    # Add title
    ax.text(5, 19.5, 'Sasya Arogya Engine - Application Architecture', 
            ha='center', va='center', fontsize=18, fontweight='bold')
    
    # Add legend
    legend_elements = [
        plt.Line2D([0], [0], color='#1976D2', lw=3, label='Main Data Flow'),
        plt.Line2D([0], [0], color='#4CAF50', lw=2, linestyle='--', label='Observability'),
        plt.Line2D([0], [0], color='#FF9800', lw=2, linestyle=':', label='Infrastructure Support')
    ]
    ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(0.98, 0.98))
    
    plt.tight_layout()
    plt.savefig('diagrams/diagram_01_professional.png', dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    plt.close()

def create_workflow_diagram():
    """Create a professional workflow state machine diagram"""
    
    fig, ax = plt.subplots(1, 1, figsize=(20, 16), dpi=300)
    ax.set_xlim(0, 20)
    ax.set_ylim(0, 16)
    ax.axis('off')
    
    # Define states with positions
    states = {
        'START': {'x': 10, 'y': 15, 'color': '#E3F2FD', 'shape': 'circle'},
        'INITIAL': {'x': 10, 'y': 13, 'color': '#E8F5E8', 'shape': 'rect'},
        'CLASSIFYING': {'x': 6, 'y': 11, 'color': '#E8F5E8', 'shape': 'rect'},
        'PRESCRIBING': {'x': 10, 'y': 11, 'color': '#E8F5E8', 'shape': 'rect'},
        'INSURANCE': {'x': 14, 'y': 11, 'color': '#FFF3E0', 'shape': 'rect'},
        'VENDOR_QUERY': {'x': 6, 'y': 9, 'color': '#FFF3E0', 'shape': 'rect'},
        'SHOW_VENDORS': {'x': 10, 'y': 9, 'color': '#FFF3E0', 'shape': 'rect'},
        'ORDER_BOOKING': {'x': 14, 'y': 9, 'color': '#FFF3E0', 'shape': 'rect'},
        'FOLLOWUP': {'x': 10, 'y': 7, 'color': '#F3E5F5', 'shape': 'rect'},
        'COMPLETED': {'x': 6, 'y': 5, 'color': '#FCE4EC', 'shape': 'rect'},
        'ERROR': {'x': 14, 'y': 5, 'color': '#FFEBEE', 'shape': 'rect'},
        'END': {'x': 10, 'y': 3, 'color': '#E3F2FD', 'shape': 'circle'}
    }
    
    # Draw states
    for state_name, state_info in states.items():
        x, y = state_info['x'], state_info['y']
        color = state_info['color']
        shape = state_info['shape']
        
        if shape == 'circle':
            circle = plt.Circle((x, y), 0.8, color=color, ec='black', linewidth=2)
            ax.add_patch(circle)
        else:
            rect = FancyBboxPatch(
                (x - 1.2, y - 0.4), 2.4, 0.8,
                boxstyle="round,pad=0.1",
                facecolor=color,
                edgecolor='black',
                linewidth=2
            )
            ax.add_patch(rect)
        
        # Add state text
        ax.text(x, y, state_name, ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Define transitions
    transitions = [
        ('START', 'INITIAL', 'New Session'),
        ('INITIAL', 'CLASSIFYING', 'Image + Context'),
        ('INITIAL', 'FOLLOWUP', 'Missing Info'),
        ('INITIAL', 'ERROR', 'Invalid Input'),
        ('CLASSIFYING', 'PRESCRIBING', 'Disease Found'),
        ('CLASSIFYING', 'FOLLOWUP', 'Need More Info'),
        ('CLASSIFYING', 'ERROR', 'Classification Failed'),
        ('PRESCRIBING', 'INSURANCE', 'Treatment Ready'),
        ('PRESCRIBING', 'VENDOR_QUERY', 'User Wants Vendors'),
        ('PRESCRIBING', 'COMPLETED', 'No Further Action'),
        ('INSURANCE', 'VENDOR_QUERY', 'Premium Calculated'),
        ('INSURANCE', 'COMPLETED', 'Insurance Only'),
        ('VENDOR_QUERY', 'SHOW_VENDORS', 'User Confirms'),
        ('VENDOR_QUERY', 'COMPLETED', 'No Vendors'),
        ('SHOW_VENDORS', 'ORDER_BOOKING', 'Vendor Selected'),
        ('SHOW_VENDORS', 'COMPLETED', 'No Selection'),
        ('ORDER_BOOKING', 'FOLLOWUP', 'Order Placed'),
        ('ORDER_BOOKING', 'COMPLETED', 'Order Complete'),
        ('FOLLOWUP', 'INITIAL', 'New Request'),
        ('FOLLOWUP', 'CLASSIFYING', 'Reclassify'),
        ('FOLLOWUP', 'PRESCRIBING', 'Regenerate'),
        ('FOLLOWUP', 'COMPLETED', 'Session End'),
        ('ERROR', 'END', 'Session Terminated'),
        ('COMPLETED', 'END', 'Session Complete')
    ]
    
    # Draw transitions
    for start, end, label in transitions:
        start_pos = (states[start]['x'], states[start]['y'])
        end_pos = (states[end]['x'], states[end]['y'])
        
        # Calculate arrow position
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]
        length = np.sqrt(dx**2 + dy**2)
        
        if length > 0:
            # Normalize direction
            dx_norm = dx / length
            dy_norm = dy / length
            
            # Adjust start and end points
            start_x = start_pos[0] + dx_norm * 0.8
            start_y = start_pos[1] + dy_norm * 0.8
            end_x = end_pos[0] - dx_norm * 0.8
            end_y = end_pos[1] - dy_norm * 0.8
            
            # Draw arrow
            ax.annotate('', xy=(end_x, end_y), xytext=(start_x, start_y),
                       arrowprops=dict(arrowstyle='->', lw=2, color='#1976D2'))
            
            # Add label
            mid_x = (start_x + end_x) / 2
            mid_y = (start_y + end_y) / 2
            ax.text(mid_x, mid_y + 0.3, label, ha='center', va='center', 
                   fontsize=8, bbox=dict(boxstyle="round,pad=0.2", facecolor='white', alpha=0.8))
    
    # Add title
    ax.text(10, 15.8, 'LangGraph Workflow State Machine', 
            ha='center', va='center', fontsize=18, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('diagrams/diagram_02_professional.png', dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    plt.close()

if __name__ == "__main__":
    print("Creating professional architecture diagrams...")
    create_architecture_diagram()
    print("✅ Created diagram_01_professional.png")
    create_workflow_diagram()
    print("✅ Created diagram_02_professional.png")
    print("🎉 Professional diagrams ready for Word documents!")
