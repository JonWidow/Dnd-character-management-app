#!/usr/bin/env python3
"""
Migration script to add armor_class column to character table.
This allows storing and displaying AC for each character.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from app.models import db

def migrate():
    with app.app_context():
        with db.engine.begin() as connection:
            # Check if the column already exists
            inspector = db.inspect(db.engine)
            columns = [c['name'] for c in inspector.get_columns('character')]
            
            if 'armor_class' not in columns:
                connection.execute(db.text(
                    "ALTER TABLE character ADD COLUMN armor_class INTEGER DEFAULT 10"
                ))
                print("✓ Added armor_class column to character table")
                print("✓ Default AC set to 10 for existing characters")
            else:
                print("✓ armor_class column already exists")

if __name__ == "__main__":
    migrate()
    print("\nMigration complete!")
