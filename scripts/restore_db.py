#!/usr/bin/env python3
"""
Restore the database from a backup file.

Usage:
    python restore_db.py <backup_file>
    python restore_db.py --list      # List backups
    python restore_db.py --latest    # Restore from most recent backup
    
Example:
    python restore_db.py characters_20260102_153000.db
"""

import sys
import os
import shutil
from pathlib import Path
from datetime import datetime

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
INSTANCE_DIR = os.path.join(PROJECT_DIR, "instance")
DB_FILE = os.path.join(INSTANCE_DIR, "characters.db")

# Backups stored OUTSIDE project directory for safety
# This survives if /opt/dnd is accidentally deleted
BACKUPS_DIR = "/opt/backups/dnd"

def list_backups():
    """List all available backups."""
    if not os.path.exists(BACKUPS_DIR):
        print("No backups found.")
        return []
    
    backups = sorted(Path(BACKUPS_DIR).glob("characters_*.db"))
    if not backups:
        print("No backups found.")
        return []
    
    print("\nAvailable backups:")
    for i, backup_file in enumerate(backups, 1):
        size = backup_file.stat().st_size / 1024  # KB
        mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
        print(f"  {i}. {backup_file.name} ({size:.1f} KB) - {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
    
    return backups

def restore_from_backup(backup_name):
    """Restore database from a backup file."""
    backup_file = os.path.join(BACKUPS_DIR, backup_name)
    
    if not os.path.exists(backup_file):
        print(f"✗ Backup file not found: {backup_file}")
        return False
    
    # Create a safety backup of current DB if it exists
    if os.path.exists(DB_FILE):
        safety_backup = os.path.join(BACKUPS_DIR, f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
        try:
            shutil.copy2(DB_FILE, safety_backup)
            print(f"✓ Safety backup created: {safety_backup}")
        except Exception as e:
            print(f"✗ Failed to create safety backup: {e}")
            return False
    
    # Restore from backup
    try:
        shutil.copy2(backup_file, DB_FILE)
        size = os.path.getsize(DB_FILE) / 1024  # KB
        print(f"✓ Restored from: {backup_name} ({size:.1f} KB)")
        print(f"✓ Database restored to: {DB_FILE}")
        return True
    except Exception as e:
        print(f"✗ Restore failed: {e}")
        return False

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Restore the D&D app database from backup")
    parser.add_argument("backup", nargs="?", help="Backup filename to restore")
    parser.add_argument("--list", action="store_true", help="List available backups")
    parser.add_argument("--latest", action="store_true", help="Restore from most recent backup")
    
    args = parser.parse_args()
    
    if args.list:
        list_backups()
        return
    
    if args.latest:
        backups = list_backups()
        if backups:
            backup_name = backups[-1].name  # Most recent
            print(f"\nRestoring from latest backup: {backup_name}")
            if restore_from_backup(backup_name):
                print("✓ Restore completed successfully")
            else:
                sys.exit(1)
        else:
            sys.exit(1)
    elif args.backup:
        if restore_from_backup(args.backup):
            print("✓ Restore completed successfully")
        else:
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
