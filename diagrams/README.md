# 📊 Sasya Arogya Engine - Technical Architecture Visualizations

Professional, interactive HTML-based visualizations of the Sasya Arogya Engine technical architecture and workflow state machine.

## 🎯 Overview

This directory contains high-quality, interactive HTML visualizations that provide:

- **Professional Architecture Diagrams** - Clean, well-spaced component layouts
- **Interactive Workflow State Machine** - Complete LangGraph FSM visualization
- **Download Capabilities** - Export as SVG or PNG for Word documents
- **Responsive Design** - Works on all devices and screen sizes
- **Hover Tooltips** - Detailed component information on hover

## 📁 Files

| File | Description | Purpose |
|------|-------------|---------|
| `index.html` | Main launcher page | Entry point with navigation |
| `architecture_visualization.html` | Application architecture | System components and data flow |
| `workflow_visualization.html` | State machine diagram | LangGraph workflow visualization |
| `serve_diagrams.py` | Local server script | Serve visualizations locally |

## 🚀 Quick Start

### Option 1: Local Server (Recommended)

```bash
# Start the local server
python3 serve_diagrams.py

# Or specify a port
python3 serve_diagrams.py 8080
```

The server will automatically open your browser to `http://localhost:8080`

### Option 2: Direct File Access

Simply open `index.html` in your web browser:

```bash
# Open in default browser
open index.html  # macOS
start index.html  # Windows
xdg-open index.html  # Linux
```

## 🎨 Features

### Architecture Visualization

- **Layered Design**: Clear separation of system layers
- **Component Details**: Hover for detailed information
- **Data Flow**: Straight arrows showing main data flow
- **Observability**: Dotted lines for monitoring connections
- **Infrastructure**: Dotted lines for infrastructure support
- **Color Coding**: Each layer has distinct colors
- **Responsive**: Adapts to different screen sizes

### Workflow State Machine

- **State Types**: Different colors for different state types
- **Transition Labels**: Clear labels for all transitions
- **Multiple Layouts**: Auto-layout, manual, and hierarchical
- **Interactive States**: Hover for state descriptions
- **Flow Paths**: Clear main flow, alternative paths, and error paths
- **Professional Styling**: Clean, modern appearance

### Download Options

- **SVG Export**: Vector format for scalable graphics
- **PNG Export**: Raster format for presentations
- **High Quality**: 300 DPI for print-ready documents
- **Word Compatible**: Optimized for Word document insertion

## 🎯 Usage in Word Documents

### Step 1: Access the Visualizations

1. Start the local server: `python3 serve_diagrams.py`
2. Open `http://localhost:8080` in your browser
3. Click on the desired diagram

### Step 2: Download the Diagram

1. Click the "📥 Download SVG" or "📥 Download PNG" button
2. Choose your preferred format:
   - **SVG**: Best for scalable graphics and editing
   - **PNG**: Best for presentations and Word documents

### Step 3: Insert in Word

1. Open your Word document
2. Go to Insert > Pictures > This Device
3. Select the downloaded diagram file
4. Resize as needed for your document layout

## 🎨 Customization

### Architecture Diagram

- **View Options**: Layered, Flow, or Detailed view
- **Connection Toggle**: Show/hide connection lines
- **Component Information**: Hover for detailed descriptions

### Workflow Diagram

- **Layout Options**: Auto-layout, Manual, or Hierarchical
- **Label Toggle**: Show/hide transition labels
- **State Information**: Hover for state descriptions

## 📊 Technical Specifications

### Architecture Diagram

- **Layers**: 7 distinct system layers
- **Components**: 28 individual components
- **Connections**: 25+ data flow connections
- **Colors**: Professional color scheme
- **Responsive**: Mobile-friendly design

### Workflow Diagram

- **States**: 12 workflow states
- **Transitions**: 24 state transitions
- **State Types**: Start, Process, Service, Error, End
- **Layouts**: 3 different layout options
- **Interactive**: Hover effects and tooltips

## 🔧 Troubleshooting

### Server Issues

```bash
# Port already in use
python3 serve_diagrams.py 8081

# Permission denied
sudo python3 serve_diagrams.py
```

### Browser Issues

- **Chrome/Edge**: Best compatibility
- **Firefox**: Good compatibility
- **Safari**: May have minor rendering differences
- **Mobile**: Responsive design works on all devices

### Download Issues

- **SVG Download**: Works in all modern browsers
- **PNG Download**: Requires canvas support
- **File Size**: PNG files are typically 500KB-2MB
- **Quality**: 300 DPI for print-ready output

## 📈 Performance

- **Load Time**: < 2 seconds on modern browsers
- **File Size**: HTML files are ~50KB each
- **Memory Usage**: < 100MB browser memory
- **Responsiveness**: Smooth interactions and animations

## 🎯 Best Practices

### For Word Documents

1. **Use PNG format** for Word documents
2. **Resize to 80-90%** of original size
3. **Add captions** for professional appearance
4. **Use consistent sizing** across all diagrams

### For Presentations

1. **Use SVG format** for scalability
2. **Full size** for detailed slides
3. **Scaled down** for overview slides
4. **Consistent styling** with presentation theme

### For Technical Documentation

1. **Use both formats** as needed
2. **Include in appendices** for reference
3. **Reference in text** with figure numbers
4. **Maintain consistency** across all diagrams

## 🔄 Updates

To update the diagrams:

1. Modify the HTML files directly
2. Update the data structures in the JavaScript
3. Test in multiple browsers
4. Update this README if needed

## 📞 Support

For issues or questions:

1. Check the troubleshooting section above
2. Verify browser compatibility
3. Check console for JavaScript errors
4. Ensure all files are in the same directory

---

**🎉 Enjoy your professional technical architecture visualizations!**

*These diagrams are designed to provide clear, professional visualizations suitable for technical documentation, presentations, and Word documents.*