#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration script to add skill_choice_count column to character_classes table.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from sqlalchemy import text

def migrate():
    """Add skill_choice_count column to character_classes table."""
    with app.app_context():
        engine = db.engine
        
        # Get list of existing columns
        inspector = db.inspect(engine)
        existing_columns = [col['name'] for col in inspector.get_columns('character_classes')]
        
        if 'skill_choice_count' not in existing_columns:
            print("Adding column: skill_choice_count")
            sql = "ALTER TABLE character_classes ADD COLUMN skill_choice_count INTEGER DEFAULT 0"
            try:
                with engine.begin() as conn:
                    conn.execute(text(sql))
                print("  ✓ skill_choice_count added successfully")
            except Exception as e:
                print(f"  ✗ Error adding skill_choice_count: {e}")
        else:
            print("Column skill_choice_count already exists, skipping...")
        
        print("\nMigration complete!")

if __name__ == "__main__":
    migrate()
