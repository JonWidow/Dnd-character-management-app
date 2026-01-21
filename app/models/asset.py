"""Asset model for grid items like terrain, objects, and effects."""
from . import db
from datetime import datetime


class GridAsset(db.Model):
    """Grid assets like terrain tiles, objects, and visual effects."""
    
    __tablename__ = 'grid_asset'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    category = db.Column(db.String(50), nullable=False)  # 'terrain', 'object', 'effect'
    file_path = db.Column(db.String(255), nullable=False)  # Relative path from static/assets/
    width = db.Column(db.Integer, default=50)  # Size in pixels
    height = db.Column(db.Integer, default=50)
    is_passable = db.Column(db.Boolean, default=True)  # Can tokens move through it?
    color_tag = db.Column(db.String(20), default='#888888')  # Color for quick identification
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'file_path': self.file_path,
            'width': self.width,
            'height': self.height,
            'is_passable': self.is_passable,
            'color_tag': self.color_tag,
            'is_active': self.is_active
        }
    
    def __repr__(self):
        return f'<GridAsset {self.name} ({self.category})>'
