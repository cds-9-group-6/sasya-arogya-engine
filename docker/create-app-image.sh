#!/bin/bash

# Script to create app images using pre-built base images - Platform-specific
# This script builds lightning-fast app images using base images with pre-installed dependencies
# Usage: ./docker/create-app-image.sh --version <version> --platform <platform> [--run] [--base-registry <registry>]

# Check if we're in the correct directory
CURRENT_DIR=$(pwd)
if [[ ! "$CURRENT_DIR" =~ .*/sasya-arogya-engine$ ]]; then
    echo "❌ Error: This script must be run from the sasya-arogya-engine directory."
    echo "Current directory: $CURRENT_DIR"
    exit 1
fi

# Source container runtime utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/container-runtime-utils.sh"

# Detect and configure container runtime
if ! detect_container_runtime; then
    exit 1
fi

# Parse command line arguments
RUN_AFTER_BUILD=false
PLATFORM=""
VERSION=""
BASE_REGISTRY="localhost"

while [[ $# -gt 0 ]]; do
    case $1 in
        --run)
            RUN_AFTER_BUILD=true
            shift
            ;;
        --platform)
            if [[ $# -lt 2 ]] || [[ ! "$2" =~ ^(amd64|arm64)$ ]]; then
                echo "❌ Error: --platform requires a value (amd64 or arm64)"
                exit 1
            fi
            PLATFORM="$2"
            shift 2
            ;;
        --version)
            if [[ $# -lt 2 ]] || [[ -z "$2" ]]; then
                echo "❌ Error: --version requires a value"
                exit 1
            fi
            VERSION="$2"
            shift 2
            ;;
        --base-registry)
            if [[ $# -lt 2 ]] || [[ -z "$2" ]]; then
                echo "❌ Error: --base-registry requires a value"
                exit 1
            fi
            BASE_REGISTRY="$2"
            shift 2
            ;;
        *)
            echo "❌ Error: Unknown option $1"
            echo "Usage: $0 --version <version> --platform <platform> [--run] [--base-registry <registry>]"
            echo "  --version: Version number for the app image (mandatory)"
            echo "  --platform: Build for specific architecture (amd64 or arm64, mandatory)"
            echo "  --run: Run the container after building (default: false)"
            echo "  --base-registry: Registry for base image (default: localhost)"
            exit 1
            ;;
    esac
done

# Validation: version and platform are mandatory
if [ -z "$VERSION" ]; then
    echo "❌ Error: --version is mandatory"
    exit 1
fi

if [ -z "$PLATFORM" ]; then
    echo "❌ Error: --platform is mandatory for app builds"
    exit 1
fi

BASE_IMAGE="$BASE_REGISTRY/sasya-base:$PLATFORM-latest"
APP_IMAGE="engine:$PLATFORM-v$VERSION"

echo "🚀 Starting app image build..."

# Show runtime information
show_runtime_info

echo "📋 Configuration:"
echo "  🏗️  Platform: $PLATFORM"
echo "  📦 Base image: $BASE_IMAGE"
echo "  🎯 App image: $APP_IMAGE"
echo "  ▶️  Run after build: $RUN_AFTER_BUILD"
echo ""

# Check if base image exists using utility function
if ! image_exists "$BASE_IMAGE"; then
    echo "❌ Error: Base image '$BASE_IMAGE' not found!"
    echo ""
    echo "💡 You need to create the base image first:"
    echo "   ./docker/create-base-image.sh --platform $PLATFORM"
    echo ""
    echo "   Or pull from registry:"
    echo "   $CONTAINER_RUNTIME pull quay.io/rajivranjan/sasya-base:$PLATFORM-latest"
    echo "   $CONTAINER_RUNTIME tag quay.io/rajivranjan/sasya-base:$PLATFORM-latest $BASE_IMAGE"
    exit 1
fi

echo "✅ Base image found: $BASE_IMAGE"

# Build the app image using utility function
echo "🔨 Building app image..."
echo ""

build_args="--build-arg BASE_IMAGE=$BASE_IMAGE --build-arg PLATFORM=$PLATFORM --build-arg VERSION=v$VERSION"
build_image "./docker/Dockerfile.app" "$APP_IMAGE" "$PLATFORM" "$build_args" "false"

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 App image built successfully!"
    echo "📊 Image details:"
    $CONTAINER_RUNTIME images "$APP_IMAGE"
    
    # Interactive prompt for registry push
    echo ""
    echo "🚀 App image built successfully for $PLATFORM architecture!"
    echo "📦 Local image: $APP_IMAGE"
    echo "🌐 Registry target: quay.io/rajivranjan/$APP_IMAGE"
    echo ""
    read -p "Do you want to push this app image to quay.io registry? (y/N): " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "📤 Tagging image for registry..."
        $CONTAINER_RUNTIME tag "$APP_IMAGE" "quay.io/rajivranjan/$APP_IMAGE"
        
        echo "📤 Pushing to quay.io/rajivranjan/$APP_IMAGE..."
        if $CONTAINER_RUNTIME push "quay.io/rajivranjan/$APP_IMAGE"; then
            echo "✅ Successfully pushed $APP_IMAGE to registry!"
        else
            echo "❌ Failed to push to registry. Please check your credentials and network."
            registry_login_help "quay.io"
        fi
    else
        echo "⏭️  Skipping registry push. Image is available locally."
    fi
    
    # Run container if requested
    if [ "$RUN_AFTER_BUILD" = true ]; then
        echo ""
        run_container "$APP_IMAGE" "8080:8080" "-e OLLAMA_HOST=http://192.168.0.100:11434" ""
    fi
    
    echo ""
    echo "🎊 App build process completed successfully!"
    echo ""
    echo "📋 Summary:"
    echo "  ✅ App image: $APP_IMAGE"
    echo "  📊 Build time: Lightning fast! (~30 seconds)"
    echo ""
    echo "💡 Next steps:"
    echo "  • Test your image: $CONTAINER_RUNTIME run -p 8080:8080 $APP_IMAGE"
    echo "  • View image details: $CONTAINER_RUNTIME inspect $APP_IMAGE"
    echo "  • When code changes: Re-run this script for instant rebuilds"
    
else
    echo "❌ App image build failed!"
    echo ""
    echo "🔧 Troubleshooting:"
    echo "  • Check that base image exists: $CONTAINER_RUNTIME images | grep sasya-base"
    echo "  • Verify platform matches base image: $PLATFORM"
    echo "  • Check logs above for specific errors"
    exit 1
fi
