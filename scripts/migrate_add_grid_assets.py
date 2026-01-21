#!/usr/bin/env python3
"""Add grid_asset table to database."""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from app import app
from app.extensions import db
from app.models.asset import GridAsset

def migrate():
    """Run migration."""
    with app.app_context():
        print("Creating grid_asset table...")
        db.create_all()
        
        # Check if table has data
        count = GridAsset.query.count()
        print(f"✅ Migration complete. Table has {count} assets.")

if __name__ == '__main__':
    migrate()
