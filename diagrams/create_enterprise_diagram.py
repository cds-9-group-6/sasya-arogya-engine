#!/usr/bin/env python3
"""
Create enterprise-grade architecture diagrams using matplotlib
Following industry best practices for technical documentation
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle
import numpy as np

def create_enterprise_architecture():
    """Create a professional enterprise architecture diagram"""
    
    # Create figure with proper aspect ratio
    fig, ax = plt.subplots(1, 1, figsize=(14, 18), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 18)
    ax.axis('off')
    
    # Professional color scheme
    colors = {
        'client': '#E8F4FD',      # Light blue
        'api': '#F0F4FF',         # Light purple
        'core': '#F0F8F0',        # Light green
        'ml': '#FFF8F0',          # Light orange
        'external': '#FDF0F8',    # Light pink
        'observability': '#F8FDF0', # Light mint
        'infrastructure': '#FFFDF0' # Light cream
    }
    
    # Define layers with proper spacing and alignment
    layers = [
        {
            'name': 'CLIENT LAYER',
            'y': 16.5,
            'height': 1.2,
            'color': colors['client'],
            'components': [
                {'name': 'Mobile App', 'x': 2, 'width': 1.5},
                {'name': 'Web Dashboard', 'x': 4, 'width': 1.5},
                {'name': 'API Clients', 'x': 6, 'width': 1.5},
                {'name': 'Third-party', 'x': 8, 'width': 1.5}
            ]
        },
        {
            'name': 'API GATEWAY LAYER',
            'y': 14.5,
            'height': 1.2,
            'color': colors['api'],
            'components': [
                {'name': 'FastAPI Server', 'x': 2, 'width': 1.5},
                {'name': 'Security & CORS', 'x': 4, 'width': 1.5},
                {'name': 'Rate Limiting', 'x': 6, 'width': 1.5},
                {'name': 'Authentication', 'x': 8, 'width': 1.5}
            ]
        },
        {
            'name': 'CORE ENGINE LAYER',
            'y': 12.5,
            'height': 1.2,
            'color': colors['core'],
            'components': [
                {'name': 'LangGraph FSM', 'x': 2, 'width': 1.5},
                {'name': 'Intent Analysis', 'x': 4, 'width': 1.5},
                {'name': 'Session Mgmt', 'x': 6, 'width': 1.5},
                {'name': 'State Persistence', 'x': 8, 'width': 1.5}
            ]
        },
        {
            'name': 'AI/ML SERVICES LAYER',
            'y': 10.5,
            'height': 1.2,
            'color': colors['ml'],
            'components': [
                {'name': 'CNN Classifier', 'x': 2, 'width': 1.5},
                {'name': 'LLaVA Vision', 'x': 4, 'width': 1.5},
                {'name': 'Ollama LLM', 'x': 6, 'width': 1.5},
                {'name': 'RAG System', 'x': 8, 'width': 1.5}
            ]
        },
        {
            'name': 'EXTERNAL SERVICES LAYER',
            'y': 8.5,
            'height': 1.2,
            'color': colors['external'],
            'components': [
                {'name': 'Insurance MCP', 'x': 2, 'width': 1.5},
                {'name': 'Vendor DB', 'x': 4, 'width': 1.5},
                {'name': 'ChromaDB', 'x': 6, 'width': 1.5},
                {'name': 'MLflow', 'x': 8, 'width': 1.5}
            ]
        },
        {
            'name': 'OBSERVABILITY LAYER',
            'y': 6.5,
            'height': 1.2,
            'color': colors['observability'],
            'components': [
                {'name': 'OpenTelemetry', 'x': 2, 'width': 1.5},
                {'name': 'Prometheus', 'x': 4, 'width': 1.5},
                {'name': 'Grafana', 'x': 6, 'width': 1.5},
                {'name': 'Jaeger', 'x': 8, 'width': 1.5}
            ]
        },
        {
            'name': 'INFRASTRUCTURE LAYER',
            'y': 4.5,
            'height': 1.2,
            'color': colors['infrastructure'],
            'components': [
                {'name': 'Docker', 'x': 2, 'width': 1.5},
                {'name': 'Redis Cache', 'x': 4, 'width': 1.5},
                {'name': 'File Storage', 'x': 6, 'width': 1.5},
                {'name': 'Config Mgmt', 'x': 8, 'width': 1.5}
            ]
        }
    ]
    
    # Draw layers
    for layer in layers:
        # Layer background
        layer_rect = Rectangle(
            (0.5, layer['y'] - layer['height']/2), 9, layer['height'],
            facecolor=layer['color'],
            edgecolor='#333333',
            linewidth=1.5,
            alpha=0.8
        )
        ax.add_patch(layer_rect)
        
        # Layer title
        ax.text(5, layer['y'], layer['name'], 
                ha='center', va='center', fontsize=12, fontweight='bold', color='#333333')
        
        # Components
        for comp in layer['components']:
            comp_rect = Rectangle(
                (comp['x'] - comp['width']/2, layer['y'] - 0.4), 
                comp['width'], 0.8,
                facecolor='white',
                edgecolor='#666666',
                linewidth=1
            )
            ax.add_patch(comp_rect)
            
            # Component text
            ax.text(comp['x'], layer['y'], comp['name'], 
                    ha='center', va='center', fontsize=9, color='#333333')
    
    # Draw main data flow (vertical)
    main_flow_x = 5
    for i in range(len(layers) - 1):
        y_start = layers[i]['y'] - layers[i]['height']/2
        y_end = layers[i + 1]['y'] + layers[i + 1]['height']/2
        
        # Main flow arrow
        ax.annotate('', xy=(main_flow_x, y_end), xytext=(main_flow_x, y_start),
                   arrowprops=dict(arrowstyle='->', lw=3, color='#1976D2'))
    
    # Draw observability connections (dotted)
    obs_y = 6.5
    for i in range(0, len(layers) - 1, 2):  # Every other layer
        y_start = layers[i]['y'] - layers[i]['height']/2
        ax.annotate('', xy=(2, obs_y), xytext=(main_flow_x, y_start),
                   arrowprops=dict(arrowstyle='->', lw=1.5, color='#4CAF50', 
                                 linestyle='--', alpha=0.7))
    
    # Draw infrastructure support (dotted)
    infra_y = 4.5
    for i in range(0, len(layers) - 2, 2):  # Every other layer except last
        y_start = layers[i]['y'] - layers[i]['height']/2
        ax.annotate('', xy=(2, infra_y), xytext=(main_flow_x, y_start),
                   arrowprops=dict(arrowstyle='->', lw=1.5, color='#FF9800', 
                                 linestyle=':', alpha=0.7))
    
    # Add title
    ax.text(5, 17.5, 'Sasya Arogya Engine - Application Architecture', 
            ha='center', va='center', fontsize=16, fontweight='bold', color='#333333')
    
    # Add legend
    legend_elements = [
        plt.Line2D([0], [0], color='#1976D2', lw=3, label='Main Data Flow'),
        plt.Line2D([0], [0], color='#4CAF50', lw=2, linestyle='--', label='Observability'),
        plt.Line2D([0], [0], color='#FF9800', lw=2, linestyle=':', label='Infrastructure')
    ]
    ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(0.98, 0.98),
             frameon=True, fancybox=True, shadow=True)
    
    plt.tight_layout()
    plt.savefig('diagrams/diagram_01_enterprise.png', dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    plt.close()

def create_workflow_state_machine():
    """Create a professional state machine diagram"""
    
    fig, ax = plt.subplots(1, 1, figsize=(16, 12), dpi=300)
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 12)
    ax.axis('off')
    
    # Define states with proper positioning
    states = {
        'START': {'x': 8, 'y': 10.5, 'type': 'circle', 'color': '#E3F2FD'},
        'INITIAL': {'x': 8, 'y': 9, 'type': 'rect', 'color': '#E8F5E8'},
        'CLASSIFYING': {'x': 4, 'y': 7.5, 'type': 'rect', 'color': '#E8F5E8'},
        'PRESCRIBING': {'x': 8, 'y': 7.5, 'type': 'rect', 'color': '#E8F5E8'},
        'INSURANCE': {'x': 12, 'y': 7.5, 'type': 'rect', 'color': '#FFF3E0'},
        'VENDOR_QUERY': {'x': 4, 'y': 6, 'type': 'rect', 'color': '#FFF3E0'},
        'SHOW_VENDORS': {'x': 8, 'y': 6, 'type': 'rect', 'color': '#FFF3E0'},
        'ORDER_BOOKING': {'x': 12, 'y': 6, 'type': 'rect', 'color': '#FFF3E0'},
        'FOLLOWUP': {'x': 8, 'y': 4.5, 'type': 'rect', 'color': '#F3E5F5'},
        'COMPLETED': {'x': 4, 'y': 3, 'type': 'rect', 'color': '#FCE4EC'},
        'ERROR': {'x': 12, 'y': 3, 'type': 'rect', 'color': '#FFEBEE'},
        'END': {'x': 8, 'y': 1.5, 'type': 'circle', 'color': '#E3F2FD'}
    }
    
    # Draw states
    for state_name, state_info in states.items():
        x, y = state_info['x'], state_info['y']
        color = state_info['color']
        state_type = state_info['type']
        
        if state_type == 'circle':
            circle = Circle((x, y), 0.6, color=color, ec='#333333', linewidth=2)
            ax.add_patch(circle)
            ax.text(x, y, state_name, ha='center', va='center', fontsize=10, fontweight='bold')
        else:
            rect = Rectangle((x-1, y-0.3), 2, 0.6, 
                           facecolor=color, edgecolor='#333333', linewidth=2)
            ax.add_patch(rect)
            ax.text(x, y, state_name, ha='center', va='center', fontsize=9, fontweight='bold')
    
    # Define transitions with labels
    transitions = [
        ('START', 'INITIAL', 'New Session'),
        ('INITIAL', 'CLASSIFYING', 'Image + Context'),
        ('INITIAL', 'FOLLOWUP', 'Missing Info'),
        ('INITIAL', 'ERROR', 'Invalid Input'),
        ('CLASSIFYING', 'PRESCRIBING', 'Disease Found'),
        ('CLASSIFYING', 'FOLLOWUP', 'Need More Info'),
        ('CLASSIFYING', 'ERROR', 'Failed'),
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
        ('ERROR', 'END', 'Terminated'),
        ('COMPLETED', 'END', 'Complete')
    ]
    
    # Draw transitions
    for start, end, label in transitions:
        start_pos = (states[start]['x'], states[start]['y'])
        end_pos = (states[end]['x'], states[end]['y'])
        
        # Calculate arrow direction
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]
        length = np.sqrt(dx**2 + dy**2)
        
        if length > 0:
            # Normalize and adjust for state boundaries
            dx_norm = dx / length
            dy_norm = dy / length
            
            # Adjust start and end points
            start_x = start_pos[0] + dx_norm * 0.6
            start_y = start_pos[1] + dy_norm * 0.6
            end_x = end_pos[0] - dx_norm * 0.6
            end_y = end_pos[1] - dy_norm * 0.6
            
            # Draw arrow
            ax.annotate('', xy=(end_x, end_y), xytext=(start_x, start_y),
                       arrowprops=dict(arrowstyle='->', lw=2, color='#1976D2'))
            
            # Add label
            mid_x = (start_x + end_x) / 2
            mid_y = (start_y + end_y) / 2
            ax.text(mid_x, mid_y + 0.2, label, ha='center', va='center', 
                   fontsize=8, bbox=dict(boxstyle="round,pad=0.2", 
                   facecolor='white', edgecolor='#CCCCCC', alpha=0.9))
    
    # Add title
    ax.text(8, 11.5, 'LangGraph Workflow State Machine', 
            ha='center', va='center', fontsize=16, fontweight='bold', color='#333333')
    
    plt.tight_layout()
    plt.savefig('diagrams/diagram_02_enterprise.png', dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    plt.close()

if __name__ == "__main__":
    print("Creating enterprise-grade architecture diagrams...")
    create_enterprise_architecture()
    print("✅ Created diagram_01_enterprise.png")
    create_workflow_state_machine()
    print("✅ Created diagram_02_enterprise.png")
    print("🎉 Enterprise diagrams ready for professional documentation!")
