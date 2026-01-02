#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration script to add subclass_id column to character table.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from sqlalchemy import text

def migrate():
    """Add subclass_id column to character table."""
    with app.app_context():
        engine = db.engine
        
        # Get list of existing columns
        inspector = db.inspect(engine)
        existing_columns = [col['name'] for col in inspector.get_columns('character')]
        
        if 'subclass_id' not in existing_columns:
            print("Adding column: subclass_id")
            sql = "ALTER TABLE character ADD COLUMN subclass_id INTEGER REFERENCES subclasses(id)"
            try:
                with engine.begin() as conn:
                    conn.execute(text(sql))
                print("  ✓ subclass_id added successfully")
            except Exception as e:
                print(f"  ✗ Error adding subclass_id: {e}")
        else:
            print("Column subclass_id already exists, skipping...")
        
        print("\nMigration complete!")

if __name__ == "__main__":
    migrate()
