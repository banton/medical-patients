# Staging Deployment Plan for v1.1

## Overview
Deploy v1.1 to a staging environment without disrupting the current production deployment on the main branch.

## Option 1: Same VM with Port Separation (Recommended for Light Staging)

### Advantages:
- Cost-effective (no additional VM)
- Easy to implement
- Sufficient for testing without heavy loads
- Can share database with separate schema

### Implementation:
1. **Deploy staging on different port (8001)**:
   ```bash
   # Create staging directory
   mkdir -p /opt/medical-patients-staging
   cd /opt/medical-patients-staging
   
   # Clone v1.1 branch
   git clone -b feature/v1.1-consolidated https://github.com/banton/medical-patients.git .
   
   # Create staging docker-compose
   cp docker-compose.prod.yml docker-compose.staging.yml
   ```

2. **Modify docker-compose.staging.yml**:
   - Change app port: 8001:8000
   - Use different container names (app-staging, db-staging, redis-staging)
   - Use different database name: medgen_db_staging
   - Use different Redis database: redis://redis-staging:6379/1

3. **Nginx Configuration** for subdomain:
   ```nginx
   # staging.domain.com
   server {
       listen 80;
       server_name staging.milmed.tech;
       
       location / {
           proxy_pass http://localhost:8001;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   
   # timeline.milmed.tech
   server {
       listen 80;
       server_name timeline.milmed.tech;
       
       location / {
           proxy_pass http://localhost:5174;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

## Option 2: Separate VM for Timeline + Staging

### Advantages:
- Complete isolation
- Can test full production setup
- Timeline viewer gets dedicated resources
- Better for performance testing

### Implementation:
1. **Provision new Droplet**:
   - 2GB RAM, 1 vCPU (minimum)
   - Ubuntu 22.04
   - Same region as production

2. **Setup both services**:
   - Main app on port 8000
   - Timeline viewer on port 5174
   - Shared Nginx for routing

## Deployment Steps (Option 1 - Recommended)

### 1. Prepare Staging Environment
```bash
# SSH to server
ssh root@your-server-ip

# Create staging structure
mkdir -p /opt/medical-patients-staging
cd /opt/medical-patients-staging

# Clone v1.1
git clone -b feature/v1.1-consolidated https://github.com/banton/medical-patients.git .

# Create .env.staging
cat > .env.staging << EOF
ENVIRONMENT=staging
DATABASE_URL=postgresql://medgen_user:medgen_password@localhost:5432/medgen_db_staging
REDIS_URL=redis://localhost:6379/1
API_KEY=staging_api_key_here
SECRET_KEY=staging_secret_key
PORT=8001
EOF
```

### 2. Create Staging Docker Compose
```yaml
# docker-compose.staging.yml
version: '3.8'

services:
  app-staging:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8001:8000"
    container_name: medical-patients-staging
    environment:
      - ENVIRONMENT=staging
      - DATABASE_URL=postgresql://medgen_user:medgen_password@db:5432/medgen_db_staging
      - REDIS_URL=redis://redis:6379/1
      - API_KEY=${API_KEY:-staging_key_here}
    networks:
      - medical-patients-network
    external_links:
      - medical-patients_db_1:db
      - medical-patients_redis_1:redis

  timeline-viewer:
    build:
      context: ./patient-timeline-viewer
      dockerfile: Dockerfile
    ports:
      - "5174:80"
    container_name: timeline-viewer
    networks:
      - medical-patients-network

networks:
  medical-patients-network:
    external: true
    name: medical-patients_default
```

### 3. Database Setup
```bash
# Create staging database
docker exec -it medical-patients_db_1 psql -U medgen_user -d medgen_db -c "CREATE DATABASE medgen_db_staging;"

# Run migrations on staging
docker-compose -f docker-compose.staging.yml run --rm app-staging alembic upgrade head
```

### 4. Deploy Staging
```bash
# Build and start staging
docker-compose -f docker-compose.staging.yml up -d --build

# Check logs
docker-compose -f docker-compose.staging.yml logs -f
```

### 5. Configure Nginx
```bash
# Add staging subdomain
sudo nano /etc/nginx/sites-available/staging.milmed.tech

# Add configuration (see above)
sudo ln -s /etc/nginx/sites-available/staging.milmed.tech /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Testing Plan

### 1. Smoke Tests
- [ ] API health check: `curl https://staging.milmed.tech/api/v1/health`
- [ ] Generate small batch (10 patients)
- [ ] Download results
- [ ] Check all API endpoints

### 2. Integration Tests
- [ ] API key management
- [ ] Configuration storage
- [ ] Job processing
- [ ] Timeline viewer data upload

### 3. Performance Tests
- [ ] Generate 1000 patients
- [ ] Monitor resource usage
- [ ] Check response times

## Rollback Plan
1. Stop staging containers: `docker-compose -f docker-compose.staging.yml down`
2. Remove staging database: `DROP DATABASE medgen_db_staging;`
3. Remove nginx config
4. Clean up directories

## Timeline Viewer Deployment

### Standalone Deployment (Recommended)
```bash
# Build production version
cd patient-timeline-viewer
npm install
npm run build

# Serve with nginx
server {
    listen 80;
    server_name timeline.milmed.tech;
    root /opt/timeline-viewer/dist;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

### Docker Deployment
```dockerfile
# patient-timeline-viewer/Dockerfile
FROM node:18-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
```

## Monitoring
- Set up health checks for both staging and timeline
- Monitor with `docker stats`
- Check nginx access logs
- Use Task status command: `task status`