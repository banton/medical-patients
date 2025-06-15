# Staging Deployment Guide - Same Server Approach

## Overview
Deploy staging environment on the same DigitalOcean droplet as production, using different ports and subdomains.

## Architecture
- **Production**: Port 8000 → milmed.tech
- **Staging API**: Port 8001 → staging.milmed.tech  
- **Timeline Viewer**: Port 3001 → timeline.milmed.tech
- **Database**: Shared managed PostgreSQL cluster with separate databases
- **Redis**: Shared instance using different database numbers (0=prod, 1=staging)

## Prerequisites
1. SSH access to the DigitalOcean droplet
2. Access to managed PostgreSQL cluster
3. DNS management access for milmed.tech domain

## Step-by-Step Deployment

### 1. Prepare the Server
```bash
# SSH into the server
ssh root@milmed.tech

# Clone or update the repository
cd /opt/medical-patients
git fetch origin
git checkout feature/v1.1-consolidated
git pull origin feature/v1.1-consolidated
```

### 2. Create Staging Database
```bash
# Connect to PostgreSQL cluster
psql postgresql://doadmin:YOUR_PASSWORD@app-7a761f5d-a598-4efc-9f1a-cd756365d498-do-user-323970-0.m.db.ondigitalocean.com:25060/defaultdb?sslmode=require

# Create staging database and user
CREATE DATABASE medgen_staging;
CREATE USER staging_user WITH ENCRYPTED PASSWORD 'generate-secure-password-here';
GRANT ALL PRIVILEGES ON DATABASE medgen_staging TO staging_user;
\c medgen_staging
GRANT ALL ON SCHEMA public TO staging_user;
\q
```

### 3. Configure Environment
```bash
# Create staging environment file
cat > .env.staging << EOF
STAGING_DB_PASSWORD=your-secure-password-from-step-2
STAGING_API_KEY=$(openssl rand -hex 32)
STAGING_SECRET_KEY=$(openssl rand -hex 16)
EOF

# Secure the file
chmod 600 .env.staging
```

### 4. Deploy Staging Containers
```bash
# Load environment variables
source .env.staging

# Build and start staging
docker compose -f docker-compose.staging.yml up -d --build

# Check status
docker ps | grep staging
docker logs medical-patients-staging --tail 50
```

### 5. Configure Nginx
```bash
# Create nginx configuration
sudo tee /etc/nginx/sites-available/staging.milmed.tech << 'EOF'
server {
    listen 80;
    server_name staging.milmed.tech;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name staging.milmed.tech;
    
    # SSL will be configured by certbot
    
    location / {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF

# Timeline viewer configuration
sudo tee /etc/nginx/sites-available/timeline.milmed.tech << 'EOF'
server {
    listen 80;
    server_name timeline.milmed.tech;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name timeline.milmed.tech;
    
    # SSL will be configured by certbot
    
    location / {
        proxy_pass http://localhost:3001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Enable sites
sudo ln -sf /etc/nginx/sites-available/staging.milmed.tech /etc/nginx/sites-enabled/
sudo ln -sf /etc/nginx/sites-available/timeline.milmed.tech /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t
```

### 6. Configure DNS
Add these A records in DigitalOcean DNS:
```
staging.milmed.tech → [droplet-ip]
timeline.milmed.tech → [droplet-ip]
```

### 7. Setup SSL Certificates
```bash
# Get certificates for both subdomains
sudo certbot --nginx -d staging.milmed.tech -d timeline.milmed.tech

# Reload nginx
sudo systemctl reload nginx
```

### 8. Build Timeline Viewer
```bash
# Create timeline viewer Dockerfile if not exists
cat > patient-timeline-viewer/Dockerfile << 'EOF'
FROM node:18-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
EOF

# Build and run timeline viewer
docker build -t timeline-viewer-staging ./patient-timeline-viewer
docker run -d --name timeline-viewer-staging -p 3001:80 timeline-viewer-staging
```

## Verification

### Check Services
```bash
# API Health
curl https://staging.milmed.tech/api/v1/health

# Documentation
curl https://staging.milmed.tech/docs

# Timeline Viewer
curl https://timeline.milmed.tech
```

### Monitor Logs
```bash
# Staging API logs
docker logs -f medical-patients-staging

# Timeline viewer logs  
docker logs -f timeline-viewer-staging

# Nginx logs
sudo tail -f /var/log/nginx/error.log
```

## Maintenance

### Update Staging
```bash
cd /opt/medical-patients
git pull origin feature/v1.1-consolidated
docker compose -f docker-compose.staging.yml up -d --build
```

### View Staging Database
```bash
psql postgresql://staging_user:password@app-7a761f5d-a598-4efc-9f1a-cd756365d498-do-user-323970-0.m.db.ondigitalocean.com:25060/medgen_staging?sslmode=require
```

### Stop Staging
```bash
docker compose -f docker-compose.staging.yml down
```

## Troubleshooting

### Port Conflicts
```bash
# Check what's using ports
sudo netstat -tlnp | grep -E "(8001|3001)"
```

### Database Connection Issues
```bash
# Test connection from container
docker exec medical-patients-staging psql $DATABASE_URL -c "SELECT 1"
```

### Container Won't Start
```bash
# Check logs
docker logs medical-patients-staging

# Check environment
docker exec medical-patients-staging env | grep -E "(DATABASE|REDIS|API)"
```

## Cost Summary
- **Additional Server Cost**: $0 (using same droplet)
- **Database Cost**: $0 (using same managed cluster)
- **Domain Cost**: $0 (subdomains of existing domain)
- **Total Additional Cost**: $0/month

## Security Notes
1. Staging uses separate database with its own credentials
2. Staging API key is different from production
3. Redis databases are isolated (0=prod, 1=staging)
4. SSL certificates protect both subdomains
5. Firewall rules apply to both production and staging