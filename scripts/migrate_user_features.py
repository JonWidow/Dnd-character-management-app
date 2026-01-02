#!/usr/bin/env python3
"""
Migration script to add new user and character fields
Adds:
- User: created_at, last_login, theme_preference
- Character: is_favorite, notes
"""

import sqlite3
import sys
from pathlib import Path

# Get database path
db_path = Path(__file__).parent.parent / 'instance' / 'characters.db'

if not db_path.exists():
    print(f"Error: Database not found at {db_path}")
    sys.exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check and add columns to user table
    print("Checking user table...")
    cursor.execute("PRAGMA table_info(user)")
    columns = {row[1] for row in cursor.fetchall()}
    
    if 'created_at' not in columns:
        print("  - Adding created_at column...")
        cursor.execute("ALTER TABLE user ADD COLUMN created_at DATETIME")
    
    if 'last_login' not in columns:
        print("  - Adding last_login column...")
        cursor.execute("ALTER TABLE user ADD COLUMN last_login DATETIME")
    
    if 'theme_preference' not in columns:
        print("  - Adding theme_preference column...")
        cursor.execute("ALTER TABLE user ADD COLUMN theme_preference VARCHAR(20) DEFAULT 'light'")
    
    # Check and add columns to character table
    print("Checking character table...")
    cursor.execute("PRAGMA table_info(character)")
    columns = {row[1] for row in cursor.fetchall()}
    
    if 'is_favorite' not in columns:
        print("  - Adding is_favorite column...")
        cursor.execute("ALTER TABLE character ADD COLUMN is_favorite BOOLEAN DEFAULT 0")
    
    if 'notes' not in columns:
        print("  - Adding notes column...")
        cursor.execute("ALTER TABLE character ADD COLUMN notes TEXT DEFAULT ''")
    
    conn.commit()
    print("\n✓ Migration completed successfully!")
    
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("✓ Columns already exist - no changes needed")
    else:
        print(f"✗ Error: {e}")
        sys.exit(1)
finally:
    conn.close()
