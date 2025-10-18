#!/bin/bash

# System monitoring script
# Usage: ./monitor.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT/infra"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "========================================="
echo "BeautyHub SaaS - System Monitor"
echo "========================================="
echo ""

# Service status
echo "━━━ Container Status ━━━"
docker compose ps
echo ""

# Health checks
echo "━━━ Health Checks ━━━"
for service in traefik postgres redis api web worker beat; do
    HEALTH=$(docker inspect --format='{{.State.Health.Status}}' beautyhub_$service 2>/dev/null || echo "no-health-check")
    
    if [ "$HEALTH" = "healthy" ]; then
        echo -e "${GREEN}✓${NC} $service: healthy"
    elif [ "$HEALTH" = "unhealthy" ]; then
        echo -e "${RED}✗${NC} $service: unhealthy"
    elif [ "$HEALTH" = "starting" ]; then
        echo -e "${YELLOW}⟳${NC} $service: starting"
    else
        echo -e "  $service: no health check"
    fi
done
echo ""

# Resource usage
echo "━━━ Resource Usage ━━━"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
echo ""

# Disk usage
echo "━━━ Disk Usage ━━━"
df -h / | tail -n 1 | awk '{print "Root filesystem: " $3 " used / " $2 " total (" $5 " used)"}'

# Docker volumes
echo ""
VOLUMES_SIZE=$(docker system df -v --format '{{.Size}}' 2>/dev/null | head -1 || echo "unknown")
echo "Docker volumes: $VOLUMES_SIZE"
echo ""

# Recent errors
echo "━━━ Recent Errors (last 10) ━━━"
docker compose logs --tail=100 --since 1h 2>&1 | grep -i "error" | tail -n 10 || echo "No recent errors"
echo ""

# SSL Certificate expiry (if using Let's Encrypt)
if [ -f "./letsencrypt/acme.json" ]; then
    echo "━━━ SSL Certificates ━━━"
    echo "✓ ACME configuration exists"
    # Note: Detailed cert info requires jq parsing
    echo ""
fi

# Database size
echo "━━━ Database Info ━━━"
DB_SIZE=$(docker compose exec -T postgres psql -U saas -d saas -t -c "SELECT pg_size_pretty(pg_database_size('saas'));" 2>/dev/null | tr -d ' ' || echo "unknown")
echo "Database size: $DB_SIZE"

DB_CONNECTIONS=$(docker compose exec -T postgres psql -U saas -d saas -t -c "SELECT count(*) FROM pg_stat_activity;" 2>/dev/null | tr -d ' ' || echo "unknown")
echo "Active connections: $DB_CONNECTIONS"
echo ""

echo "========================================="
echo "Monitor complete - $(date)"
echo "========================================="
echo ""
echo "For continuous monitoring, use:"
echo "  watch -n 5 ./monitor.sh"
echo ""
echo "For live logs:"
echo "  ./logs.sh"

