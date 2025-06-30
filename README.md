# Helm Aware - ArgoCD Chart Analysis Dashboard

A modern Flask-based web application that analyzes ArgoCD Applications and ApplicationSets to identify Helm charts and compare their versions with available updates.

## Features

- 🔍 **ArgoCD Integration**: Automatically discovers and analyzes ArgoCD Applications and ApplicationSets
- 📊 **Helm Chart Detection**: Identifies Helm charts from various repository types (HTTP, OCI)
- 🔄 **Version Comparison**: Compares installed versions with available versions from remote repositories
- 🎨 **Modern UI**: Beautiful, responsive single-page application with real-time updates
- 📈 **Statistics Dashboard**: Overview of applications, charts, and available updates
- 🔐 **Kubernetes Native**: Runs as a Kubernetes deployment with proper RBAC

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Browser   │    │   Flask App      │    │   Kubernetes    │
│                 │◄──►│   (Port 5000)    │◄──►│   API Server    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   Helm CLI       │
                       │   (OCI/HTTP)     │
                       └──────────────────┘
```

## Quick Start

### Prerequisites

- Kubernetes cluster with ArgoCD installed
- `kubectl` configured to access your cluster
- `docker` for building the container image

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd helm-aware
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application locally**
   ```bash
   python app/run.py
   ```

4. **Access the dashboard**
   Open your browser and navigate to `http://localhost:5000`

### Docker Deployment

1. **Build the Docker image**
   ```bash
   docker build -t helm-aware:latest .
   ```

2. **Deploy to Kubernetes**
   ```bash
   # Apply all Kubernetes manifests
   kubectl apply -k k8s/
   
   # Or apply individually
   kubectl apply -f k8s/namespace.yaml
   kubectl apply -f k8s/configmap.yaml
   kubectl apply -f k8s/service-account.yaml
   kubectl apply -f k8s/deployment.yaml
   kubectl apply -f k8s/service.yaml
   kubectl apply -f k8s/ingress.yaml
   ```

3. **Access the application**
   ```bash
   # Port forward to access locally
   kubectl port-forward -n helm-aware svc/helm-aware 8080:80
   ```
   
   Then open `http://localhost:8080` in your browser.

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Host to bind the Flask application |
| `PORT` | `5000` | Port to bind the Flask application |
| `DEBUG` | `false` | Enable Flask debug mode |
| `LOG_LEVEL` | `INFO` | Logging level |

### Kubernetes Configuration

The application includes proper RBAC configuration to access ArgoCD CRDs:

- **ClusterRole**: Read access to ArgoCD Applications and ApplicationSets
- **ServiceAccount**: Non-root user with minimal required permissions
- **SecurityContext**: Secure container configuration

## API Endpoints

### GET `/`
Main dashboard page with the single-page application.

### GET `/api/applications`
Returns all ArgoCD Applications and ApplicationSets with Helm chart analysis.

**Response:**
```json
{
  "applications": [
    {
      "metadata": {
        "name": "example-app",
        "namespace": "argocd"
      },
      "helm_charts": [
        {
          "repo_url": "https://charts.bitnami.com/bitnami",
          "chart_name": "nginx",
          "chart_version": "13.2.0",
          "available_versions": ["13.2.1", "13.2.0", "13.1.0"]
        }
      ]
    }
  ],
  "application_sets": [...]
}
```

### POST `/api/chart-versions`
Get available versions for a specific chart.

**Request:**
```json
{
  "repo_url": "https://charts.bitnami.com/bitnami",
  "chart_name": "nginx"
}
```

## Helm Chart Detection

The application automatically detects Helm charts by analyzing:

1. **Chart Field**: Presence of a `chart` field in the source
2. **OCI Protocol**: Sources starting with `oci://`
3. **Version Pattern**: Target revisions matching semantic versioning

### Supported Repository Types

- **HTTP/HTTPS**: Traditional Helm chart repositories
- **OCI**: Open Container Initiative registries
- **Auto-detection**: Assumes OCI for repositories without protocol

## Troubleshooting

### Common Issues

1. **Permission Denied**
   ```bash
   # Check if the service account has proper permissions
   kubectl auth can-i list applications --as=system:serviceaccount:helm-aware:helm-aware
   ```

2. **Helm Command Failures**
   ```bash
   # Check if Helm is available in the container
   kubectl exec -n helm-aware deployment/helm-aware -- helm version
   ```

3. **Network Connectivity**
   ```bash
   # Test connectivity to external repositories
   kubectl exec -n helm-aware deployment/helm-aware -- curl -I https://charts.bitnami.com/bitnami/index.yaml
   ```

### Logs

```bash
# View application logs
kubectl logs -n helm-aware deployment/helm-aware

# Follow logs in real-time
kubectl logs -n helm-aware deployment/helm-aware -f
```

## Development

### Project Structure

```
helm-aware/
├── app/                    # Flask application
│   ├── __init__.py        # App factory
│   ├── routes.py          # API routes
│   ├── run.py             # Entry point
│   ├── services/          # Business logic
│   │   ├── argocd_service.py
│   │   └── helm_service.py
│   └── templates/         # HTML templates
│       └── index.html
├── k8s/                   # Kubernetes manifests
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── service-account.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   └── kustomization.yaml
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container definition
└── README.md             # This file
```

### Adding New Features

1. **New API Endpoint**: Add to `app/routes.py`
2. **New Service**: Create in `app/services/`
3. **UI Changes**: Modify `app/templates/index.html`
4. **K8s Changes**: Update manifests in `k8s/`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- Create an issue in the GitHub repository
- Check the troubleshooting section above
- Review the logs for error details 