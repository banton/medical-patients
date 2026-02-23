# Redis Migration Guide: Custom to Managed Redis

## Overview
This guide documents the migration from a custom Redis container to DigitalOcean Managed Redis service.

## Benefits of Managed Redis
- **High Availability**: Automatic failover and redundancy
- **Managed Backups**: Automated daily backups with point-in-time recovery
- **Security**: SSL/TLS encryption, private networking
- **Monitoring**: Built-in metrics and alerts
- **Zero Maintenance**: No need to manage Redis versions or patches

## Configuration Changes

### 1. Environment Variables
Update your production environment variables:

```bash
# Old configuration (custom Redis container)
REDIS_URL=redis://redis:6379

# New configuration (managed Redis)
REDIS_URL=rediss://default:<password>@<cluster-name>.db.ondigitalocean.com:25061/0
```

**Important**: Note the `rediss://` protocol (with double 's') for SSL/TLS connections.

### 2. Application Files Updated
- `.env.example` - Added managed Redis documentation
- `production-app-spec.yaml` - Removed Redis service, using environment variable
- `docker-compose.staging.yml` - Added support for managed Redis URL
- `.do-app-spec-redis-service.yaml` - Removed Redis service definition

### 3. DigitalOcean Setup

#### Create Managed Redis Database
1. Go to DigitalOcean Control Panel > Databases
2. Click "Create Database"
3. Choose Redis
4. Select configuration:
   - **Engine**: Redis 7
   - **Plan**: Basic ($15/month for 1GB RAM)
   - **Region**: Same as your app (e.g., NYC3)
   - **VPC**: Same VPC as your app

#### Configure Connection
1. In the database overview, go to "Connection Details"
2. Choose the appropriate connection method:
   - **Private Network (Recommended)**: Use the VPC network connection string
   - **Public Network**: Use the public connection string (if trusted sources configured)
3. Connection format:
   ```
   rediss://default:<password>@<hostname>:25061/0
   ```
4. Add to your app's environment variables:
   ```bash
   doctl apps update <app-id> --spec production-app-spec.yaml
   doctl apps config set <app-id> REDIS_URL="rediss://default:<password>@<hostname>:25061/0"
   ```

#### Security Settings
1. Add your app to the trusted sources:
   - Go to Settings > Trusted Sources
   - Add your app's name
2. Enable eviction policy:
   - Go to Settings > Eviction Policy
   - Select "allkeys-lru" for cache behavior

## Migration Steps

### 1. Pre-Migration
- [ ] Create managed Redis database in DigitalOcean
- [ ] Test connection from local environment
- [ ] Update staging environment first

### 2. Migration
1. Update app environment variable:
   ```bash
   doctl apps config set <app-id> REDIS_URL=<managed-redis-url>
   ```

2. Deploy the updated app spec:
   ```bash
   doctl apps update <app-id> --spec production-app-spec.yaml
   ```

3. Monitor app logs for successful Redis connection:
   ```bash
   doctl apps logs <app-id> --follow
   ```

### 3. Post-Migration
- [ ] Verify cache operations are working
- [ ] Check application performance
- [ ] Remove old Redis container from billing

## Testing Connection

### Local Testing
```python
import redis
import ssl

# Create SSL context for managed Redis
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False

# Connect to managed Redis
r = redis.Redis.from_url(
    "rediss://default:password@cluster.db.ondigitalocean.com:25061/0",
    ssl_cert_reqs="required",
    ssl_ca_certs=None,
    ssl_context=ssl_context
)

# Test connection
print(r.ping())  # Should return True
```

### Application Testing
The application will automatically handle SSL connections when using `rediss://` URLs.

## Rollback Plan
If issues occur, revert to custom Redis:
1. Update REDIS_URL back to `redis://redis:6379`
2. Redeploy with the old app spec that includes Redis service

## Cost Comparison
- **Custom Redis Container**: $5/month (0.5GB RAM)
- **Managed Redis Basic**: $15/month (1GB RAM)
- **Additional Benefits**: Backups, monitoring, high availability

## Monitoring
After migration, monitor:
- Redis connection pool health at `/api/v1/health`
- Cache hit rates in application metrics
- Redis memory usage in DO dashboard
- Connection count and latency

## Troubleshooting

### SSL Connection Errors
If you see SSL errors, ensure:
- Using `rediss://` protocol (not `redis://`)
- Redis client library supports SSL (redis-py >= 4.0)

### Connection Timeouts
- **Private Network**: Ensure app and Redis are in the same VPC
- **Public Network**: Add your IP/app to trusted sources
- The private hostname (e.g., `private-*.db.ondigitalocean.com`) is only accessible within the VPC
- Test connectivity from within the app container, not from local machine

### Performance Issues
- Monitor latency between app and Redis
- Consider upgrading to a larger Redis plan if needed
- Check eviction policy settings

### Testing from Local Development
To test the managed Redis from your local machine:
1. Use the public hostname (not the private one)
2. Add your IP address to the trusted sources in the Redis settings
3. Or use an SSH tunnel through your DigitalOcean droplet