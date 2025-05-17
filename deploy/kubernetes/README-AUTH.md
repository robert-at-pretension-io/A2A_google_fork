# HTTPS and Authentication Setup

This guide explains how to enable HTTPS and authentication for the A2A system.

## Prerequisites

1. Create a Google OAuth client:
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create a new project (or use existing)
   - Navigate to API & Services > Credentials
   - Create OAuth client ID (Web application type)
   - Add authorized redirect URI: `https://a2a.example.com/oauth2/callback`
   - Note the Client ID and Client Secret

2. Install cert-manager in your cluster:
   ```bash
   kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.12.0/cert-manager.yaml
   ```

3. Configure a ClusterIssuer for Let's Encrypt:
   ```bash
   kubectl apply -f - <<EOF
   apiVersion: cert-manager.io/v1
   kind: ClusterIssuer
   metadata:
     name: letsencrypt-prod
   spec:
     acme:
       email: your-email@example.com
       server: https://acme-v02.api.letsencrypt.org/directory
       privateKeySecretRef:
         name: letsencrypt-prod
       solvers:
       - http01:
           ingress:
             class: nginx
   EOF
   ```

## Setup Instructions

1. Update the OAuth2 proxy secret with your credentials:
   ```bash
   # Generate a random cookie secret
   COOKIE_SECRET=$(openssl rand -base64 32 | tr -- '+/' '-_')
   
   # Update the secret file with your values
   sed -i "s/replace-with-32-byte-random-string/$COOKIE_SECRET/" deploy/kubernetes/manifests/common/oauth2-proxy-secret.yaml
   sed -i "s/replace-with-oauth-client-id/your-client-id/" deploy/kubernetes/manifests/common/oauth2-proxy-secret.yaml
   sed -i "s/replace-with-oauth-client-secret/your-client-secret/" deploy/kubernetes/manifests/common/oauth2-proxy-secret.yaml
   ```

2. Update your domain in the ingress configuration:
   ```bash
   # Replace example.com with your domain
   sed -i "s/a2a.example.com/your-actual-domain.com/" deploy/kubernetes/kustomize/overlays/prod/ingress-with-auth.yaml
   ```

3. Deploy with authentication enabled:
   ```bash
   kubectl apply -k deploy/kubernetes/kustomize/overlays/prod
   ```

## How it works

1. **HTTPS**: cert-manager automatically obtains and renews TLS certificates from Let's Encrypt.

2. **Authentication**: When a user accesses the site:
   - The Nginx ingress controller checks with oauth2-proxy if the user is authenticated
   - If not, they're redirected to Google login
   - After successful login, oauth2-proxy sets a secure cookie and redirects back to the application
   - All subsequent requests include this cookie, allowing access

3. **Security**: This setup ensures:
   - All traffic is encrypted via HTTPS
   - Only authenticated users can access the application
   - Session cookies are secure and HTTP-only

## Customizing Authentication

To restrict access to specific email domains:
```bash
# Modify oauth2-proxy.yaml, changing:
- --email-domain=*
# To specific domains:
- --email-domain=yourdomain.com
- --email-domain=anotherdomain.org
```