#!/bin/bash

# Script to create base image with all dependencies
# This should be run once or when requirements.txt changes
# Usage: ./docker/create-base-image.sh [--platform amd64|arm64]

# Check if we're in the correct directory
CURRENT_DIR=$(pwd)
if [[ ! "$CURRENT_DIR" =~ .*/sasya-arogya-engine$ ]]; then
    echo "Error: This script must be run from the sasya-arogya-engine directory."
    exit 1
fi

# Source container runtime utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/container-runtime-utils.sh"

# Detect and configure container runtime
if ! detect_container_runtime; then
    exit 1
fi

# Parse arguments
ARCH="both"
while [[ $# -gt 0 ]]; do
    case $1 in
        --platform)
            if [[ $# -lt 2 ]] || [[ ! "$2" =~ ^(amd64|arm64|both)$ ]]; then
                echo "Error: --platform requires a value (amd64, arm64, or both)"
                exit 1
            fi
            ARCH="$2"
            shift 2
            ;;
        *)
            echo "Error: Unknown option $1"
            echo "Usage: $0 [--platform amd64|arm64|both]"
            exit 1
            ;;
    esac
done

echo "Building base image for architecture: $ARCH"

# Show runtime information
show_runtime_info

# Create/update requirements file if uv is available
if command -v uv &> /dev/null; then
    echo "Using uv package manager to compile requirements..."
    uv pip compile ./pyproject.toml -o ./requirements.txt
else
    echo "Using existing requirements.txt file"
fi

# Function to build base image
build_base_image() {
    local platform=$1
    local tag="sasya-base:$platform-latest"
    
    echo "Building base image for $platform..."
    
    # Use utility function for optimal build
    build_args="--build-arg PLATFORM=$platform"
    build_image "./docker/Dockerfile.base" "$tag" "$platform" "$build_args" "false"
    
    if [ $? -eq 0 ]; then
        echo "✅ Successfully built base image: $tag"
        echo "📊 Image size:"
        $CONTAINER_RUNTIME images $tag
        
        # Interactive prompt for registry operations
        echo ""
        echo "🎯 Base image built successfully for $platform!"
        echo "📦 Local image: $tag"
        echo "🌐 Registry target: quay.io/rajivranjan/$tag"
        echo ""
        echo "ℹ️  Base images are typically pushed to registries for team sharing."
        read -p "Do you want to push this base image to quay.io registry? (y/N): " -n 1 -r
        echo ""
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "📤 Tagging image for registry..."
            $CONTAINER_RUNTIME tag $tag quay.io/rajivranjan/$tag
            
            echo "📤 Pushing to quay.io/rajivranjan/$tag..."
            if $CONTAINER_RUNTIME push quay.io/rajivranjan/$tag; then
                echo "✅ Successfully pushed $tag to registry!"
            else
                echo "❌ Failed to push to registry. Please check your credentials and network."
                registry_login_help "quay.io"
                return 1
            fi
        else
            echo "⏭️  Skipping registry push. Base image is available locally."
            echo "🔧 You can manually push later with:"
            echo "   $CONTAINER_RUNTIME tag $tag quay.io/rajivranjan/$tag"
            echo "   $CONTAINER_RUNTIME push quay.io/rajivranjan/$tag"
        fi
    else
        echo "❌ Build failed for $platform"
        exit 1
    fi
}

# Build for specified architectures
if [ "$ARCH" = "amd64" ] || [ "$ARCH" = "both" ]; then
    build_base_image "amd64"
fi

if [ "$ARCH" = "arm64" ] || [ "$ARCH" = "both" ]; then
    build_base_image "arm64"
fi

echo ""
echo "🎉 Base image creation completed successfully!"
echo ""
echo "📋 Summary of created base images:"
if [ "$ARCH" = "amd64" ] || [ "$ARCH" = "both" ]; then
    echo "  ✅ AMD64 base: localhost/sasya-base:amd64-latest"
fi
if [ "$ARCH" = "arm64" ] || [ "$ARCH" = "both" ]; then
    echo "  ✅ ARM64 base: localhost/sasya-base:arm64-latest"
fi
echo ""
echo "🚀 Next steps for lightning-fast builds:"
echo "  1️⃣  Use base image for app builds:"
echo "     podman build -f docker/Dockerfile.app -t engine:arm64-v6 ."
echo ""
echo "  2️⃣  Or use optimized script with base image:"
echo "     ./docker/create-image-engine-optimized.sh --version 6 --platform arm64"
echo ""
echo "  3️⃣  Only rebuild base image when requirements.txt changes"
echo ""
echo "💡 Performance improvement: App builds now take ~30 seconds instead of ~15 minutes!"
