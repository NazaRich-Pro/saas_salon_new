#!/bin/bash
#
# PostgreSQL Backup Script
# Performs encrypted daily backups with 14-day retention
#
# Usage: ./backup.sh
# Cron: 0 2 * * * /path/to/backup.sh
#

set -e  # Exit on error
set -u  # Exit on undefined variable

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/backups/postgres}"
POSTGRES_HOST="${POSTGRES_HOST:-postgres}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_DB="${POSTGRES_DB:-saas}"
POSTGRES_USER="${POSTGRES_USER:-saas}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-supersecret}"
ENCRYPTION_PASSWORD="${BACKUP_ENCRYPTION_PASSWORD:-changeme}"
RETENTION_DAYS=14

# Date format for backup filename
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/backup_${DATE}.sql"
ENCRYPTED_BACKUP="${BACKUP_FILE}.gz.enc"

# Logging
LOG_FILE="${BACKUP_DIR}/backup.log"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=== Starting PostgreSQL Backup ==="

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Set PostgreSQL password
export PGPASSWORD="$POSTGRES_PASSWORD"

# Perform backup
log "Creating backup: $BACKUP_FILE"
pg_dump \
    -h "$POSTGRES_HOST" \
    -p "$POSTGRES_PORT" \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    --format=plain \
    --no-owner \
    --no-acl \
    --verbose \
    > "$BACKUP_FILE" 2>> "$LOG_FILE"

if [ $? -eq 0 ]; then
    log "✓ Backup created successfully"
else
    log "✗ Backup failed!"
    exit 1
fi

# Compress and encrypt backup
log "Compressing and encrypting backup..."
gzip -c "$BACKUP_FILE" | \
    openssl enc -aes-256-cbc -salt -pbkdf2 -pass pass:"$ENCRYPTION_PASSWORD" \
    > "$ENCRYPTED_BACKUP"

if [ $? -eq 0 ]; then
    log "✓ Backup encrypted: $ENCRYPTED_BACKUP"
    # Remove unencrypted backup
    rm "$BACKUP_FILE"
    log "✓ Unencrypted backup removed"
else
    log "✗ Encryption failed!"
    exit 1
fi

# Calculate backup size
BACKUP_SIZE=$(du -h "$ENCRYPTED_BACKUP" | cut -f1)
log "Backup size: $BACKUP_SIZE"

# Clean up old backups (keep last 14 days)
log "Cleaning up old backups (keeping last $RETENTION_DAYS days)..."
find "$BACKUP_DIR" -name "backup_*.sql.gz.enc" -type f -mtime +$RETENTION_DAYS -delete

OLD_BACKUP_COUNT=$(find "$BACKUP_DIR" -name "backup_*.sql.gz.enc" -type f | wc -l)
log "Backups remaining: $OLD_BACKUP_COUNT"

# Verify backup integrity
log "Verifying backup integrity..."
openssl enc -aes-256-cbc -d -pbkdf2 -pass pass:"$ENCRYPTION_PASSWORD" -in "$ENCRYPTED_BACKUP" | gzip -t

if [ $? -eq 0 ]; then
    log "✓ Backup integrity verified"
else
    log "✗ Backup integrity check failed!"
    exit 1
fi

log "=== Backup completed successfully ==="
log ""

# Optional: Send notification (Slack/Email/Telegram)
# curl -X POST https://hooks.slack.com/... -d "Backup completed: $BACKUP_SIZE"

exit 0
