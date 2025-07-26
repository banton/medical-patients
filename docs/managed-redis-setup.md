# DigitalOcean Managed Redis Setup Guide

## Quick Setup Steps

### 1. Create Managed Redis Database
```bash
# Using DigitalOcean CLI
doctl databases create medical-patients-redis \
  --engine redis \
  --version 7 \
  --region nyc3 \
  --size db-s-1vcpu-1gb \
  --num-nodes 1
```

Or via the DigitalOcean Control Panel:
1. Go to Databases → Create Database
2. Choose Redis 7
3. Select Basic plan ($15/month)
4. Same region as your app (e.g., NYC3)
5. Same VPC as your app

### 2. Get Connection String
```bash
# Get the connection details
doctl databases connection medical-patients-redis --format "Host,Port,Password,SSL"

# Get the full connection string
doctl databases connection medical-patients-redis --format "URI"
```

The connection string will look like:
```
rediss://default:AVNS_xxxxxxxxxxxxx@db-redis-nyc3-xxxxx.db.ondigitalocean.com:25061/0
```

**Important**: Note the `rediss://` protocol (with double 's') for SSL connections.

### 3. Configure Trusted Sources
Add your app to trusted sources:
```bash
# Get your app's ID
doctl apps list

# Add app as trusted source
doctl databases firewalls append <database-id> --rule "type:app,value:<app-id>"
```

### 4. Update App Environment
```bash
# Set the Redis URL in your app
doctl apps config set <app-id> \
  REDIS_URL="rediss://default:password@hostname:25061/0" \
  CACHE_ENABLED="true"
```

### 5. Verify Connection
Check your app logs to confirm Redis connection:
```bash
doctl apps logs <app-id> --follow | grep -i redis
```

You should see:
```
Redis cache initialized successfully
```

## Troubleshooting

### Connection Refused
- Ensure app is in trusted sources
- Use private hostname if in same VPC
- Check Redis is in same region

### SSL Errors
- Ensure using `rediss://` (not `redis://`)
- App now handles SSL automatically

### Cache Not Working
- Check CACHE_ENABLED=true
- Verify REDIS_URL is set correctly
- Check app logs for errors

## Fallback Behavior

The application now gracefully handles Redis unavailability:
- If Redis connection fails at startup, the app continues without caching
- All cache operations safely return None/False when Redis is unavailable
- No errors are thrown to end users

## Cost
- Basic plan: $15/month (1GB RAM, 1 node)
- Includes: Automated backups, monitoring, SSL encryption

## Benefits Over Self-Hosted
- No maintenance required
- Automatic backups
- Built-in monitoring
- SSL encryption by default
- High availability options