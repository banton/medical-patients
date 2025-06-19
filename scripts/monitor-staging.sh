#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=== Staging Environment Status ===${NC}"
echo ""

# Check Docker containers
echo -e "${YELLOW}Docker Containers:${NC}"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(staging|timeline)"
echo ""

# Check staging health
echo -e "${YELLOW}Staging API Health:${NC}"
STAGING_HEALTH=$(curl -s http://localhost:8001/api/v1/health 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "$STAGING_HEALTH" | jq -r '.status // "Unknown"'
else
    echo -e "${RED}Failed to connect to staging API${NC}"
fi
echo ""

# Check database connections
echo -e "${YELLOW}Database Connections:${NC}"
docker exec medical-patients_db_1 psql -U medgen_user -d postgres -c "
SELECT datname, count(*) as connections 
FROM pg_stat_activity 
WHERE datname IN ('medgen_db', 'medgen_db_staging')
GROUP BY datname;"
echo ""

# Check Redis
echo -e "${YELLOW}Redis Status:${NC}"
docker exec medical-patients_redis_1 redis-cli INFO server | grep -E "(redis_version|uptime_in_days)"
echo ""

# Check disk usage
echo -e "${YELLOW}Disk Usage:${NC}"
df -h | grep -E "(Filesystem|/$)"
echo ""

# Recent logs
echo -e "${YELLOW}Recent Staging Logs (last 20 lines):${NC}"
docker logs medical-patients-staging --tail 20 2>&1 | tail -20

echo ""
echo -e "${GREEN}=== End of Status Report ===${NC}"