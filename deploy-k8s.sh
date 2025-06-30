#!/bin/bash

# Simple Kubernetes deployment script for Helm Aware
# Applies manifests individually without kustomize

set -e

echo "🚀 Deploying Helm Aware to Kubernetes..."

# Create namespace
echo "📦 Creating namespace..."
kubectl apply -f k8s/namespace.yaml

# Apply RBAC
echo "🔐 Applying RBAC..."
kubectl apply -f k8s/service-account.yaml

# Apply configuration
echo "⚙️  Applying configuration..."
kubectl apply -f k8s/configmap.yaml

# Apply deployment
echo "🚀 Applying deployment..."
kubectl apply -f k8s/deployment.yaml

# Apply service
echo "🌐 Applying service..."
kubectl apply -f k8s/service.yaml

# Apply ingress (optional)
echo "🔗 Applying ingress..."
kubectl apply -f k8s/ingress.yaml

echo "✅ Deployment complete!"
echo ""
echo "📊 To check status:"
echo "   kubectl get pods -n helm-aware"
echo ""
echo "🔍 To view logs:"
echo "   kubectl logs -n helm-aware deployment/helm-aware -f"
echo ""
echo "🌐 To access the application:"
echo "   kubectl port-forward -n helm-aware svc/helm-aware 8080:80"
echo "   Then open http://localhost:8080" 