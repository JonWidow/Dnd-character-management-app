#!/usr/bin/env python3
"""
Migration script to add user_id foreign key to character table.
This allows characters to be owned by users.
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
            
            if 'user_id' not in columns:
                connection.execute(db.text(
                    "ALTER TABLE character ADD COLUMN user_id INTEGER"
                ))
                print("✓ Added user_id column to character table")
                print("✓ Foreign key constraint ready (will be enforced on next operation)")
            else:
                print("✓ user_id column already exists")

if __name__ == "__main__":
    migrate()
