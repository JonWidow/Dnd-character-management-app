#!/usr/bin/env python3
"""
Migration script to add placed_asset table for grid asset persistence.
"""

import sys
import os

# Add parent directory to path so we can import app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import app, db
from app.models.asset import PlacedAsset

def migrate():
    """Create the placed_asset table."""
    with app.app_context():
        try:
            # Create the table
            db.create_all()
            print("✓ Created placed_asset table")
            
            # Verify the table exists
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'placed_asset' in tables:
                columns = [col['name'] for col in inspector.get_columns('placed_asset')]
                print(f"✓ Table has columns: {', '.join(columns)}")
                return True
            else:
                print("✗ Failed to create placed_asset table")
                return False
                
        except Exception as e:
            print(f"✗ Error: {e}")
            return False

if __name__ == '__main__':
    success = migrate()
    sys.exit(0 if success else 1)
