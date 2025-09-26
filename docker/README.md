# 🚀 Docker Optimization Guide for Sasya Arogya Engine - Platform-Specific

This guide provides comprehensive Docker build optimizations to reduce build times from **15+ minutes to 30 seconds** and minimize internet downloads during development. All builds are **platform-specific** supporting both **ARM64** (Apple Silicon) and **AMD64** (Intel/AMD) architectures separately.

## 📊 Performance Comparison

| Strategy | First Build | Code Changes | Dependencies Download | Local Cache |
|----------|-------------|--------------|----------------------|-------------|
| **Original** | ~15-20 min | ~15-20 min | 2.5GB+ every time | ❌ None |
| **Optimized** | ~10-15 min | ~2-5 min | Cached locally | ✅ Full pip cache |
| **Base Image** | ~15 min (once) | ~30 seconds | Pre-installed | ✅ Pre-built deps |

## 🎯 Quick Start - Platform-Specific

### 🍎 For Apple Silicon (ARM64)

#### Option 1: Instant Optimization (Recommended for Development)
```bash
# Setup (one-time)
./docker/setup.sh

# Build with local caching (much faster subsequent builds)
./docker/create-image-engine-optimized.sh \
  --version 6 \
  --platform arm64 \
  --use-local-cache \
  --run
```

#### Option 2: Maximum Performance (Recommended for Production)
```bash
# Step 1: Create base image (one-time setup per platform)
./docker/create-base-image.sh --platform arm64

# Step 2: Lightning-fast app builds (30 seconds!)
./docker/create-app-image.sh --version 6 --platform arm64 --run
```

### 💻 For Intel/AMD (AMD64)

#### Option 1: Instant Optimization (Recommended for Development)
```bash
# Setup (one-time)
./docker/setup.sh

# Build with local caching (much faster subsequent builds)
./docker/create-image-engine-optimized.sh \
  --version 6 \
  --platform amd64 \
  --use-local-cache \
  --run
```

#### Option 2: Maximum Performance (Recommended for Production)
```bash
# Step 1: Create base image (one-time setup per platform)
./docker/create-base-image.sh --platform amd64

# Step 2: Lightning-fast app builds (30 seconds!)
./docker/create-app-image.sh --version 6 --platform amd64 --run
```

### 🌐 For Both Platforms (CI/CD)
```bash
# Create base images for both platforms
./docker/create-base-image.sh --platform both

# Build app images for both platforms
./docker/create-image-engine-optimized.sh --version 6 --platform both
```

## 🎛️ Quick Reference - Registry Push Control

**All scripts ask before pushing to quay.io/rajivranjan**:
- ✅ **Press Enter** (default) = Skip push, keep local
- ✅ **Press 'y'** = Push to registry for team sharing
- ✅ **Authentication**: `podman login quay.io` (one-time setup)
- ✅ **Manual push later**: Scripts show exact commands if you skip

**💡 Recommended workflow**: Skip pushes during development, push base images for team sharing.

[📖 **Full push control documentation →**](#🎛️-registry-push-control)

## 📁 File Structure

```
docker/
├── README.md                           # This comprehensive guide
├── setup.sh                            # One-time setup script (makes all executable)
├── container-runtime-utils.sh          # 🆕 Docker/Podman compatibility utilities
├── Dockerfile.engine                   # Original Dockerfile
├── Dockerfile.engine.optimized         # Optimized version with platform-specific caching
├── Dockerfile.base                     # Platform-specific base image with all dependencies  
├── Dockerfile.app                      # Platform-specific app-only image (uses base)
├── create-image-engine.sh              # Original build script
├── create-image-engine-optimized.sh    # Platform-aware optimized build script (Docker/Podman)
├── create-base-image.sh                # Platform-specific base image creation script (Docker/Podman)
└── create-app-image.sh                 # Platform-specific lightning-fast app builds (Docker/Podman)
.dockerignore                           # Optimized build context (90% smaller)
```

## 🐳 Docker vs Podman Compatibility

All scripts **automatically detect** and work seamlessly with both Docker and Podman runtimes:

### 🐙 **Podman** (Recommended for macOS)
- ✅ **Rootless by default** (more secure)
- ✅ **No daemon required** (faster startup)
- ✅ **Docker CLI compatible** (drop-in replacement)
- ✅ **Better for development** on macOS
- ⚠️ Limited cache mount support (depending on version)

### 🐳 **Docker** (Team Compatibility)
- ✅ **BuildKit support** (advanced caching)
- ✅ **Cache mount support** (faster builds)
- ✅ **Widely adopted** in teams
- ✅ **Extensive ecosystem**
- ⚠️ Requires daemon to be running

### 🔍 **Automatic Detection**

The scripts automatically:
1. **Detect available runtime** (Podman first, then Docker)
2. **Check capabilities** (cache mounts, BuildKit)
3. **Optimize commands** for each runtime
4. **Provide helpful tips** specific to your runtime

```bash
# Example detection output
🔍 Detecting container runtime...
🐙 Found Podman v5.6.0
  ✅ Registry credentials detected
  💡 Podman Tips:
     • Rootless by default (more secure)
     • Compatible with Docker commands
```

## 🔧 Detailed Usage

### 1. Optimized Build Script

**Purpose**: Enhanced version of original script with local caching and better user experience.

**Usage**:
```bash
./docker/create-image-engine-optimized.sh [OPTIONS]
```

**Options**:
- `--version <version>` *(required)*: Version number for the image
- `--platform <arch>`: Build for specific architecture (`amd64`, `arm64`, or `both`)
- `--use-local-cache`: Use local pip cache to avoid re-downloading packages
- `--run`: Run the container after building
- `--dockerfile <path>`: Specify custom Dockerfile path

**Examples**:
```bash
# Basic optimized build
./docker/create-image-engine-optimized.sh --version 6 --platform arm64

# Build with local cache and run immediately
./docker/create-image-engine-optimized.sh \
  --version 6 \
  --platform arm64 \
  --use-local-cache \
  --run

# Build for both architectures with caching
./docker/create-image-engine-optimized.sh \
  --version 6 \
  --platform both \
  --use-local-cache
```

**Interactive Features**:
- ✅ Prompts whether to push to quay.io registry
- ✅ Shows image sizes and build summary
- ✅ Provides next steps and commands
- ✅ Error handling with helpful messages

### 2. Base Image Strategy

**Purpose**: Build a base image once with all dependencies, then build app images in seconds.

#### Step 1: Create Base Image

```bash
./docker/create-base-image.sh [--platform <arch>]
```

**Examples**:
```bash
# Create base image for ARM64
./docker/create-base-image.sh --platform arm64

# Create base images for both architectures
./docker/create-base-image.sh --platform both
```

**What it does**:
- ✅ Installs all system dependencies
- ✅ Downloads and installs all Python packages
- ✅ Creates optimized base image (~1.5GB)
- ✅ Optionally pushes to registry for team sharing

#### Step 2: Build App Image

```bash
# Using the dedicated app script (recommended - super fast!)
./docker/create-app-image.sh --version 6 --platform arm64 --run

# Or manually using Dockerfile.app
podman build -f docker/Dockerfile.app \
  --build-arg BASE_IMAGE=localhost/sasya-base:arm64-latest \
  --build-arg PLATFORM=arm64 \
  --build-arg VERSION=v6 \
  -t engine:arm64-v6 .
```

**Benefits**:
- ⚡ **30-second builds** for code changes
- 🔄 **No dependency downloads** (pre-installed in base)
- 📦 **Smaller final images** (layered approach)
- 🚀 **Perfect for CI/CD** pipelines

### 3. App Image Script (Lightning Fast)

**Purpose**: Build app images using pre-built base images in ~30 seconds.

**Usage**:
```bash
./docker/create-app-image.sh [OPTIONS]
```

**Options**:
- `--version <version>` *(required)*: Version number for the app image
- `--platform <platform>` *(required)*: Architecture (`amd64` or `arm64`)
- `--run`: Run the container after building
- `--base-registry <registry>`: Registry for base image (default: `localhost`)

**Examples**:
```bash
# Basic app build for ARM64
./docker/create-app-image.sh --version 6 --platform arm64

# Build and run immediately
./docker/create-app-image.sh --version 6 --platform arm64 --run

# Use base image from registry
./docker/create-app-image.sh \
  --version 6 \
  --platform arm64 \
  --base-registry quay.io/rajivranjan
```

**Interactive Features**:
- ✅ Validates base image exists before building
- ✅ Prompts whether to push to registry
- ✅ Shows build time and image details
- ✅ Provides troubleshooting guidance if build fails

**Prerequisites**:
- Base image must exist: `localhost/sasya-base:<platform>-latest`
- Create with: `./docker/create-base-image.sh --platform <platform>`

### 4. Local Package Caching

**How it works**:
```bash
# Your local pip cache location
~/.cache/pip/

# The script mounts this during build
--mount=type=cache,target=/pip-cache
```

**Benefits**:
- ✅ Packages downloaded once, reused forever
- ✅ Works across different projects
- ✅ Survives container rebuilds
- ✅ Reduces internet dependency

## 🛠️ Advanced Optimizations

### 1. Build Context Optimization

The `.dockerignore` file excludes unnecessary files:

```bash
# What's excluded (90% size reduction):
- .git/ (version control)
- __pycache__/ (Python cache)
- *.md (documentation)
- images/ (large media files)
- tests/ (test files)
- backup/ (backup files)
```

### 2. Layer Caching Strategy

**Optimized Dockerfile structure**:
```dockerfile
# 1. System dependencies (rarely change)
RUN apt-get install ...

# 2. Requirements file only (changes less frequently)
COPY requirements.txt .
RUN pip install -r requirements.txt

# 3. Application code (changes most frequently)
COPY ./fsm_agent ./ml ./core .
```

### 3. Multi-Architecture Support

**Building for different platforms**:
```bash
# ARM64 (Apple Silicon, modern ARM servers)
--platform linux/arm64

# AMD64 (Intel/AMD processors)
--platform linux/amd64

# Both (CI/CD or distribution)
--platform both
```

## 🚨 Troubleshooting

### Build Failures

**Error**: "COPY failed: no such file or directory"
```bash
# Solution: Check .dockerignore and ensure required files aren't excluded
cat .dockerignore
```

**Error**: "registry push failed"
```bash
# Solution: Login to registry (auto-detected)
# For Podman:
podman login quay.io

# For Docker:
docker login quay.io

# Scripts will show the correct command for your runtime
```

💡 **See [Registry Push Control](#🎛️-registry-push-control) for complete push management guide.**

**Error**: "platform not supported"
```bash
# Solution: Use correct platform flag
--platform linux/arm64  # for Apple Silicon
--platform linux/amd64  # for Intel/AMD
```

### Cache Issues

**Cache not working**:
```bash
# Check cache directory
ls -la ~/.cache/pip/

# Clear cache if corrupted
rm -rf ~/.cache/pip/
```

**Base image outdated**:
```bash
# Rebuild base image when requirements.txt changes
./docker/create-base-image.sh --platform arm64
```

### Runtime-Specific Issues

**Podman: "command not found"**:
```bash
# Install Podman on macOS
brew install podman

# Or download from: https://podman.io/getting-started/installation
```

**Docker: "daemon not running"**:
```bash
# Start Docker Desktop (macOS)
open -a Docker

# Or start Docker service (Linux)
sudo systemctl start docker
```

**Podman: "registry authentication required"**:
```bash
# Login to registry
podman login quay.io
# The script will detect this automatically
```

**Docker: "BuildKit not enabled"**:
```bash
# Enable BuildKit for better caching
export DOCKER_BUILDKIT=1
# Or add to ~/.bashrc for persistence
```

### Registry Issues

**Push permissions**:
```bash
# Login with your credentials
podman login quay.io
# Enter username and password/token
```

**Rate limiting**:
```bash
# Use base images to reduce pulls
# Or set up local registry mirror
```

## 📋 Best Practices

### Development Workflow (Platform-Specific)

#### 🍎 Apple Silicon (ARM64) Workflow:
1. **First time setup**:
   ```bash
   ./docker/setup.sh
   ./docker/create-base-image.sh --platform arm64
   ```

2. **Daily development**:
   ```bash
   # Lightning-fast app builds (30 seconds)
   ./docker/create-app-image.sh --version 6 --platform arm64
   ```

3. **When dependencies change**:
   ```bash
   # Rebuild base image only
   ./docker/create-base-image.sh --platform arm64
   ```

#### 💻 Intel/AMD (AMD64) Workflow:
1. **First time setup**:
   ```bash
   ./docker/setup.sh
   ./docker/create-base-image.sh --platform amd64
   ```

2. **Daily development**:
   ```bash
   # Lightning-fast app builds (30 seconds)
   ./docker/create-app-image.sh --version 6 --platform amd64
   ```

3. **When dependencies change**:
   ```bash
   # Rebuild base image only
   ./docker/create-base-image.sh --platform amd64
   ```

### Production Deployment

1. **CI/CD Pipeline**:
   ```bash
   # Use base image for fast builds
   ./docker/create-image-engine-optimized.sh \
     --version $BUILD_NUMBER \
     --platform both \
     --dockerfile docker/Dockerfile.app
   ```

2. **Registry Strategy**:
   - Push base images to shared registry
   - Team pulls base images instead of building
   - App images build in seconds

### Team Collaboration

1. **Share base images**:
   ```bash
   # Team lead creates and pushes base image
   ./docker/create-base-image.sh --platform both
   # (Choose 'y' when prompted to push)
   
   # Team members pull and use
   podman pull quay.io/rajivranjan/sasya-base:arm64-latest
   ```

2. **Consistent environments**:
   - Everyone uses same base image
   - Reduces "works on my machine" issues
   - Faster onboarding for new developers

## 📊 Monitoring and Maintenance

### Check Image Sizes
```bash
# List all images with sizes
podman images | grep engine

# Check specific image layers
podman history localhost/engine:arm64-v6
```

### Clean Up
```bash
# Remove unused images
podman system prune -a

# Remove specific images
podman rmi engine:arm64-v5

# Check disk usage
du -sh ~/.cache/pip/
```

### Update Strategy
```bash
# Monthly: Update base images
./docker/create-base-image.sh --platform both

# Weekly: Clean up old images
podman system prune

# Daily: Use app-only builds
podman build -f docker/Dockerfile.app -t engine:latest .
```

## 🔗 Related Files

- **[pyproject.toml](../pyproject.toml)**: Project dependencies
- **[requirements.txt](../requirements.txt)**: Compiled dependencies
- **[.dockerignore](../.dockerignore)**: Build context optimization
- **[fsm_agent/](../fsm_agent/)**: Main application code

## 💡 Tips and Tricks

### Speed Up Builds Further

1. **Use SSD storage** for Docker cache
2. **Increase Docker memory** allocation
3. **Use build cache mounts** with BuildKit
4. **Pre-warm pip cache** with common packages

### Security Considerations

1. **Use non-root user** (already implemented)
2. **Scan images** for vulnerabilities
3. **Keep base images updated** regularly
4. **Use specific package versions** (already in requirements.txt)

### Cost Optimization

1. **Reduce registry pushes** (use interactive prompts)
2. **Share base images** across team
3. **Use multi-stage builds** for smaller images
4. **Clean up regularly** to save storage

## 🎛️ Registry Push Control

All scripts provide **interactive control** over pushes to `quay.io/rajivranjan` registry:

### 🤔 **Interactive Prompts (Default Behavior)**

Every script **automatically asks** before pushing:

```bash
🚀 Image built successfully for arm64 architecture!
📦 Local image: localhost/engine:arm64-v6
🌐 Registry target: quay.io/rajivranjan/engine:arm64-v6

Do you want to push this image to quay.io registry? (y/N): 
```

**Your options:**
- Press **`y`** or **`Y`** + Enter to push
- Press **`n`**, **`N`**, or just **Enter** to skip (default)

### 🎯 **Push Control Strategies**

#### **Development Mode (No Pushes)**
```bash
# For daily development - keep everything local
./docker/create-base-image.sh --platform arm64
# Press Enter when prompted (defaults to No)

./docker/create-app-image.sh --version 6 --platform arm64 --run  
# Press Enter when prompted (defaults to No)
```

#### **Team Sharing Mode (Selective Pushes)**
```bash
# Push base images for team sharing (infrequent)
./docker/create-base-image.sh --platform arm64
# Press 'y' when prompted ✅

# Skip app image pushes (frequent changes)
./docker/create-app-image.sh --version 6 --platform arm64
# Press Enter when prompted (skip)
```

#### **Release Mode (Push Everything)**
```bash
# For releases - push both base and app images
./docker/create-base-image.sh --platform arm64  
# Press 'y' when prompted ✅

./docker/create-app-image.sh --version 6 --platform arm64
# Press 'y' when prompted ✅
```

### 🔐 **Registry Authentication**

#### **First-Time Setup:**
```bash
# Login to your quay.io account (one-time setup)
podman login quay.io
# Enter your quay.io username and password/token

# Verify authentication
./docker/setup.sh
# Look for: "✅ Registry credentials detected"
```

#### **Authentication Control:**
```bash
# Check if authenticated
podman info --format "{{.Registries}}"

# Logout to prevent any pushes
podman logout quay.io

# Login with token (for automation)
echo "YOUR_TOKEN" | podman login quay.io --username YOUR_USERNAME --password-stdin
```

### 📋 **Manual Push Control**

If you skip the automatic push, you can **manually push later**:

```bash
# For base images
podman tag sasya-base:arm64-latest quay.io/rajivranjan/sasya-base:arm64-latest
podman push quay.io/rajivranjan/sasya-base:arm64-latest

# For app images  
podman tag engine:arm64-v6 quay.io/rajivranjan/engine:arm64-v6
podman push quay.io/rajivranjan/engine:arm64-v6
```

### 🤖 **Automated Push Control**

For **CI/CD or scripted builds**:

```bash
# Always skip pushes
echo "n" | ./docker/create-app-image.sh --version 6 --platform arm64

# Always push
echo "y" | ./docker/create-app-image.sh --version 6 --platform arm64

# Local-only wrapper script
cat > docker/build-local-only.sh << 'EOF'
#!/bin/bash
echo "n" | ./docker/create-base-image.sh --platform arm64
echo "n" | ./docker/create-app-image.sh --version 6 --platform arm64 --run
EOF
chmod +x docker/build-local-only.sh
```

### 🛡️ **Security Best Practices**

#### **Repository Access:**
- **Public repos**: Anyone can pull, only you can push
- **Private repos**: Only authenticated users can pull/push

#### **Token-Based Authentication:**
```bash
# Generate tokens in quay.io settings
# Use tokens instead of passwords for better security
```

#### **Robot Accounts (For Automation):**
```bash
# Create robot accounts in quay.io for CI/CD
podman login quay.io --username "rajivranjan+robot_name"
```

### 📊 **Monitoring Pushes**

```bash
# List images in registry
podman search quay.io/rajivranjan/

# List local images
podman images | grep quay.io/rajivranjan

# Compare local vs registry versions
podman images localhost/engine:arm64-v6
podman images quay.io/rajivranjan/engine:arm64-v6
```

### 🚫 **Prevent Accidental Pushes**

1. **Logout from registry**: `podman logout quay.io`
2. **Use local-only scripts**: Create wrapper scripts that auto-decline pushes
3. **Safe defaults**: All prompts default to "No" - just press Enter

### 💡 **Push Control Tips**

- **Base images**: Push occasionally for team sharing
- **App images**: Usually keep local for development
- **Releases**: Push both base and app images
- **Failed pushes**: Don't break builds, show helpful login commands
- **Authentication**: One-time setup, works across all scripts

---

## 🆘 Support

If you encounter issues:

1. **Check logs**: `podman logs <container-id>`
2. **Verify permissions**: `ls -la docker/*.sh`
3. **Test connectivity**: `ping quay.io`
4. **Check disk space**: `df -h`

**Need help?** Check the troubleshooting section above or create an issue in the repository.

---

*This optimization guide was created to reduce build times from 15+ minutes to under 30 seconds. Happy building! 🚀*
