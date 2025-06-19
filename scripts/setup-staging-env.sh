#!/bin/bash

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Setting up staging environment configuration${NC}"

# Check if .env.staging already exists
if [ -f .env.staging ]; then
    echo -e "${YELLOW}Warning: .env.staging already exists${NC}"
    read -p "Overwrite? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi

# Generate secure values
STAGING_API_KEY=$(openssl rand -hex 32)
STAGING_SECRET_KEY=$(openssl rand -hex 16)

# Create .env.staging
cat > .env.staging << EOF
# Staging Environment Variables
# Generated on $(date)

# Database password - UPDATE THIS after creating the staging database
STAGING_DB_PASSWORD=CHANGE_ME_TO_ACTUAL_PASSWORD

# API Key for staging environment
STAGING_API_KEY=${STAGING_API_KEY}

# Secret key for staging
STAGING_SECRET_KEY=${STAGING_SECRET_KEY}

# Optional: Override other settings
# CORS_ORIGINS=https://staging.milmed.tech,https://timeline.milmed.tech
# DEBUG=false
# CACHE_ENABLED=true
EOF

# Secure the file
chmod 600 .env.staging

echo -e "${GREEN}✅ Created .env.staging${NC}"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT: You must update STAGING_DB_PASSWORD after creating the database${NC}"
echo ""
echo "Next steps:"
echo "1. Connect to PostgreSQL and create staging database:"
echo "   psql \$PRODUCTION_DATABASE_URL"
echo "   CREATE DATABASE medgen_staging;"
echo "   CREATE USER staging_user WITH ENCRYPTED PASSWORD 'your-secure-password';"
echo "   GRANT ALL PRIVILEGES ON DATABASE medgen_staging TO staging_user;"
echo ""
echo "2. Update STAGING_DB_PASSWORD in .env.staging"
echo ""
echo "3. Start staging with: task staging:up"