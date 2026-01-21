"""Blueprint for grid asset management."""
from flask import Blueprint, jsonify, request, current_app
from app.models import db
from app.models.asset import GridAsset
import os

assets_bp = Blueprint('assets', __name__, url_prefix='/api/assets')


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
