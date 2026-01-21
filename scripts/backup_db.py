#!/usr/bin/env python3
"""
Backup the SQLite database to a timestamped file.
Can be run manually or via cron for automated backups.

Usage:
    python backup_db.py [--keep-days 30]
    
Creates backups in: instance/backups/
"""

import sys
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
INSTANCE_DIR = os.path.join(PROJECT_DIR, "instance")
DB_FILE = os.path.join(INSTANCE_DIR, "characters.db")

# Backups stored OUTSIDE project directory for safety
# This survives if /opt/dnd is accidentally deleted
BACKUPS_DIR = "/opt/backups/dnd"

def setup_backup_dir():
    """Ensure backup directory exists."""
    os.makedirs(BACKUPS_DIR, exist_ok=True)
    print(f"Backup directory: {BACKUPS_DIR}")

def backup_database():
    """Create a timestamped backup of the database."""
    if not os.path.exists(DB_FILE):
        print(f"✗ Database file not found: {DB_FILE}")
        return False
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUPS_DIR, f"characters_{timestamp}.db")
    
    try:
        shutil.copy2(DB_FILE, backup_file)
        size = os.path.getsize(backup_file) / 1024  # KB
        print(f"✓ Backup created: {backup_file} ({size:.1f} KB)")
        return True
    except Exception as e:
        print(f"✗ Backup failed: {e}")
        return False

def cleanup_old_backups(keep_days=30):
    """Delete backups older than keep_days."""
    if not os.path.exists(BACKUPS_DIR):
        return
    
    cutoff = datetime.now() - timedelta(days=keep_days)
    deleted = 0
    
    for backup_file in Path(BACKUPS_DIR).glob("characters_*.db"):
        try:
            mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
            if mtime < cutoff:
                backup_file.unlink()
                deleted += 1
                print(f"  Deleted old backup: {backup_file.name}")
        except Exception as e:
            print(f"  Error deleting {backup_file.name}: {e}")
    
    if deleted > 0:
        print(f"✓ Cleaned up {deleted} old backup(s)")

def list_backups():
    """List all available backups."""
    if not os.path.exists(BACKUPS_DIR):
        print("No backups found.")
        return
    
    backups = sorted(Path(BACKUPS_DIR).glob("characters_*.db"))
    if not backups:
        print("No backups found.")
        return
    
    print("\nAvailable backups:")
    for i, backup_file in enumerate(backups, 1):
        size = backup_file.stat().st_size / 1024  # KB
        mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
        print(f"  {i}. {backup_file.name} ({size:.1f} KB) - {mtime.strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Backup the D&D app database")
    parser.add_argument("--keep-days", type=int, default=30, help="Keep backups for N days (default: 30)")
    parser.add_argument("--list", action="store_true", help="List available backups")
    parser.add_argument("--no-cleanup", action="store_true", help="Don't clean up old backups")
    
    args = parser.parse_args()
    
    setup_backup_dir()
    
    if args.list:
        list_backups()
        return
    
    if backup_database():
        if not args.no_cleanup:
            cleanup_old_backups(args.keep_days)
        print(f"✓ Backup completed successfully")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
