.PHONY: help build run test clean deploy undeploy logs

# Default target
help:
	@echo "Helm Aware - Available commands:"
	@echo "  build     - Build Docker image"
	@echo "  run       - Run application locally"
	@echo "  test      - Run tests (placeholder)"
	@echo "  clean     - Clean up build artifacts"
	@echo "  deploy    - Deploy to Kubernetes"
	@echo "  undeploy  - Remove from Kubernetes"
	@echo "  logs      - View application logs"

# Build Docker image
build:
	@echo "Building Docker image..."
	docker build -t helm-aware:latest .

# Run application locally
run:
	@echo "Running application locally..."
	python app/run.py

# Run tests (placeholder for future test implementation)
test:
	@echo "Running tests..."
	@echo "Tests not implemented yet"

# Clean up build artifacts
clean:
	@echo "Cleaning up..."
	docker rmi helm-aware:latest 2>/dev/null || true
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true

# Deploy to Kubernetes
deploy:
	@echo "Deploying to Kubernetes..."
	kubectl apply -k k8s/
	@echo "Deployment complete!"
	@echo "To access the application:"
	@echo "  kubectl port-forward -n helm-aware svc/helm-aware 8080:80"
	@echo "  Then open http://localhost:8080"

# Remove from Kubernetes
undeploy:
	@echo "Removing from Kubernetes..."
	kubectl delete -k k8s/
	@echo "Undeployment complete!"

# View application logs
logs:
	@echo "Viewing application logs..."
	kubectl logs -n helm-aware deployment/helm-aware -f

# Check application status
status:
	@echo "Checking application status..."
	kubectl get pods -n helm-aware
	kubectl get svc -n helm-aware
	kubectl get ingress -n helm-aware

# Install dependencies
install:
	@echo "Installing Python dependencies..."
	pip install -r requirements.txt

# Format code
format:
	@echo "Formatting code..."
	black app/
	flake8 app/

# Lint code
lint:
	@echo "Linting code..."
	flake8 app/
	pylint app/ 