#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Medical Patients Staging Deployment ===${NC}"
echo -e "${GREEN}Deploying to same server on port 8001${NC}"
echo ""

# Check if we're on the staging branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "feature/v1.1-consolidated" ]; then
    echo -e "${YELLOW}Warning: Not on feature/v1.1-consolidated branch${NC}"
    echo -e "${YELLOW}Current branch: $CURRENT_BRANCH${NC}"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 1: Setup staging database
echo -e "${YELLOW}Step 1: Setting up staging database${NC}"
echo "Connect to PostgreSQL and run:"
echo "psql postgresql://doadmin:YOUR_ADMIN_PASSWORD@app-7a761f5d-a598-4efc-9f1a-cd756365d498-do-user-323970-0.m.db.ondigitalocean.com:25060/defaultdb?sslmode=require"
echo ""
echo "CREATE DATABASE medgen_staging;"
echo "CREATE USER staging_user WITH ENCRYPTED PASSWORD 'your-secure-password';"
echo "GRANT ALL PRIVILEGES ON DATABASE medgen_staging TO staging_user;"
echo "\\c medgen_staging"
echo "GRANT ALL ON SCHEMA public TO staging_user;"
echo ""
read -p "Have you created the database? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}Please create the database first${NC}"
    exit 1
fi

# Step 2: Set environment variables
echo -e "${YELLOW}Step 2: Setting environment variables${NC}"
if [ ! -f .env.staging ]; then
    echo "Creating .env.staging file..."
    cat > .env.staging << EOF
# Staging Environment Variables
STAGING_DB_PASSWORD=your-secure-password
STAGING_API_KEY=staging-$(openssl rand -hex 32)
STAGING_SECRET_KEY=staging-secret-$(openssl rand -hex 16)
EOF
    echo -e "${GREEN}Created .env.staging - Please update the database password!${NC}"
    exit 1
fi

# Load staging environment
set -a
source .env.staging
set +a

# Step 3: Build and start staging container
echo -e "${YELLOW}Step 3: Building and starting staging container${NC}"
docker compose -f docker-compose.staging.yml build
docker compose -f docker-compose.staging.yml up -d

# Wait for container to be healthy
echo -e "${YELLOW}Waiting for staging to be healthy...${NC}"
for i in {1..30}; do
    if docker exec medical-patients-staging curl -f http://localhost:8000/api/v1/health > /dev/null 2>&1; then
        echo -e "${GREEN}Staging API is healthy!${NC}"
        break
    fi
    echo -n "."
    sleep 2
done

# Step 4: Setup nginx configuration
echo -e "${YELLOW}Step 4: Setting up nginx configuration${NC}"
sudo tee /etc/nginx/sites-available/staging.milmed.tech << 'EOF'
server {
    listen 80;
    server_name staging.milmed.tech;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 301 https://$server_name$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name staging.milmed.tech;
    
    ssl_certificate /etc/letsencrypt/live/staging.milmed.tech/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/staging.milmed.tech/privkey.pem;
    
    location / {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name timeline.milmed.tech;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 301 https://$server_name$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name timeline.milmed.tech;
    
    ssl_certificate /etc/letsencrypt/live/timeline.milmed.tech/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/timeline.milmed.tech/privkey.pem;
    
    location / {
        proxy_pass http://localhost:3001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Step 5: Get SSL certificates
echo -e "${YELLOW}Step 5: Getting SSL certificates${NC}"
sudo certbot certonly --nginx -d staging.milmed.tech -d timeline.milmed.tech

# Enable sites
sudo ln -sf /etc/nginx/sites-available/staging.milmed.tech /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# Step 6: Configure DNS
echo -e "${YELLOW}Step 6: Configure DNS (manual step)${NC}"
echo "Add these DNS records to DigitalOcean:"
echo ""
echo "1. A record: staging.milmed.tech -> $(curl -s https://ifconfig.me)"
echo "2. A record: timeline.milmed.tech -> $(curl -s https://ifconfig.me)"
echo ""

# Final status
echo -e "${GREEN}=== Deployment Complete ===${NC}"
echo ""
echo "Staging API: https://staging.milmed.tech/api/v1/health"
echo "Staging Docs: https://staging.milmed.tech/docs"
echo "Timeline Viewer: https://timeline.milmed.tech"
echo ""
echo "Container status:"
docker ps | grep -E "(medical-patients-staging|timeline-viewer-staging)"