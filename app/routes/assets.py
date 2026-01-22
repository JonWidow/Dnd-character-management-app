"""Blueprint for grid asset management."""
from flask import Blueprint, jsonify, request, current_app
from app.models import db
from app.models.asset import GridAsset, PlacedAsset
from app.utils.asset_manager import get_assets, get_asset_categories
import os
from pathlib import Path

assets_bp = Blueprint('assets', __name__, url_prefix='/api/assets')


@assets_bp.route('/files', methods=['GET'])
def get_asset_files():
    """Get list of available SVG asset files from the static/assets directory."""
    category = request.args.get('category')
    assets = get_assets(category)
    
    if category:
        return jsonify(assets)
    
    # Return all categories
    return jsonify(assets)


@assets_bp.route('/files/categories', methods=['GET'])
def get_asset_file_categories():
    """Get all available asset categories from filesystem."""
    categories = get_asset_categories()
    return jsonify(categories)


@assets_bp.route('/list', methods=['GET'])
def list_assets():
    """Get all available grid assets, optionally filtered by category."""
    category = request.args.get('category')
    
    query = GridAsset.query.filter_by(is_active=True)
    
    if category:
        query = query.filter_by(category=category)
    
    assets = query.order_by(GridAsset.category, GridAsset.name).all()
    return jsonify([asset.to_dict() for asset in assets])


@assets_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get all available asset categories."""
    categories = db.session.query(GridAsset.category).distinct().filter(
        GridAsset.is_active == True
    ).order_by(GridAsset.category).all()
    
    return jsonify([cat[0] for cat in categories])


@assets_bp.route('/<int:asset_id>', methods=['GET'])
def get_asset(asset_id):
    """Get a specific asset by ID."""
    asset = GridAsset.query.get_or_404(asset_id)
    return jsonify(asset.to_dict())


@assets_bp.route('', methods=['POST'])
def create_asset():
    """Create a new grid asset (admin only)."""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['name', 'category', 'file_path']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Check if file exists
    asset_file = os.path.join(
        current_app.static_folder,
        'assets',
        data['file_path']
    )
    if not os.path.exists(asset_file):
        return jsonify({'error': 'Asset file not found'}), 400
    
    asset = GridAsset(
        name=data['name'],
        description=data.get('description', ''),
        category=data['category'],
        file_path=data['file_path'],
        width=data.get('width', 50),
        height=data.get('height', 50),
        is_passable=data.get('is_passable', True),
        color_tag=data.get('color_tag', '#888888')
    )
    
    db.session.add(asset)
    db.session.commit()
    
    return jsonify(asset.to_dict()), 201


@assets_bp.route('/<int:asset_id>', methods=['PUT'])
def update_asset(asset_id):
    """Update an existing asset (admin only)."""
    asset = GridAsset.query.get_or_404(asset_id)
    data = request.get_json()
    
    # Update fields
    if 'name' in data:
        asset.name = data['name']
    if 'description' in data:
        asset.description = data['description']
    if 'width' in data:
        asset.width = data['width']
    if 'height' in data:
        asset.height = data['height']
    if 'is_passable' in data:
        asset.is_passable = data['is_passable']
    if 'color_tag' in data:
        asset.color_tag = data['color_tag']
    if 'is_active' in data:
        asset.is_active = data['is_active']
    
    db.session.commit()
    return jsonify(asset.to_dict())


@assets_bp.route('/<int:asset_id>', methods=['DELETE'])
def delete_asset(asset_id):
    """Delete/deactivate an asset (admin only)."""
    asset = GridAsset.query.get_or_404(asset_id)
    asset.is_active = False
    db.session.commit()
    return '', 204


# ===== PLACED ASSETS ENDPOINTS =====

@assets_bp.route('/placed/<grid_code>', methods=['GET'])
def get_placed_assets(grid_code):
    """Get all placed assets on a specific grid."""
    assets = PlacedAsset.query.filter_by(grid_code=grid_code).all()
    return jsonify([asset.to_dict() for asset in assets])


@assets_bp.route('/placed', methods=['POST'])
def create_placed_asset():
    """Place a new asset on a grid."""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['grid_code', 'asset_path', 'x', 'y']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    placed_asset = PlacedAsset(
        grid_code=data['grid_code'],
        asset_path=data['asset_path'],
        x=data['x'],
        y=data['y'],
        width=data.get('width', 50),
        height=data.get('height', 50),
        rotation=data.get('rotation', 0)
    )
    
    db.session.add(placed_asset)
    db.session.commit()
    
    return jsonify(placed_asset.to_dict()), 201


@assets_bp.route('/placed/<int:placed_asset_id>', methods=['PUT'])
def update_placed_asset(placed_asset_id):
    """Update a placed asset (position, rotation, etc.)."""
    asset = PlacedAsset.query.get_or_404(placed_asset_id)
    data = request.get_json()
    
    if 'x' in data:
        asset.x = data['x']
    if 'y' in data:
        asset.y = data['y']
    if 'width' in data:
        asset.width = data['width']
    if 'height' in data:
        asset.height = data['height']
    if 'rotation' in data:
        asset.rotation = data['rotation']
    
    db.session.commit()
    return jsonify(asset.to_dict())


@assets_bp.route('/placed/<int:placed_asset_id>', methods=['DELETE'])
def delete_placed_asset(placed_asset_id):
    """Remove a placed asset from a grid."""
    asset = PlacedAsset.query.get_or_404(placed_asset_id)
    db.session.delete(asset)
    db.session.commit()
    return '', 204
