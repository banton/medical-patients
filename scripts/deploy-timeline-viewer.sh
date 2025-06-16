#!/bin/bash
# Deploy Timeline Viewer to DigitalOcean App Platform

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

echo "🚀 Timeline Viewer Deployment Script"
echo "===================================="
echo ""

# Check if doctl is installed
if ! command -v doctl &> /dev/null; then
    print_error "doctl CLI is not installed!"
    echo "Install it from: https://docs.digitalocean.com/reference/doctl/how-to/install/"
    exit 1
fi

# Check if authenticated
if ! doctl auth list &> /dev/null; then
    print_error "Not authenticated with DigitalOcean!"
    echo "Run: doctl auth init"
    exit 1
fi

# Parse arguments
DEPLOY_METHOD="app-platform"  # Default to App Platform
if [[ "$1" == "--droplet" ]]; then
    DEPLOY_METHOD="droplet"
fi

if [[ "$DEPLOY_METHOD" == "app-platform" ]]; then
    print_info "Deploying to DigitalOcean App Platform..."
    
    # Check if app already exists
    APP_ID=$(doctl apps list --format ID,Spec.Name --no-header | grep "medical-timeline-viewer" | awk '{print $1}' || true)
    
    if [ -z "$APP_ID" ]; then
        print_step "Creating new app..."
        doctl apps create --spec timeline-viewer-app-spec.yaml
    else
        print_step "Updating existing app (ID: $APP_ID)..."
        doctl apps update $APP_ID --spec timeline-viewer-app-spec.yaml
    fi
    
    print_info "Deployment initiated!"
    echo ""
    echo "📋 Next steps:"
    echo "1. Monitor deployment: doctl apps list"
    echo "2. View logs: doctl apps logs medical-timeline-viewer"
    echo "3. Access at: https://viewer.milmed.tech (after DNS propagation)"
    
else
    # Droplet deployment option
    print_info "Building Docker image for Droplet deployment..."
    
    print_step "Building production image..."
    cd patient-timeline-viewer
    docker build -f Dockerfile.prod -t timeline-viewer:latest .
    
    print_step "Tagging for registry..."
    # Assumes you have a DigitalOcean Container Registry
    REGISTRY_URL="registry.digitalocean.com/your-registry-name"
    docker tag timeline-viewer:latest $REGISTRY_URL/timeline-viewer:latest
    
    print_step "Pushing to registry..."
    docker push $REGISTRY_URL/timeline-viewer:latest
    
    print_info "Docker image pushed!"
    echo ""
    echo "📋 To deploy on a Droplet:"
    echo "1. SSH into your Droplet"
    echo "2. Pull the image: docker pull $REGISTRY_URL/timeline-viewer:latest"
    echo "3. Run: docker run -d -p 80:80 --name timeline-viewer $REGISTRY_URL/timeline-viewer:latest"
    echo "4. Configure nginx/caddy to proxy viewer.milmed.tech to the container"
fi

echo ""
print_info "Deployment script completed!"