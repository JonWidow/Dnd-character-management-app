"""Asset management for grid tokens, terrain, and effects."""

import os
from pathlib import Path
import json

ASSET_BASE_PATH = Path(__file__).parent.parent / 'static' / 'assets'

ASSET_CATEGORIES = {
    'tokens': 'Character and creature tokens',
    'terrain': 'Terrain and tile assets',
    'objects': 'Objects, furniture, and props',
    'effects': 'Spell effects and visual effects'
}


def get_assets(category=None):
    """
    Get list of all assets, optionally filtered by category.
    
    Args:
        category (str, optional): Filter by asset category ('tokens', 'terrain', 'objects', 'effects')
    
    Returns:
        dict: Categorized assets with metadata
    """
    assets = {}
    
    categories_to_scan = [category] if category else list(ASSET_CATEGORIES.keys())
    
    for cat in categories_to_scan:
        cat_path = ASSET_BASE_PATH / cat
        if not cat_path.exists():
            assets[cat] = []
            continue
        
        # Get all SVG files in the category
        svg_files = sorted(cat_path.glob('*.svg'))
        
        assets[cat] = [
            {
                'name': f.stem,
                'filename': f.name,
                'path': f'/static/assets/{cat}/{f.name}',
                'category': cat,
                'type': 'svg'
            }
            for f in svg_files
        ]
    
    return assets if category is None else assets.get(category, [])


def get_asset(category, filename):
    """
    Get a specific asset.
    
    Args:
        category (str): Asset category
        filename (str): Filename of the asset
    
    Returns:
        dict: Asset metadata if exists, None otherwise
    """
    assets = get_assets(category)
    for asset in assets:
        if asset['filename'] == filename:
            return asset
    return None


def asset_exists(category, filename):
    """Check if an asset exists."""
    asset_path = ASSET_BASE_PATH / category / filename
    return asset_path.exists() and asset_path.suffix.lower() == '.svg'


def get_asset_categories():
    """Get all available asset categories."""
    return ASSET_CATEGORIES


def import_asset_metadata(category):
    """
    Import metadata for assets in a category from a JSON file.
    Expected format: /app/static/assets/{category}/metadata.json
    
    Args:
        category (str): Asset category
    
    Returns:
        dict: Metadata keyed by asset filename, or empty dict if no metadata file
    """
    metadata_path = ASSET_BASE_PATH / category / 'metadata.json'
    
    if metadata_path.exists():
        try:
            with open(metadata_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    
    return {}
