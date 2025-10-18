#!/bin/bash
#
# PostgreSQL Restore Script
# Restores from encrypted backup
#
# Usage: ./restore.sh <backup_file>
# Example: ./restore.sh /backups/postgres/backup_20251012_020000.sql.gz.enc
#
# WARNING: This will DROP and recreate the database!
#

set -e
set -u

# Check arguments
if [ $# -lt 1 ]; then
    echo "Usage: $0 <backup_file>"
    echo "Example: $0 /backups/postgres/backup_20251012_020000.sql.gz.enc"
    exit 1
fi

BACKUP_FILE="$1"

# Configuration
POSTGRES_HOST="${POSTGRES_HOST:-postgres}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_DB="${POSTGRES_DB:-saas}"
POSTGRES_USER="${POSTGRES_USER:-saas}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-supersecret}"
ENCRYPTION_PASSWORD="${BACKUP_ENCRYPTION_PASSWORD:-changeme}"

# Logging
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    log "✗ Backup file not found: $BACKUP_FILE"
    exit 1
fi

log "=== Starting PostgreSQL Restore ==="
log "Backup file: $BACKUP_FILE"

# Confirmation prompt
read -p "⚠️  WARNING: This will DROP and recreate the database '$POSTGRES_DB'. Continue? (yes/no): " -r
if [[ ! $REPLY =~ ^yes$ ]]; then
    log "Restore cancelled by user"
    exit 0
fi

# Set PostgreSQL password
export PGPASSWORD="$POSTGRES_PASSWORD"

# Test database connection
log "Testing database connection..."
psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d postgres -c "SELECT version();" > /dev/null

if [ $? -eq 0 ]; then
    log "✓ Database connection successful"
else
    log "✗ Database connection failed!"
    exit 1
fi

# Decrypt and decompress backup
log "Decrypting and decompressing backup..."
TEMP_BACKUP="/tmp/restore_$(date +%s).sql"
openssl enc -aes-256-cbc -d -pbkdf2 -pass pass:"$ENCRYPTION_PASSWORD" -in "$BACKUP_FILE" | \
    gunzip > "$TEMP_BACKUP"

if [ $? -eq 0 ]; then
    log "✓ Backup decrypted successfully"
else
    log "✗ Decryption failed! Check encryption password."
    exit 1
fi

# Drop existing connections
log "Terminating existing database connections..."
psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d postgres -c \
    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$POSTGRES_DB' AND pid <> pg_backend_pid();" \
    > /dev/null 2>&1

# Drop and recreate database
log "Dropping database '$POSTGRES_DB'..."
psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d postgres -c "DROP DATABASE IF EXISTS $POSTGRES_DB;" > /dev/null

log "Creating database '$POSTGRES_DB'..."
psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d postgres -c "CREATE DATABASE $POSTGRES_DB;" > /dev/null

if [ $? -eq 0 ]; then
    log "✓ Database recreated"
else
    log "✗ Failed to recreate database!"
    rm "$TEMP_BACKUP"
    exit 1
fi

# Restore backup
log "Restoring backup..."
psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$TEMP_BACKUP" 2>&1 | tee /tmp/restore.log

if [ ${PIPESTATUS[0]} -eq 0 ]; then
    log "✓ Restore completed successfully"
else
    log "⚠️  Restore completed with warnings (check /tmp/restore.log)"
fi

# Clean up temp file
rm "$TEMP_BACKUP"
log "✓ Temporary files cleaned up"

# Verify restore
log "Verifying restore..."
TABLE_COUNT=$(psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c \
    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")

log "Tables restored: $TABLE_COUNT"

if [ "$TABLE_COUNT" -gt 0 ]; then
    log "✓ Restore verification passed"
else
    log "✗ Restore verification failed - no tables found!"
    exit 1
fi

log "=== Restore completed successfully ==="
log ""
log "Next steps:"
log "1. Verify application functionality"
log "2. Check data integrity"
log "3. Restart application services if needed"

exit 0
