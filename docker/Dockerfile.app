# Application Dockerfile using pre-built base image - Platform-specific
# This will build very fast since all dependencies are pre-installed in base image
# 
# Build commands (choose platform-specific):
# ARM64: podman build --platform linux/arm64 --build-arg BASE_IMAGE=localhost/sasya-base:arm64-latest --build-arg PLATFORM=arm64 -t engine:arm64-v6 -f ./docker/Dockerfile.app .
# AMD64: podman build --platform linux/amd64 --build-arg BASE_IMAGE=localhost/sasya-base:amd64-latest --build-arg PLATFORM=amd64 -t engine:amd64-v6 -f ./docker/Dockerfile.app .

ARG BASE_IMAGE
ARG PLATFORM
ARG VERSION

FROM ${BASE_IMAGE}

WORKDIR /app

# Copy application code only (very fast since no pip installs)
COPY ./fsm_agent ./fsm_agent
COPY ./ml ./ml
COPY ./core ./core

# Create empty __init__.py for package structure
RUN touch ./__init__.py

# Add platform and version labels for identification
LABEL sasya.platform=${PLATFORM}
LABEL sasya.type="app"
LABEL sasya.version=${VERSION}

# Switch to non-root user
USER appuser

EXPOSE 8080

CMD ["python", "./fsm_agent/run_fsm_server.py", "--host", "0.0.0.0", "--port", "8080"]
