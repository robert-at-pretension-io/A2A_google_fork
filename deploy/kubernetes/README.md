# A2A Kubernetes Deployment

This directory contains the Kubernetes manifests and scripts for deploying the A2A demo application and its agents in a Kubernetes cluster.

> **Related Documentation**:
> - [Main A2A Protocol Documentation](https://google.github.io/A2A/)
> - [Main Project README](/README.md)
> - [Local Docker Deployment](/deploy/local/README.md)
> - [Sample Agents Documentation](/samples/python/agents/README.md)

## Overview

The deployment consists of:

1. **UI Pod** - The web interface that users interact with
2. **Agent Pods** - Various A2A agents that can be used with the UI
3. **Shared Configuration** - ConfigMap and Secrets for application settings

## Getting Started

### Prerequisites

- Docker installed locally
- A Kubernetes cluster (can be local like Minikube, k3s, or Docker Desktop)
- `kubectl` configured to connect to your cluster
- If using Vertex AI agents: Google Cloud authentication set up (`gcloud auth login`)

### Quick Start

1. **Build the Docker images:**

   ```bash
   # Make scripts executable
   chmod +x deploy/kubernetes/scripts/*.sh
   
   # Build images
   ./deploy/kubernetes/scripts/build.sh
   ```

2. **Setup your secrets:**

   ```bash
   ./deploy/kubernetes/scripts/setup-secret.sh
   ```

3. **Deploy the UI and agents:**

   ```bash
   # Deploy just the UI
   ./deploy/kubernetes/scripts/deploy.sh ui
   
   # Deploy a specific agent
   ./deploy/kubernetes/scripts/deploy.sh google_adk
   
   # Deploy the Vertex image generation agent
   ./deploy/kubernetes/scripts/deploy.sh vertex_image_gen
   
   # Deploy UI and all available agents
   ./deploy/kubernetes/scripts/deploy.sh all
   ```

4. **Access the UI:**

   ```bash
   kubectl port-forward svc/a2a-ui 12000:12000
   ```

   Then visit http://localhost:12000 in your browser.

## Available Agents

| Agent | Port | Special Requirements | Description |
|-------|------|----------------------|-------------|
| google_adk | 10002 | Google API Key | Basic reimbursement agent |
| elevenlabs_tts | 10005 | ElevenLabs API Key | Text-to-speech agent |
| vertex_image_gen | 10006 | Vertex AI, GCP Project | Image generation agent |
| repo_cloner | 10003 | Git CLI | Git repository cloning agent |

## Directory Structure

```
kubernetes/
├── README.md                 # This file
├── manifests/
│   ├── common/               # Shared resources
│   │   ├── configmap.yaml    # Shared configuration
│   │   └── secret.yaml       # API keys (generated from template)
│   ├── ui/                   # UI components
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── pvc.yaml
│   └── agents/               # Agent components
│       ├── google_adk/
│       │   ├── deployment.yaml
│       │   └── service.yaml
│       ├── elevenlabs_tts/
│       │   ├── deployment.yaml
│       │   └── service.yaml
│       ├── vertex_image_gen/
│       │   ├── deployment.yaml
│       │   └── service.yaml
│       └── repo_cloner/
│           ├── deployment.yaml
│           └── service.yaml
├── docker/                   # Dockerfiles
│   ├── ui/
│   │   └── Dockerfile
│   └── agent/
│       └── Dockerfile
├── scripts/                  # Helper scripts
│   ├── build.sh              # Build Docker images
│   ├── deploy.sh             # Deploy to Kubernetes
│   └── setup-secret.sh       # Setup secrets
└── kustomize/                # Advanced configurations
    ├── base/                 # Base configurations
    └── overlays/             # Environment-specific overrides
        ├── dev/              # Development environment
        └── prod/             # Production environment
```

## Agent Auto-Registration

By default, the agents are deployed but must be manually registered in the UI. 

To access a deployed agent from the UI:

1. Go to the "Remote Agents" tab in the UI
2. Add the agent using its Kubernetes service name and port:
   - Example: `a2a-agent-google-adk:10002`
   - Example: `a2a-agent-vertex-image-gen:10006`
   - Example: `a2a-agent-repo-cloner:10003`

## Customization

- **Environment Variables**: Edit the `configmap.yaml` to add or modify environment variables
- **Storage Size**: Adjust the storage size in `pvc.yaml` if needed
- **Adding New Agents**: Create new agent manifests by copying the existing ones and updating the name, port, and any specific environment variables

## Using Vertex AI Agents

Vertex AI-based agents require additional configuration:

1. During the `setup-secret.sh` script, answer 'y' to "Use Vertex AI?" and provide your GCP project ID and location.
2. Ensure your Kubernetes cluster has access to Google Cloud (via GKE or properly configured credentials).
3. If running locally, you might need to mount your Google Cloud credentials into the pod.

## Advanced Usage

### Using Persistent Storage

The UI uses a Kubernetes PersistentVolumeClaim for storing conversation history and agent registrations. This ensures data persists across pod restarts.

### Using Kustomize for Different Environments

For development:
```bash
kubectl apply -k deploy/kubernetes/kustomize/overlays/dev/
```

For production:
```bash
kubectl apply -k deploy/kubernetes/kustomize/overlays/prod/
```

### Using an Ingress

To expose the UI outside the cluster, an Ingress configuration is included in the production overlay.

## Troubleshooting

### Common Issues

- **Pod not starting**: Check logs with `kubectl logs -f deployment/a2a-ui`
- **Agent connection issues**: Ensure the agent services are running with `kubectl get svc`
- **UI not loading**: Check if the pod is running with `kubectl get pods`
- **Vertex AI authentication errors**: Verify your Google Cloud credentials are correctly configured in the secret

### Network/Connection Issues

If you encounter connection failures between the UI and agents or see warnings about "non-text parts in the response":

1. **Check Agent Logs**: 
   ```bash
   kubectl logs deployment/a2a-agent-elevenlabs-tts
   ```

2. **Verify Agent Is Listening on 0.0.0.0**:
   Agents must bind to 0.0.0.0 (not localhost) to be accessible from other pods. The Docker container entrypoint should now include the `--host=0.0.0.0` flag.

3. **Validate Port Configuration**:
   Ensure the port numbers in deployment.yaml and service.yaml match what's in the agent's configuration:
   - Google ADK Agent: 10002
   - ElevenLabs TTS Agent: 10005
   - Vertex Image Gen Agent: 10006
   - Git Repository Cloner Agent: 10003

4. **Test the Connection Inside the Cluster**:
   You can run a debug pod to test connectivity:
   ```bash
   kubectl run -it --rm debug --image=curlimages/curl -- sh
   ```
   Then test connectivity:
   ```bash
   curl http://a2a-agent-elevenlabs-tts:10005
   ```

## Local Testing with Docker Compose

For easier local development, see the Docker Compose setup in `deploy/local/`.