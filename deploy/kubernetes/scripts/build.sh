#!/bin/bash

# Script to build A2A Docker images
set -e

# Set root directory to project root
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT_DIR"

echo "Building A2A Docker images from $ROOT_DIR"

# Build UI image
echo "🔨 Building UI image..."
docker build -t a2a-ui:latest -f deploy/kubernetes/docker/ui/Dockerfile .

# Get list of agent directories
AGENT_DIRS=$(ls -d samples/python/agents/*/ | cut -d'/' -f4)

# Build agent images
for AGENT in $AGENT_DIRS; do
  if [ -d "samples/python/agents/$AGENT" ]; then
    # Check if agent has its own pyproject.toml or uses the parent one
    if [ -f "samples/python/agents/$AGENT/pyproject.toml" ] || [ -f "samples/python/agents/$AGENT/__main__.py" ]; then
      echo "🔨 Building agent: $AGENT"
      docker build -t a2a-agent:$AGENT --build-arg AGENT_DIR=$AGENT -f deploy/kubernetes/docker/agent/Dockerfile .
    else
      echo "⚠️ Skipping agent $AGENT (no pyproject.toml or __main__.py found)"
    fi
  fi
done

echo "✅ All images built successfully"