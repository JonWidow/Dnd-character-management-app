#!/bin/bash

# Database backup script for D&D Character Management App
# This script backs up the SQLite database to a timestamped file
# Usage: ./backup_db.sh [backup_type] [retention_count]
# Default backup_type is "daily" and retention_count is 3 if not specified

DB_PATH="/opt/Dnd-character-management-app/instance/characters.db"
BACKUP_DIR="/opt/backups"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_TYPE=${1:-daily}
RETENTION_COUNT=${2:-3}
BACKUP_FILE="$BACKUP_DIR/characters_backup_${BACKUP_TYPE}_$TIMESTAMP.db"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Check if database exists
if [ ! -f "$DB_PATH" ]; then
    echo "Error: Database file not found at $DB_PATH" >> "$BACKUP_DIR/backup.log"
    exit 1
fi

# Create backup using cp (SQLite safe method)
cp "$DB_PATH" "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backup created successfully: $BACKUP_FILE (type: $BACKUP_TYPE)" >> "$BACKUP_DIR/backup.log"
    
    # Keep only the specified number of recent backups of this type to save space
    KEEP_COUNT=$((RETENTION_COUNT + 1))
    ls -t "$BACKUP_DIR"/characters_backup_${BACKUP_TYPE}_*.db 2>/dev/null | tail -n +$KEEP_COUNT | xargs -r rm
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Cleanup completed - kept $RETENTION_COUNT most recent $BACKUP_TYPE backups" >> "$BACKUP_DIR/backup.log"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backup failed for database at $DB_PATH" >> "$BACKUP_DIR/backup.log"
    exit 1
fi
