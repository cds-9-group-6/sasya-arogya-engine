# 🐳🐙 Docker vs Podman Runtime Compatibility Guide

This document details how the build scripts automatically handle both Docker and Podman runtimes seamlessly.

## 🔍 **Automatic Runtime Detection**

All scripts use the shared `container-runtime-utils.sh` to automatically:

1. **Detect Available Runtime**
   - Checks for Podman first (user preference on macOS)
   - Falls back to Docker if Podman not found
   - Provides installation guidance if neither found

2. **Check Runtime Capabilities**
   - BuildKit support (Docker)
   - Cache mount support (Docker/newer Podman)
   - Registry authentication status
   - Daemon status (Docker only)

3. **Optimize Commands**
   - Use runtime-specific syntax
   - Enable best features for each runtime
   - Provide runtime-specific tips

## 🐙 **Podman Advantages (Your Setup)**

```bash
# Runtime Detection Output
🔍 Detecting container runtime...
🐙 Found Podman v5.6.0
  ✅ Registry credentials detected
  💡 Podman Tips:
     • Rootless by default (more secure)
     • Compatible with Docker commands
     • No daemon required
```

**Why Podman is Great for macOS Development:**
- ✅ **Rootless** - Runs without administrator privileges
- ✅ **No Daemon** - Starts instantly, no background processes
- ✅ **Docker Compatible** - Same commands and Dockerfile syntax
- ✅ **Better Resource Usage** - Lower memory footprint
- ✅ **Secure by Default** - Containers can't escalate privileges

## 🐳 **Docker Advantages (Team Compatibility)**

```bash
# Runtime Detection Output
🔍 Detecting container runtime...
🐳 Found Docker v24.0.6
  ✅ BuildKit and cache mount support detected
  ✅ Docker daemon accessible
  💡 Docker Tips:
     • Enable BuildKit: export DOCKER_BUILDKIT=1
     • Use Docker Desktop for macOS/Windows
```

**Why Docker is Great for Teams:**
- ✅ **BuildKit** - Advanced caching and parallel builds
- ✅ **Cache Mounts** - Persistent build caches across builds
- ✅ **Widespread Adoption** - Most developers familiar
- ✅ **Ecosystem** - Extensive tooling and integrations

## 🛠️ **Runtime-Specific Optimizations**

### **Image Building**
```bash
# Podman
podman build --platform linux/arm64 -t image:tag .

# Docker (with BuildKit)
DOCKER_BUILDKIT=1 docker build --platform linux/arm64 -t image:tag .
```

### **Cache Mounting**
```bash
# Docker (with BuildKit)
RUN --mount=type=cache,target=/pip-cache pip install -r requirements.txt

# Podman (fallback to standard caching)
RUN pip install --cache-dir=/pip-cache -r requirements.txt
```

### **Image Existence Check**
```bash
# Podman
podman image exists "image:tag"

# Docker
docker image inspect "image:tag" &>/dev/null
```

## 📊 **Feature Comparison**

| Feature | Podman | Docker | Script Handling |
|---------|--------|--------|-----------------|
| **Platform Builds** | ✅ Native | ✅ Native | Auto-detected |
| **Cache Mounts** | ⚠️ Limited | ✅ Full | Fallback logic |
| **Registry Auth** | ✅ Auto | ✅ Auto | Auto-detected |
| **Rootless** | ✅ Default | ❌ Optional | Runtime-specific tips |
| **Daemon Required** | ❌ No | ✅ Yes | Status checks |
| **BuildKit** | ❌ N/A | ✅ Yes | Conditional usage |

## 🚀 **Team Workflow Recommendations**

### **For Your Development (Podman)**
```bash
# Fast, secure, daemon-free development
./docker/create-base-image.sh --platform arm64
./docker/create-app-image.sh --version 6 --platform arm64 --run
```

### **For Colleagues (Docker)**
```bash
# Same commands work with Docker
export DOCKER_BUILDKIT=1  # Enable advanced caching
./docker/create-base-image.sh --platform amd64
./docker/create-app-image.sh --version 6 --platform amd64 --run
```

### **For CI/CD (Both)**
```bash
# Works regardless of runtime
./docker/create-base-image.sh --platform both
# Individual platform builds
./docker/create-app-image.sh --version ${BUILD_NUMBER} --platform arm64
./docker/create-app-image.sh --version ${BUILD_NUMBER} --platform amd64
```

## 🔧 **Migration Between Runtimes**

### **From Docker to Podman**
```bash
# All existing Docker commands work
alias docker=podman
# Images are compatible
podman pull docker.io/your-image:tag
```

### **From Podman to Docker**
```bash
# Start Docker daemon
open -a Docker  # macOS
# Use same commands
docker pull quay.io/your-image:tag
```

## 🆘 **Troubleshooting Runtime Issues**

### **Script Shows Wrong Runtime**
```bash
# Check PATH
which podman docker
# Force detection
source docker/container-runtime-utils.sh
detect_container_runtime
```

### **Performance Differences**
```bash
# Podman: Better for development
- Faster startup (no daemon)
- Lower memory usage
- Better security

# Docker: Better for production builds
- Advanced caching (BuildKit)
- Parallel layer builds
- Ecosystem tooling
```

### **Registry Authentication**
```bash
# Both runtimes use same process
podman login quay.io  # for Podman
docker login quay.io  # for Docker
# Scripts auto-detect which to suggest
```

## 💡 **Best Practices**

1. **Use Setup Script** - Always start with `./docker/setup.sh`
2. **Let Scripts Decide** - Runtime detection is automatic
3. **Share Base Images** - Both runtimes can use same registry images
4. **Document Runtime** - Team should know which runtime is used where
5. **Test Both** - Verify builds work with both runtimes

## 🎯 **Summary**

The optimized Docker build system now provides:

- ✅ **Automatic Runtime Detection** - Works with Podman or Docker
- ✅ **Platform-Specific Builds** - ARM64 and AMD64 separation
- ✅ **Interactive Registry Control** - User prompts for pushes
- ✅ **Optimal Performance** - Runtime-specific optimizations
- ✅ **Team Compatibility** - Same commands work for everyone
- ✅ **Comprehensive Documentation** - Clear guidance for all scenarios

**Your setup (Podman on macOS) is optimized for development, while colleagues using Docker get production-grade caching features. Both work seamlessly with the same scripts!** 🚀
