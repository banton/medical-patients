#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=== Medical Patients v1.1 Staging Deployment ===${NC}"

# Check if running as root
if [[ $EUID -ne 0 ]]; then 
   echo -e "${RED}This script must be run as root${NC}" 
   exit 1
fi

# Configuration
STAGING_DIR="/opt/medical-patients-staging"
TIMELINE_DIR="/opt/timeline-viewer"
BRANCH="feature/v1.1-consolidated"

echo -e "${YELLOW}Step 1: Creating staging directory...${NC}"
mkdir -p $STAGING_DIR
cd $STAGING_DIR

echo -e "${YELLOW}Step 2: Cloning v1.1 branch...${NC}"
if [ -d ".git" ]; then
    git fetch origin
    git checkout $BRANCH
    git pull origin $BRANCH
else
    git clone -b $BRANCH https://github.com/banton/medical-patients.git .
fi

echo -e "${YELLOW}Step 3: Creating staging database...${NC}"
# Check if staging database exists
DB_EXISTS=$(docker exec medical-patients_db_1 psql -U medgen_user -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='medgen_db_staging'")
if [ "$DB_EXISTS" != "1" ]; then
    docker exec medical-patients_db_1 psql -U medgen_user -d postgres -c "CREATE DATABASE medgen_db_staging;"
    echo "Staging database created"
else
    echo "Staging database already exists"
fi

echo -e "${YELLOW}Step 4: Building staging containers...${NC}"
docker-compose -f docker-compose.staging.yml build

echo -e "${YELLOW}Step 5: Starting staging environment...${NC}"
docker-compose -f docker-compose.staging.yml up -d

echo -e "${YELLOW}Step 6: Waiting for staging to be ready...${NC}"
sleep 10

echo -e "${YELLOW}Step 7: Running database migrations...${NC}"
docker exec medical-patients-staging alembic upgrade head

echo -e "${YELLOW}Step 8: Building Timeline Viewer...${NC}"
mkdir -p $TIMELINE_DIR
cd $STAGING_DIR/patient-timeline-viewer

# Install dependencies and build
npm install
npm run build

# Copy built files
cp -r dist/* $TIMELINE_DIR/
echo "Timeline viewer built and deployed to $TIMELINE_DIR"

echo -e "${YELLOW}Step 9: Setting up Nginx...${NC}"
# Copy nginx configs
cp $STAGING_DIR/nginx/staging.conf /etc/nginx/sites-available/staging.milmed.tech
cp $STAGING_DIR/nginx/timeline.conf /etc/nginx/sites-available/timeline.milmed.tech

# Enable sites
ln -sf /etc/nginx/sites-available/staging.milmed.tech /etc/nginx/sites-enabled/
ln -sf /etc/nginx/sites-available/timeline.milmed.tech /etc/nginx/sites-enabled/

# Test nginx config
nginx -t
if [ $? -eq 0 ]; then
    systemctl reload nginx
    echo -e "${GREEN}Nginx configured successfully${NC}"
else
    echo -e "${RED}Nginx configuration error!${NC}"
    exit 1
fi

echo -e "${YELLOW}Step 10: Running health checks...${NC}"
sleep 5

# Check staging API
STAGING_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/api/v1/health)
if [ "$STAGING_HEALTH" = "200" ]; then
    echo -e "${GREEN}✓ Staging API is healthy${NC}"
else
    echo -e "${RED}✗ Staging API health check failed (HTTP $STAGING_HEALTH)${NC}"
fi

echo -e "${GREEN}=== Deployment Complete ===${NC}"
echo ""
echo "Access your staging sites at:"
echo "- Staging App: https://staging.milmed.tech"
echo "- Timeline Viewer: https://timeline.milmed.tech"
echo ""
echo "To view logs:"
echo "- Staging: docker-compose -f $STAGING_DIR/docker-compose.staging.yml logs -f"
echo ""
echo "To stop staging:"
echo "- docker-compose -f $STAGING_DIR/docker-compose.staging.yml down"