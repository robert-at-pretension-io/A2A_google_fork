# Kubernetes Deployment Guide for A2A Online

This guide provides step-by-step instructions for deploying A2A agents in a Kubernetes cluster online, covering both managed Kubernetes services and self-hosted options.

## Option 1: Using a Managed Kubernetes Service (Easiest)

### Google Kubernetes Engine (GKE)
```bash
# 1. Create a GKE cluster
gcloud container clusters create a2a-cluster \
  --num-nodes=3 \
  --zone=us-central1-a \
  --machine-type=e2-standard-2

# 2. Get credentials
gcloud container clusters get-credentials a2a-cluster --zone=us-central1-a
```

### Amazon EKS
```bash
# 1. Create an EKS cluster
eksctl create cluster --name a2a-cluster --nodes 3
```

### Digital Ocean Kubernetes
```bash
# 1. Create cluster via DO Console or CLI
doctl kubernetes cluster create a2a-cluster --count 3 --size s-2vcpu-4gb
```

## Option 2: Single VPS with K3s (Most Cost-Effective)

### 1. Provision a VPS
- Get a VPS with at least 4GB RAM (DigitalOcean, Linode, Vultr, etc.)
- Ubuntu 20.04 or newer

### 2. Install K3s
```bash
# SSH into your server
ssh root@your-server-ip

# Install K3s
curl -sfL https://get.k3s.io | sh -

# Check installation
kubectl get nodes
```

### 3. Configure kubectl locally
```bash
# On your local machine
scp root@your-server-ip:/etc/rancher/k3s/k3s.yaml ~/.kube/config
sed -i 's/127.0.0.1/your-server-ip/g' ~/.kube/config
```

## Deploy A2A to Your Kubernetes Cluster

### 1. Clone the repository
```bash
git clone https://github.com/google/a2a.git
cd a2a
```

### 2. Build and push images to a registry

#### Option A: Docker Hub
```bash
# Login to Docker Hub
docker login

# Build and push images
cd deploy/kubernetes/scripts
./build.sh

# Tag and push to Docker Hub
docker tag a2a-ui:latest yourusername/a2a-ui:latest
docker tag a2a-agent-google-adk:latest yourusername/a2a-agent-google-adk:latest
docker tag a2a-agent-repo-cloner:latest yourusername/a2a-agent-repo-cloner:latest

docker push yourusername/a2a-ui:latest
docker push yourusername/a2a-agent-google-adk:latest
docker push yourusername/a2a-agent-repo-cloner:latest
```

#### Option B: Use Google Container Registry (for GKE)
```bash
# Configure Docker for GCR
gcloud auth configure-docker

# Tag and push
docker tag a2a-ui:latest gcr.io/your-project/a2a-ui:latest
docker push gcr.io/your-project/a2a-ui:latest
```

### 3. Update Kubernetes manifests
```bash
# Update image references in deployment files
cd deploy/kubernetes/manifests

# Edit each deployment.yaml to use your registry
nano ui/deployment.yaml
# Change image: a2a-ui:latest to image: yourusername/a2a-ui:latest
```

### 4. Create namespace and deploy
```bash
# Create namespace
kubectl create namespace a2a

# Deploy secrets
cd deploy/kubernetes/scripts
./setup-secret.sh

# Deploy everything
kubectl apply -f ../manifests/common/ -n a2a
kubectl apply -f ../manifests/ui/ -n a2a
kubectl apply -f ../manifests/agents/repo_cloner/ -n a2a
```

### 5. Expose services to the internet

#### Option A: LoadBalancer (for cloud providers)
```bash
# Edit service type
kubectl edit svc a2a-ui -n a2a
# Change type: ClusterIP to type: LoadBalancer
```

#### Option B: Ingress with cert-manager (recommended)
```bash
# Install ingress controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml

# Install cert-manager for SSL
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
```

Create an ingress file `ingress.yaml`:
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: a2a-ingress
  namespace: a2a
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/proxy-body-size: 50m
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - a2a.yourdomain.com
    secretName: a2a-tls
  rules:
  - host: a2a.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: a2a-ui
            port:
              number: 12000
      - path: /api/repo-cloner
        pathType: Prefix
        backend:
          service:
            name: a2a-agent-repo-cloner
            port:
              number: 10003
```

Create cert issuer `issuer.yaml`:
```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
```

Apply:
```bash
kubectl apply -f issuer.yaml
kubectl apply -f ingress.yaml
```

#### Option C: NodePort (for single VPS)
```bash
# Edit services to use NodePort
kubectl edit svc a2a-ui -n a2a
# Change type: ClusterIP to type: NodePort
# Note the port (e.g., 32000)

# Access via http://your-server-ip:32000
```

### 6. Configure DNS
Point your domain to:
- LoadBalancer IP (if using LoadBalancer)
- Ingress controller IP (if using Ingress)
- Your VPS IP (if using NodePort)

## Quick Deployment Script

Create `deploy-online.sh`:
```bash
#!/bin/bash

# Set your Docker Hub username
DOCKER_USER="yourusername"
DOMAIN="a2a.yourdomain.com"

# Build images
cd deploy/kubernetes/scripts
./build.sh

# Push to registry
for img in ui agent-google-adk agent-repo-cloner; do
  docker tag a2a-$img:latest $DOCKER_USER/a2a-$img:latest
  docker push $DOCKER_USER/a2a-$img:latest
done

# Update manifests with your images
cd ../manifests
find . -name "*.yaml" -exec sed -i "s|image: a2a-|image: $DOCKER_USER/a2a-|g" {} \;

# Deploy
kubectl create namespace a2a
kubectl apply -f common/ -n a2a
kubectl apply -f ui/ -n a2a
kubectl apply -f agents/repo_cloner/ -n a2a

echo "Deployment complete!"
echo "Check status: kubectl get all -n a2a"
```

## Monitoring and Management

```bash
# Check status
kubectl get all -n a2a

# View logs
kubectl logs -n a2a deployment/a2a-ui
kubectl logs -n a2a deployment/a2a-agent-repo-cloner

# Scale deployments
kubectl scale -n a2a deployment/a2a-ui --replicas=3

# Update deployment
kubectl set image -n a2a deployment/a2a-ui ui=$DOCKER_USER/a2a-ui:v2
```

## Security Considerations

1. **Network Policies**: Restrict traffic between pods
2. **RBAC**: Set up proper role-based access control
3. **Secrets**: Use Kubernetes secrets for API keys
4. **Pod Security**: Use security contexts and policies
5. **Regular Updates**: Keep cluster and images updated

## Cost Optimization Tips

### For Production
- Use spot/preemptible instances for non-critical workloads
- Configure horizontal pod autoscaling (HPA)
- Use persistent volumes efficiently
- Monitor resource usage and right-size pods

### For Development/Testing
- K3s on a single VPS is very cost-effective
- Use services like DigitalOcean's $12/month droplets
- Scale down to zero when not in use

## Troubleshooting

### Common Issues

1. **Image Pull Errors**
   - Ensure images are pushed to registry
   - Check image names match in manifests
   - Verify registry credentials

2. **Service Connection Issues**
   - Check service names and ports
   - Verify network policies
   - Test with port-forwarding first

3. **SSL Certificate Issues**
   - Ensure DNS is properly configured
   - Check cert-manager logs
   - Verify ingress annotations

### Debug Commands
```bash
# Describe pod for errors
kubectl describe pod -n a2a <pod-name>

# Check events
kubectl get events -n a2a --sort-by='.lastTimestamp'

# Test connectivity
kubectl run -it --rm debug --image=busybox -n a2a -- sh
```

## Next Steps

1. Set up CI/CD pipeline for automated deployments
2. Configure monitoring with Prometheus/Grafana
3. Implement backup strategies for persistent data
4. Set up alerting for critical issues
5. Document your specific deployment configuration