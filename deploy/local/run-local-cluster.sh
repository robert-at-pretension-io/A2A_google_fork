#!/bin/bash

# Quick script to run the A2A local cluster with Docker Compose
# Created by Claude

cd "$(dirname "$0")"

echo "Starting A2A local cluster..."

# Check if .env exists
if [ ! -f ".env" ]; then
  echo "Error: .env file not found!"
  echo "Please create it by copying .env.template and filling in your API keys"
  exit 1
fi

# Clean up any previous failed containers
echo "Cleaning up any previous containers..."
docker compose down --volumes

# Build images only when sources have changed
echo "Building images if needed..."
docker compose build

# Start services
echo "Starting services..."
docker compose up -d

# Wait for services to start up
echo "Waiting for services to start..."
sleep 15

# Check if containers are running
RUNNING_COUNT=$(docker compose ps --services --filter "status=running" | wc -l)
if [ "$RUNNING_COUNT" -lt 3 ]; then
  echo "⚠️ Warning: Not all containers appear to be running"
  echo "Check container status with: docker compose ps"
  
  # Show logs for failed containers
  echo "\nLogs from containers:"
  docker compose logs
else
  echo "✅ All containers are running!"
fi

echo ""
echo "A2A Demo is now available at: http://localhost:12001"
echo ""
echo "To register agents in the UI, go to 'Remote Agents' tab and add:"
echo "- agent-google-adk:10002"
echo "- agent-elevenlabs-tts:10005 (if using ElevenLabs)"
echo "- agent-vertex-image-gen:10006 (if using Vertex AI)"
echo ""
echo "To stop the cluster, run:"
echo "docker compose down"