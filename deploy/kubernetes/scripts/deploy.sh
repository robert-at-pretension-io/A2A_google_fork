#!/bin/bash

# Script to deploy A2A components to Kubernetes
set -e

# Set root directory to project root
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT_DIR"

function print_usage {
  echo "Usage: ./deploy.sh [ui|all|<agent-name>]"
  echo "  ui         - Deploy only the UI"
  echo "  all        - Deploy UI and all agents"
  echo "  <agent>    - Deploy a specific agent (e.g., google_adk, elevenlabs_tts)"
  echo "Examples:"
  echo "  ./deploy.sh ui"
  echo "  ./deploy.sh google_adk"
  echo "  ./deploy.sh all"
}

# Deploy UI
function deploy_ui {
  echo "🚀 Deploying UI..."
  kubectl apply -f "$ROOT_DIR/deploy/kubernetes/manifests/common/configmap.yaml"
  kubectl apply -f "$ROOT_DIR/deploy/kubernetes/manifests/common/secret.yaml"
  kubectl apply -f "$ROOT_DIR/deploy/kubernetes/manifests/ui/pvc.yaml"
  kubectl apply -f "$ROOT_DIR/deploy/kubernetes/manifests/ui/deployment.yaml"
  kubectl apply -f "$ROOT_DIR/deploy/kubernetes/manifests/ui/service.yaml"
}

# Deploy a specific agent
function deploy_agent {
  AGENT=$1
  if [ -d "$ROOT_DIR/deploy/kubernetes/manifests/agents/$AGENT" ]; then
    echo "🚀 Deploying agent: $AGENT"
    kubectl apply -f "$ROOT_DIR/deploy/kubernetes/manifests/agents/$AGENT/deployment.yaml"
    kubectl apply -f "$ROOT_DIR/deploy/kubernetes/manifests/agents/$AGENT/service.yaml"
  else
    echo "⚠️ Agent $AGENT not found in manifests directory"
  fi
}

# Check for secret file
if [ ! -f "$ROOT_DIR/deploy/kubernetes/manifests/common/secret.yaml" ]; then
  echo "⚠️ Secret file not found. Please create it from the template:"
  echo "cp $ROOT_DIR/deploy/kubernetes/manifests/common/secret.yaml.template $ROOT_DIR/deploy/kubernetes/manifests/common/secret.yaml"
  echo "Then edit the file to include your API keys."
  exit 1
fi

# Main script logic
case "$1" in
  "ui")
    deploy_ui
    ;;
  "all")
    deploy_ui
    for AGENT_DIR in "$ROOT_DIR"/deploy/kubernetes/manifests/agents/*/; do
      AGENT=$(basename "$AGENT_DIR")
      deploy_agent "$AGENT"
    done
    ;;
  "")
    print_usage
    ;;
  *)
    deploy_agent "$1"
    ;;
esac

echo "✅ Deployment completed"
echo "To access the UI, run:"
echo "kubectl port-forward svc/a2a-ui 12000:12000"
echo "Then visit http://localhost:12000 in your browser"