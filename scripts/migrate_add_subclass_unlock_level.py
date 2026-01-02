#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from app.models.character_struct import CharacterClassModel

def migrate():
    """Add subclass_unlock_level column to character_classes table if it doesn't exist."""
    with app.app_context():
        # Use raw SQL to check and add the column
        with db.engine.connect() as conn:
            # Check if column exists
            try:
                result = conn.execute(db.text("PRAGMA table_info(character_classes)"))
                columns = [row[1] for row in result]
                
                if 'subclass_unlock_level' not in columns:
                    print("Adding subclass_unlock_level column...")
                    conn.execute(db.text("ALTER TABLE character_classes ADD COLUMN subclass_unlock_level INTEGER DEFAULT 3"))
                    conn.commit()
                    print("✓ Column added successfully")
                else:
                    print("✓ Column already exists")
            except Exception as e:
                print(f"✗ Error: {e}")
                return False
    
    return True

if __name__ == "__main__":
    if migrate():
        print("[DONE] Migration complete")
    else:
        print("[ERROR] Migration failed")
        sys.exit(1)
