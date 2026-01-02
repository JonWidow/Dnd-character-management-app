#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration script to add proficiency columns to character_classes table.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from sqlalchemy import text

def migrate():
    """Add proficiency columns to character_classes table."""
    with app.app_context():
        engine = db.engine
        
        # Get list of existing columns
        inspector = db.inspect(engine)
        existing_columns = [col['name'] for col in inspector.get_columns('character_classes')]
        
        columns_to_add = [
            ('skill_proficiencies', 'JSON'),
            ('armor_proficiencies', 'JSON'),
            ('weapon_proficiencies', 'JSON'),
            ('tool_proficiencies', 'JSON'),
            ('saving_throw_proficiencies', 'JSON'),
        ]
        
        for col_name, col_type in columns_to_add:
            if col_name not in existing_columns:
                print(f"Adding column: {col_name}")
                sql = f"ALTER TABLE character_classes ADD COLUMN {col_name} {col_type} DEFAULT '[]'"
                try:
                    with engine.begin() as conn:
                        conn.execute(text(sql))
                    print(f"  ✓ {col_name} added successfully")
                except Exception as e:
                    print(f"  ✗ Error adding {col_name}: {e}")
            else:
                print(f"Column {col_name} already exists, skipping...")
        
        print("\nMigration complete!")

if __name__ == "__main__":
    migrate()
