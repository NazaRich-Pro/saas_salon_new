#!/bin/bash

# Log monitoring script
# Usage: ./logs.sh [service] [options]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

SERVICE=$1
OPTIONS="${@:2}"

cd "$PROJECT_ROOT/infra"

echo "========================================="
echo "BeautyHub SaaS - Logs"
echo "========================================="
echo ""

if [ -z "$SERVICE" ]; then
    echo "Showing logs for all services..."
    echo ""
    docker compose logs -f --tail=100 $OPTIONS
elif [ "$SERVICE" = "list" ]; then
    echo "Available services:"
    docker compose ps --services
elif [ "$SERVICE" = "errors" ]; then
    echo "Showing ERROR logs for all services..."
    echo ""
    docker compose logs --tail=500 | grep -i "error"
elif [ "$SERVICE" = "warnings" ]; then
    echo "Showing WARNING logs for all services..."
    echo ""
    docker compose logs --tail=500 | grep -i "warning"
else
    echo "Showing logs for: $SERVICE"
    echo ""
    docker compose logs -f --tail=100 $SERVICE $OPTIONS
fi

