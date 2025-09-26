#!/bin/bash

# Docker Optimization Setup Script
# This script makes all Docker scripts executable and provides setup instructions

echo "🚀 Setting up Docker optimization tools..."
echo ""

# Check if we're in the correct directory
CURRENT_DIR=$(pwd)
if [[ ! "$CURRENT_DIR" =~ .*/sasya-arogya-engine$ ]]; then
    echo "❌ Error: This script must be run from the sasya-arogya-engine directory."
    echo "Current directory: $CURRENT_DIR"
    exit 1
fi

# Make all scripts executable
echo "📝 Making scripts executable..."
chmod +x docker/create-image-engine-optimized.sh
chmod +x docker/create-base-image.sh
chmod +x docker/create-app-image.sh
chmod +x docker/create-image-engine.sh  # Original script
chmod +x docker/container-runtime-utils.sh  # Runtime utilities

echo "✅ All scripts are now executable!"
echo ""

# Source and test container runtime utilities
source ./docker/container-runtime-utils.sh

echo "🔍 Testing container runtime detection..."
if detect_container_runtime; then
    echo "✅ Container runtime detection working properly!"
    show_runtime_info
else
    echo "⚠️  Container runtime setup needed. Please install:"
    echo "  🐙 Podman (recommended): https://podman.io/getting-started/installation"
    echo "  🐳 Docker: https://docs.docker.com/get-docker/"
    echo ""
    echo "📱 macOS users can use:"
    echo "  • brew install podman"
    echo "  • Docker Desktop from docker.com"
fi

# Check for uv package manager
if command -v uv &> /dev/null; then
    echo "📦 Found uv package manager - will use for fast dependency resolution"
else
    echo "💡 Consider installing uv for faster builds: pip install uv"
fi

echo ""
echo "🎯 Quick Start Options (Platform-specific):"
echo ""
echo "🍎 For Apple Silicon (ARM64):"
echo "  1️⃣  Optimized build: ./docker/create-image-engine-optimized.sh --version 6 --platform arm64 --use-local-cache"
echo "  2️⃣  Base image strategy: ./docker/create-base-image.sh --platform arm64"
echo "  3️⃣  Lightning app build: ./docker/create-app-image.sh --version 6 --platform arm64"
echo ""
echo "💻 For Intel/AMD (AMD64):"
echo "  1️⃣  Optimized build: ./docker/create-image-engine-optimized.sh --version 6 --platform amd64 --use-local-cache"
echo "  2️⃣  Base image strategy: ./docker/create-base-image.sh --platform amd64"
echo "  3️⃣  Lightning app build: ./docker/create-app-image.sh --version 6 --platform amd64"
echo ""
echo "🌐 For both platforms:"
echo "  🔄 Multi-platform base: ./docker/create-base-image.sh --platform both"
echo "  🔄 Multi-platform build: ./docker/create-image-engine-optimized.sh --version 6 --platform both"
echo ""
echo "📚 Full documentation:"
echo "   cat docker/README.md"
echo ""
echo "✨ Setup complete! Ready for platform-specific lightning-fast Docker builds!"
