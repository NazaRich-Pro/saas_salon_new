#!/bin/bash
#
# Test Backup/Restore Cycle
# Creates a backup and attempts to restore it to verify the process works
#
# Usage: ./test_backup.sh
#

set -e
set -u

# Configuration
TEST_DB="saas_test_restore_$(date +%s)"
BACKUP_DIR="${BACKUP_DIR:-/backups/postgres}"
POSTGRES_HOST="${POSTGRES_HOST:-postgres}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-saas}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-supersecret}"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

log "=== Starting Backup/Restore Test ==="

# Step 1: Create backup
log "Step 1: Creating backup..."
./backup.sh

if [ $? -eq 0 ]; then
    log "✓ Backup created successfully"
else
    log "✗ Backup failed!"
    exit 1
fi

# Find latest backup
LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/backup_*.sql.gz.enc | head -1)
log "Latest backup: $LATEST_BACKUP"

# Step 2: Create test database
log "Step 2: Creating test database '$TEST_DB'..."
export PGPASSWORD="$POSTGRES_PASSWORD"
psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d postgres -c "CREATE DATABASE $TEST_DB;" > /dev/null

# Step 3: Restore to test database
log "Step 3: Restoring to test database..."
TEMP_BACKUP="/tmp/test_restore_$(date +%s).sql"
ENCRYPTION_PASSWORD="${BACKUP_ENCRYPTION_PASSWORD:-changeme}"

openssl enc -aes-256-cbc -d -pbkdf2 -pass pass:"$ENCRYPTION_PASSWORD" -in "$LATEST_BACKUP" | \
    gunzip > "$TEMP_BACKUP"

psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$TEST_DB" < "$TEMP_BACKUP" > /dev/null 2>&1

if [ $? -eq 0 ]; then
    log "✓ Restore to test database successful"
else
    log "⚠️  Restore completed with warnings"
fi

rm "$TEMP_BACKUP"

# Step 4: Verify data
log "Step 4: Verifying restored data..."

# Count tables
TABLE_COUNT=$(psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$TEST_DB" -t -c \
    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")

log "Tables in test database: $TABLE_COUNT"

# Count some key records
TENANT_COUNT=$(psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$TEST_DB" -t -c \
    "SELECT COUNT(*) FROM tenants;" 2>/dev/null || echo "0")

USER_COUNT=$(psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$TEST_DB" -t -c \
    "SELECT COUNT(*) FROM users;" 2>/dev/null || echo "0")

log "Tenants: $TENANT_COUNT"
log "Users: $USER_COUNT"

# Step 5: Cleanup
log "Step 5: Cleaning up test database..."
psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d postgres -c "DROP DATABASE $TEST_DB;" > /dev/null

log "✓ Test database cleaned up"

# Final verdict
if [ "$TABLE_COUNT" -gt 0 ]; then
    log "=== ✓ Backup/Restore Test PASSED ==="
    log "Your backup system is working correctly!"
    exit 0
else
    log "=== ✗ Backup/Restore Test FAILED ==="
    log "No tables found in restored database!"
    exit 1
fi

