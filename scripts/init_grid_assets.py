#!/usr/bin/env python3
"""Initialize grid assets."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from app.models.asset import GridAsset
from app.extensions import db

# Sample assets to add
SAMPLE_ASSETS = [
    # Terrain
    {
        'name': 'Stone Floor',
        'description': 'Plain stone dungeon floor',
        'category': 'terrain',
        'file_path': 'terrain/stone_floor.svg',
        'width': 50,
        'height': 50,
        'is_passable': True,
        'color_tag': '#888888'
    },
    {
        'name': 'Grass',
        'description': 'Grassy terrain',
        'category': 'terrain',
        'file_path': 'terrain/grass.svg',
        'width': 50,
        'height': 50,
        'is_passable': True,
        'color_tag': '#228B22'
    },
    {
        'name': 'Water',
        'description': 'Water terrain',
        'category': 'terrain',
        'file_path': 'terrain/water.svg',
        'width': 50,
        'height': 50,
        'is_passable': False,
        'color_tag': '#4169E1'
    },
    # Objects
    {
        'name': 'Door',
        'description': 'Wooden door',
        'category': 'object',
        'file_path': 'objects/door.svg',
        'width': 40,
        'height': 50,
        'is_passable': False,
        'color_tag': '#8B4513'
    },
    {
        'name': 'Pillar',
        'description': 'Stone pillar',
        'category': 'object',
        'file_path': 'objects/pillar.svg',
        'width': 50,
        'height': 50,
        'is_passable': False,
        'color_tag': '#A9A9A9'
    },
    {
        'name': 'Table',
        'description': 'Wooden table',
        'category': 'object',
        'file_path': 'objects/table.svg',
        'width': 60,
        'height': 40,
        'is_passable': False,
        'color_tag': '#D2691E'
    },
    # Effects
    {
        'name': 'Fire',
        'description': 'Fire effect',
        'category': 'effect',
        'file_path': 'effects/fire.svg',
        'width': 40,
        'height': 40,
        'is_passable': True,
        'color_tag': '#FF4500'
    },
    {
        'name': 'Ice',
        'description': 'Ice/frost effect',
        'category': 'effect',
        'file_path': 'effects/ice.svg',
        'width': 40,
        'height': 40,
        'is_passable': True,
        'color_tag': '#87CEEB'
    },
    {
        'name': 'Magic Circle',
        'description': 'Magical circle',
        'category': 'effect',
        'file_path': 'effects/magic_circle.svg',
        'width': 50,
        'height': 50,
        'is_passable': True,
        'color_tag': '#9932CC'
    },
]

def init_assets():
    """Initialize sample assets in the database."""
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Check if assets already exist
        existing = GridAsset.query.first()
        if existing:
            print("Assets already initialized. Skipping...")
            return
        
        # Add sample assets
        for asset_data in SAMPLE_ASSETS:
            asset = GridAsset(**asset_data)
            db.session.add(asset)
        
        db.session.commit()
        print(f"✅ Initialized {len(SAMPLE_ASSETS)} grid assets")

if __name__ == '__main__':
    init_assets()
