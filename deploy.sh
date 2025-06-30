#!/bin/bash

# Helm Aware Deployment Script
# This script builds and deploys the Helm Aware application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required tools are installed
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed. Please install kubectl first."
        exit 1
    fi
    
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Cannot connect to Kubernetes cluster. Please check your kubectl configuration."
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Build Docker image
build_image() {
    print_status "Building Docker image..."
    
    if docker build -t helm-aware:latest .; then
        print_success "Docker image built successfully"
    else
        print_error "Failed to build Docker image"
        exit 1
    fi
}

# Deploy to Kubernetes
deploy_to_k8s() {
    print_status "Deploying to Kubernetes..."
    
    # Create namespace if it doesn't exist
    if ! kubectl get namespace helm-aware &> /dev/null; then
        print_status "Creating helm-aware namespace..."
        kubectl apply -f k8s/namespace.yaml
    fi
    
    # Apply all manifests
    if kubectl apply -k k8s/; then
        print_success "Kubernetes deployment successful"
    else
        print_error "Failed to deploy to Kubernetes"
        exit 1
    fi
}

# Wait for deployment to be ready
wait_for_deployment() {
    print_status "Waiting for deployment to be ready..."
    
    kubectl wait --for=condition=available --timeout=300s deployment/helm-aware -n helm-aware
    
    if [ $? -eq 0 ]; then
        print_success "Deployment is ready"
    else
        print_error "Deployment failed to become ready"
        exit 1
    fi
}

# Show deployment status
show_status() {
    print_status "Deployment status:"
    echo
    kubectl get pods -n helm-aware
    echo
    kubectl get svc -n helm-aware
    echo
    kubectl get ingress -n helm-aware
}

# Show access instructions
show_access_instructions() {
    print_success "Deployment completed successfully!"
    echo
    print_status "To access the application:"
    echo "1. Port forward the service:"
    echo "   kubectl port-forward -n helm-aware svc/helm-aware 8080:80"
    echo
    echo "2. Open your browser and navigate to:"
    echo "   http://localhost:8080"
    echo
    print_status "To view logs:"
    echo "   kubectl logs -n helm-aware deployment/helm-aware -f"
    echo
    print_status "To check status:"
    echo "   kubectl get pods -n helm-aware"
}

# Main deployment function
main() {
    echo "🚀 Helm Aware Deployment Script"
    echo "================================"
    echo
    
    check_prerequisites
    build_image
    deploy_to_k8s
    wait_for_deployment
    show_status
    show_access_instructions
}

# Handle command line arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "undeploy")
        print_status "Undeploying Helm Aware..."
        kubectl delete -k k8s/ || true
        print_success "Undeployment completed"
        ;;
    "status")
        show_status
        ;;
    "logs")
        print_status "Showing application logs..."
        kubectl logs -n helm-aware deployment/helm-aware -f
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [command]"
        echo
        echo "Commands:"
        echo "  deploy   - Build and deploy the application (default)"
        echo "  undeploy - Remove the application from Kubernetes"
        echo "  status   - Show deployment status"
        echo "  logs     - Show application logs"
        echo "  help     - Show this help message"
        ;;
    *)
        print_error "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac 