#!/bin/bash

# Optimized Docker build script with local package caching
# Usage: ./docker/create-image-engine-optimized.sh --version <version> [--platform amd64|arm64] [--run] [--use-local-cache]

# Check if we're in the correct directory (should be /sasya-arogya-engine)
CURRENT_DIR=$(pwd)
if [[ ! "$CURRENT_DIR" =~ .*/sasya-arogya-engine$ ]]; then
    echo "Error: This script must be run from the sasya-arogya-engine directory."
    echo "Current directory: $CURRENT_DIR"
    echo "Please navigate to the sasya-arogya-engine directory and run the script again."
    echo "Example: cd /path/to/sasya-arogya-engine && ./docker/create-image-engine-optimized.sh --version 6"
    exit 1
fi

echo "Running from correct directory: $CURRENT_DIR"

# Source container runtime utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/container-runtime-utils.sh"

# Detect and configure container runtime
if ! detect_container_runtime; then
    exit 1
fi

# Parse command line arguments
RUN_AFTER_BUILD=false
ARCH=""
VERSION=""
USE_LOCAL_CACHE=false
DOCKERFILE="./docker/Dockerfile.engine.optimized"

while [[ $# -gt 0 ]]; do
    case $1 in
        --run)
            RUN_AFTER_BUILD=true
            shift
            ;;
        --platform)
            if [[ $# -lt 2 ]] || [[ ! "$2" =~ ^(amd64|arm64)$ ]]; then
                echo "Error: --platform requires a value (amd64 or arm64)"
                exit 1
            fi
            ARCH="$2"
            shift 2
            ;;
        --version)
            if [[ $# -lt 2 ]] || [[ -z "$2" ]]; then
                echo "Error: --version requires a value"
                exit 1
            fi
            VERSION="$2"
            shift 2
            ;;
        --use-local-cache)
            USE_LOCAL_CACHE=true
            shift
            ;;
        --dockerfile)
            if [[ $# -lt 2 ]] || [[ -z "$2" ]]; then
                echo "Error: --dockerfile requires a value"
                exit 1
            fi
            DOCKERFILE="$2"
            shift 2
            ;;
        *)
            echo "Error: Unknown option $1"
            echo "Usage: $0 --version <version> [--platform amd64|arm64] [--run] [--use-local-cache] [--dockerfile path]"
            echo "  --version: Version number for the image (mandatory)"
            echo "  --platform: Build for specific architecture (amd64 or arm64, default: both)"
            echo "  --run: Run the container after building (default: false)"
            echo "  --use-local-cache: Use local pip cache directory (default: false)"
            echo "  --dockerfile: Specify dockerfile path (default: ./docker/Dockerfile.engine.optimized)"
            exit 1
            ;;
    esac
done

# Validation: version is mandatory
if [ -z "$VERSION" ]; then
    echo "Error: --version is mandatory"
    echo "Usage: $0 --version <version> [options]"
    echo "Example: $0 --version 6 --platform amd64 --use-local-cache --run"
    exit 1
fi

# Validation: if --run is true, --platform must be specified
if [ "$RUN_AFTER_BUILD" = true ] && [ -z "$ARCH" ]; then
    echo "Error: --run requires --platform to be specified"
    exit 1
fi

if [ -z "$ARCH" ]; then
    ARCH="both"
fi

# Setup local pip cache directory
LOCAL_PIP_CACHE="$HOME/.cache/pip"
if [ "$USE_LOCAL_CACHE" = true ]; then
    echo "Setting up local pip cache directory: $LOCAL_PIP_CACHE"
    mkdir -p "$LOCAL_PIP_CACHE"
fi

echo "--------------------------------"
echo "Building for architecture: $ARCH"
echo "Version: $VERSION"
echo "Running after build: $RUN_AFTER_BUILD"
echo "Using local cache: $USE_LOCAL_CACHE"
echo "Dockerfile: $DOCKERFILE"
echo "Starting the optimized build"

# Show runtime information
show_runtime_info

# Create/update requirements file if uv is available
if command -v uv &> /dev/null; then
    echo "Using uv package manager to compile requirements..."
    uv pip compile ./pyproject.toml -o ./requirements.txt
else
    echo "*** Using existing requirements.txt file ***"
    echo "For faster dependency resolution, install uv: pip install uv"
fi

# Function to build image with optimizations
build_image() {
    local platform=$1
    local tag_suffix=$2
    
    echo "Building for $platform..."
    
    # Pull base image if not exists
    if ! image_exists "localhost/python:$tag_suffix"; then
        echo "Pulling base image for $platform..."
        pull_image "python:3.12-slim" "$platform"
        $CONTAINER_RUNTIME tag docker.io/library/python:3.12-slim localhost/python:$tag_suffix
    else
        echo "Base image localhost/python:$tag_suffix already exists, skipping pull"
    fi
    
    # Prepare build arguments with platform and version
    BUILD_ARGS="--build-arg BASE_TAG=$tag_suffix --build-arg PLATFORM=$platform --build-arg VERSION=v$VERSION"
    
    # Add cache mount if using local cache
    if [ "$USE_LOCAL_CACHE" = true ]; then
        if [ "$CONTAINER_RUNTIME" = "docker" ]; then
            # Docker BuildKit cache mount
            BUILD_ARGS="$BUILD_ARGS --build-arg BUILDKIT_INLINE_CACHE=1"
        fi
    fi
    
    # Build the image
    if [ "$USE_LOCAL_CACHE" = true ] && [ "$CONTAINER_RUNTIME" = "docker" ]; then
        # Use BuildKit for cache mounting (Docker only)
        DOCKER_BUILDKIT=1 $CONTAINER_RUNTIME build \
            --platform linux/$platform \
            $BUILD_ARGS \
            -t engine:$platform-v$VERSION \
            -f $DOCKERFILE \
            .
    else
        # Standard build
        $CONTAINER_RUNTIME build \
            --platform linux/$platform \
            $BUILD_ARGS \
            -t engine:$platform-v$VERSION \
            -f $DOCKERFILE \
            .
    fi
    
    # Tag and push if successful
    if [ $? -eq 0 ]; then
        echo "Successfully built engine:$platform-v$VERSION"
        echo "Image size:"
        $CONTAINER_RUNTIME images localhost/engine:$platform-v$VERSION
        
        # Interactive prompt for registry push
        echo ""
        echo "🚀 Image built successfully for $platform architecture!"
        echo "📦 Local image: localhost/engine:$platform-v$VERSION"
        echo "🌐 Registry target: quay.io/rajivranjan/engine:$platform-v$VERSION"
        echo ""
        read -p "Do you want to push this image to quay.io registry? (y/N): " -n 1 -r
        echo ""
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "📤 Tagging image for registry..."
            $CONTAINER_RUNTIME tag localhost/engine:$platform-v$VERSION quay.io/rajivranjan/engine:$platform-v$VERSION
            
            echo "📤 Pushing to quay.io/rajivranjan/engine:$platform-v$VERSION..."
            if $CONTAINER_RUNTIME push quay.io/rajivranjan/engine:$platform-v$VERSION; then
                echo "✅ Successfully pushed engine:$platform-v$VERSION to registry!"
            else
                echo "❌ Failed to push to registry. Please check your credentials and network."
                registry_login_help "quay.io"
                return 1
            fi
        else
            echo "⏭️  Skipping registry push. Image is available locally."
        fi
    else
        echo "❌ Build failed for $platform"
        exit 1
    fi
}

# Build for specified architectures
if [ "$ARCH" = "amd64" ] || [ "$ARCH" = "both" ]; then
    build_image "amd64" "amd64-3.12-slim"
fi

if [ "$ARCH" = "arm64" ] || [ "$ARCH" = "both" ]; then
    build_image "arm64" "arm64-3.12-slim"
fi

# Run container if requested
if [ "$RUN_AFTER_BUILD" = true ]; then
    echo "Starting container..."
    
    # Mount local cache if using it
    MOUNT_ARGS=""
    if [ "$USE_LOCAL_CACHE" = true ]; then
        MOUNT_ARGS="-v $LOCAL_PIP_CACHE:/pip-cache:ro"
    fi
    
    if [ "$ARCH" = "amd64" ]; then
        run_container "localhost/engine:amd64-v$VERSION" "8080:8080" "-e OLLAMA_HOST=http://192.168.0.100:11434" "$MOUNT_ARGS"
    elif [ "$ARCH" = "arm64" ]; then
        run_container "localhost/engine:arm64-v$VERSION" "8080:8080" "-e OLLAMA_HOST=http://192.168.0.100:11434" "$MOUNT_ARGS"
    fi
fi

echo ""
echo "🎉 Build process completed successfully!"
echo ""
echo "📋 Summary:"
if [ "$ARCH" = "amd64" ] || [ "$ARCH" = "both" ]; then
    echo "  ✅ AMD64 image: localhost/engine:amd64-v$VERSION"
fi
if [ "$ARCH" = "arm64" ] || [ "$ARCH" = "both" ]; then
    echo "  ✅ ARM64 image: localhost/engine:arm64-v$VERSION"
fi
echo ""
echo "💡 Next steps:"
echo "  • Test your image: $CONTAINER_RUNTIME run -p 8080:8080 localhost/engine:<arch>-v$VERSION"
echo "  • View all images: $CONTAINER_RUNTIME images"
echo "  • Clean up: $CONTAINER_RUNTIME system prune"
