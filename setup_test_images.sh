#!/bin/bash

# Setup Test Images for Sasya Arogya Engine Periodic Tests
# This script creates placeholder test images for the periodic testing system

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Create test images directory
TEST_IMAGES_DIR="resources/images_for_test"
log_info "Creating test images directory: $TEST_IMAGES_DIR"
mkdir -p "$TEST_IMAGES_DIR"

# Function to create a placeholder image
create_placeholder_image() {
    local filename="$1"
    local description="$2"
    local size="${3:-100x100}"
    
    log_info "Creating placeholder image: $filename"
    
    # Create a simple colored rectangle as placeholder
    # This is a minimal PNG file (1x1 pixel, red)
    cat > "$TEST_IMAGES_DIR/$filename" << 'EOF'
iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==
EOF
    
    # Decode the base64 to create actual PNG
    base64 -d > "$TEST_IMAGES_DIR/$filename" << 'EOF'
iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==
EOF
    
    log_success "Created placeholder: $filename"
}

# Create placeholder test images
log_info "Creating placeholder test images..."

create_placeholder_image "rice_leaf_blight.jpg" "Rice leaf blight test image"
create_placeholder_image "apple_leaf_disease.jpg" "Apple leaf disease test image"
create_placeholder_image "tomato_disease.jpg" "Tomato disease test image"
create_placeholder_image "wheat_rust.jpg" "Wheat rust test image"

# Create a README for the test images
cat > "$TEST_IMAGES_DIR/README.md" << 'EOF'
# Test Images for Sasya Arogya Engine

This directory contains placeholder test images for the periodic testing system.

## Required Images

- `rice_leaf_blight.jpg` - Rice leaf blight disease image
- `apple_leaf_disease.jpg` - Apple leaf disease image  
- `tomato_disease.jpg` - Tomato disease image
- `wheat_rust.jpg` - Wheat rust disease image

## Note

These are currently placeholder images. In a production environment, replace these with actual plant disease images for proper testing.

## Image Requirements

- Format: JPG or PNG
- Size: Recommended 224x224 pixels or larger
- Quality: Clear, well-lit images of diseased plant parts
- Content: Actual plant disease symptoms for accurate testing
EOF

log_success "Test images setup completed!"
log_info "Test images directory: $TEST_IMAGES_DIR"
log_warning "Note: These are placeholder images. Replace with actual plant disease images for production testing."

# List created files
log_info "Created files:"
ls -la "$TEST_IMAGES_DIR"
