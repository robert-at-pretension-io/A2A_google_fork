#!/bin/bash

# Script to help setup secret.yaml from template
set -e

# Set root directory to project root
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT_DIR"

TEMPLATE="$ROOT_DIR/deploy/kubernetes/manifests/common/secret.yaml.template"
SECRET="$ROOT_DIR/deploy/kubernetes/manifests/common/secret.yaml"

if [ -f "$SECRET" ]; then
  read -p "Secret file already exists. Overwrite? (y/n) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
  fi
fi

echo "Setting up A2A secrets file"
echo "Please enter your API keys (leave empty if not used)"

# Google API Key
read -p "Google API Key: " GOOGLE_API_KEY
GOOGLE_API_KEY_B64=$(echo -n "$GOOGLE_API_KEY" | base64)

# Vertex AI settings (if needed)
read -p "Use Vertex AI? (y/n): " -n 1 -r USE_VERTEX
echo
if [[ $USE_VERTEX =~ ^[Yy]$ ]]; then
  read -p "Google Cloud Project ID: " GCP_PROJECT
  GCP_PROJECT_B64=$(echo -n "$GCP_PROJECT" | base64)
  
  read -p "Google Cloud Location (e.g., us-central1): " GCP_LOCATION
  GCP_LOCATION_B64=$(echo -n "$GCP_LOCATION" | base64)
fi

# Elevenlabs API Key (if needed)
read -p "ElevenLabs API Key (optional): " ELEVENLABS_API_KEY
ELEVENLABS_API_KEY_B64=$(echo -n "$ELEVENLABS_API_KEY" | base64)

# Copy from template
cp "$TEMPLATE" "$SECRET"

# Replace placeholders
sed -i "s/BASE64_ENCODED_API_KEY/$GOOGLE_API_KEY_B64/g" "$SECRET"

# Add Vertex AI config if provided
if [[ $USE_VERTEX =~ ^[Yy]$ ]]; then
  sed -i "s/BASE64_ENCODED_PROJECT_ID/$GCP_PROJECT_B64/g" "$SECRET"
  sed -i "s/BASE64_ENCODED_LOCATION/$GCP_LOCATION_B64/g" "$SECRET"
else
  # Comment out the Vertex AI lines if not using
  sed -i "s/^  GOOGLE_CLOUD_PROJECT.*/#  GOOGLE_CLOUD_PROJECT: BASE64_ENCODED_PROJECT_ID/g" "$SECRET"
  sed -i "s/^  GOOGLE_CLOUD_LOCATION.*/#  GOOGLE_CLOUD_LOCATION: BASE64_ENCODED_LOCATION/g" "$SECRET"
fi

# Add ElevenLabs API key if provided
if [ ! -z "$ELEVENLABS_API_KEY" ]; then
  sed -i "s/BASE64_ENCODED_ELEVENLABS_KEY/$ELEVENLABS_API_KEY_B64/g" "$SECRET"
else
  # Comment out if not using
  sed -i "s/^  ELEVENLABS_API_KEY.*/#  ELEVENLABS_API_KEY: BASE64_ENCODED_ELEVENLABS_KEY/g" "$SECRET"
fi

echo "✅ Secret file created at: $SECRET"
echo "You can now deploy using the deploy.sh script"