# DigitalOcean Staging Implementation Plan

## Overview
Create a complete staging environment using DigitalOcean App Platform that mirrors production but uses the v1.1 branch.

## Current Production Setup
- **App Platform**: medical-patients-generator-redis
- **Database**: Managed PostgreSQL 17 (app-7a761f5d-a598-4efc-9f1a-cd756365d498)
- **Region**: NYC
- **Domain**: milmed.tech
- **Components**:
  - API service (Python/FastAPI)
  - Redis service (internal)
  - Frontend static site
  - Managed PostgreSQL database

## Staging Architecture

### Option 1: Duplicate App Platform (Recommended)
Create a separate App Platform app for staging with:
- Same structure as production
- Different database (staging database)
- Branch: feature/v1.1-consolidated
- Domains: staging.milmed.tech, timeline.milmed.tech

### Option 2: Add Staging Components to Existing App
Add staging services to the existing app with different paths/ports.

## Implementation Steps

### Phase 1: Prepare App Specification

```yaml
# staging-app-spec.yaml
name: medical-patients-staging
region: nyc

services:
  - name: api-staging
    github:
      repo: banton/medical-patients
      branch: feature/v1.1-consolidated
      deploy_on_push: true
    build_command: pip install -r requirements.txt
    run_command: |
      if [ ! -z "$DATABASE_URL" ]; then
        alembic upgrade head
      fi
      python -m uvicorn src.main:app --host 0.0.0.0 --port $PORT
    source_dir: /
    environment_slug: python
    instance_size_slug: apps-s-1vcpu-0.5gb
    instance_count: 1
    http_port: 8080
    health_check:
      initial_delay_seconds: 30
      period_seconds: 30
      timeout_seconds: 10
      success_threshold: 1
      failure_threshold: 3
      http_path: /api/v1/health
    envs:
      - key: ENVIRONMENT
        value: staging
        scope: RUN_AND_BUILD_TIME
      - key: DATABASE_URL
        value: ${staging_db.DATABASE_URL}
        scope: RUN_AND_BUILD_TIME
      - key: REDIS_URL
        value: redis://redis-staging:6379
        scope: RUN_AND_BUILD_TIME
      - key: CACHE_ENABLED
        value: "true"
        scope: RUN_AND_BUILD_TIME
      - key: DEBUG
        value: "false"
        scope: RUN_AND_BUILD_TIME
      - key: CORS_ORIGINS
        value: "https://staging.milmed.tech,https://timeline.milmed.tech"
        scope: RUN_AND_BUILD_TIME
      - key: API_KEY
        value: ${STAGING_API_KEY}
        scope: RUN_AND_BUILD_TIME
        type: SECRET

  - name: redis-staging
    image:
      registry_type: DOCKER_HUB
      registry: library
      repository: redis
      tag: 7-alpine
    run_command: redis-server --appendonly yes --dir /data
    instance_size_slug: apps-s-1vcpu-0.5gb
    instance_count: 1
    internal_ports:
      - 6379

static_sites:
  - name: frontend-staging
    github:
      repo: banton/medical-patients
      branch: feature/v1.1-consolidated
      deploy_on_push: true
    source_dir: /static
    
  - name: timeline-viewer
    github:
      repo: banton/medical-patients
      branch: feature/v1.1-consolidated
      deploy_on_push: true
    build_command: cd patient-timeline-viewer && npm install && npm run build
    source_dir: /patient-timeline-viewer
    output_dir: /patient-timeline-viewer/dist

databases:
  - name: staging-db
    engine: PG
    version: "17"
    production: false
    size: db-s-1vcpu-1gb
    num_nodes: 1

domains:
  - domain: staging.milmed.tech
    type: PRIMARY
  - domain: timeline.milmed.tech
    type: ALIAS

ingress:
  rules:
    # Timeline viewer on timeline.milmed.tech
    - match:
        path:
          prefix: /
      component:
        name: timeline-viewer
      cors:
        allow_origins:
          - prefix: https://staging.milmed.tech
    
    # API routes on staging.milmed.tech
    - match:
        path:
          prefix: /api
      component:
        name: api-staging
        preserve_path_prefix: true
    
    # Docs on staging.milmed.tech
    - match:
        path:
          prefix: /docs
      component:
        name: api-staging
        preserve_path_prefix: true
    
    # OpenAPI spec
    - match:
        path:
          prefix: /openapi.json
      component:
        name: api-staging
        preserve_path_prefix: true
    
    # Frontend on staging.milmed.tech
    - match:
        path:
          prefix: /
      component:
        name: frontend-staging
```

### Phase 2: Create Staging Database

```bash
# Using DO CLI to create staging database
doctl databases create \
  --engine pg \
  --name medical-patients-staging-db \
  --region nyc1 \
  --size db-s-1vcpu-1gb \
  --version 17
```

### Phase 3: Deploy Using DigitalOcean MCP

```python
# deploy-staging.py
import json
from mcp_digitalocean import create_app, get_database_connection_string

# Read app spec
with open('staging-app-spec.yaml', 'r') as f:
    app_spec = yaml.safe_load(f)

# Get staging database connection string
db_info = get_database_connection_string('medical-patients-staging-db')
app_spec['services'][0]['envs'][1]['value'] = db_info['connection_string']

# Create staging app
response = create_app(
    spec=app_spec,
    project_id='d081419f-f93f-44a5-a7df-8430ba834788'  # Same project as production
)

print(f"Staging app created: {response['app']['id']}")
```

### Phase 4: DNS Configuration

```bash
# Add DNS records for subdomains
doctl compute domain records create milmed.tech \
  --record-type CNAME \
  --record-name staging \
  --record-data medical-patients-staging.ondigitalocean.app

doctl compute domain records create milmed.tech \
  --record-type CNAME \
  --record-name timeline \
  --record-data medical-patients-staging.ondigitalocean.app
```

### Phase 5: Environment Variables Setup

```bash
# Set staging-specific secrets
doctl apps update <staging-app-id> \
  --spec-env name=STAGING_API_KEY,value=<new-staging-key>,type=SECRET \
  --spec-env name=SECRET_KEY,value=<staging-secret>,type=SECRET
```

## Monitoring and Testing

### Health Checks
```bash
# Check staging API health
curl https://staging.milmed.tech/api/v1/health

# Check timeline viewer
curl https://timeline.milmed.tech/

# Check database connectivity
doctl databases connection <staging-db-id> --format json
```

### Deployment Monitoring
```bash
# Watch deployment progress
doctl apps list-deployments <staging-app-id>

# Get deployment logs
doctl apps logs <staging-app-id> --type=deploy

# Get runtime logs
doctl apps logs <staging-app-id> --type=run
```

## Cost Analysis

### Staging Environment Monthly Cost:
- **API Service**: $5/month (Basic 512MB)
- **Redis Service**: $5/month (Basic 512MB)
- **Database**: $15/month (1GB/1vCPU)
- **Static Sites**: Free
- **Total**: ~$25/month

### Production Environment (Current):
- **API + Redis**: $10/month
- **Database**: Included in app
- **Total**: ~$10/month

## Rollback Plan

1. **Quick Rollback**:
   ```bash
   # Delete staging app
   doctl apps delete <staging-app-id>
   
   # Delete staging database
   doctl databases delete <staging-db-id>
   
   # Remove DNS records
   doctl compute domain records delete milmed.tech <staging-record-id>
   doctl compute domain records delete milmed.tech <timeline-record-id>
   ```

2. **Preserve Data Rollback**:
   - Take database snapshot before deletion
   - Export configurations
   - Document any issues found

## Advantages of This Approach

1. **Complete Isolation**: Staging is completely separate from production
2. **Easy Deployment**: Push to branch triggers automatic deployment
3. **Cost Effective**: Only $25/month for full staging environment
4. **Production Parity**: Uses same App Platform features as production
5. **Easy Cleanup**: Single command to tear down entire staging

## Timeline

1. **Day 1**: 
   - Create staging database
   - Deploy staging app
   - Configure DNS

2. **Day 2**:
   - Test all endpoints
   - Verify timeline viewer
   - Load test with sample data

3. **Day 3**:
   - Fix any issues
   - Document findings
   - Plan production deployment