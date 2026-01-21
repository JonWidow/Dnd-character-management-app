from . import db
from datetime import datetime

class Encounter(db.Model):
    __tablename__ = 'encounter'
    
    id = db.Column(db.Integer, primary_key=True)
    session_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='active')  # active, paused, complete
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    participants = db.relationship('CombatParticipant', cascade='all, delete-orphan', lazy=True, back_populates='encounter')
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_code': self.session_code,
            'name': self.name,
            'status': self.status,
            'participants': [p.to_dict() for p in self.participants]
        }


class CombatParticipant(db.Model):
    __tablename__ = 'combat_participant'
    
    id = db.Column(db.Integer, primary_key=True)
    encounter_id = db.Column(db.Integer, db.ForeignKey('encounter.id'), nullable=False)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    x = db.Column(db.Float, default=0)
    y = db.Column(db.Float, default=0)
    color = db.Column(db.String(7), default='#ff0000')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    character = db.relationship('Character', backref='tokens')
    encounter = db.relationship('Encounter', back_populates='participants')
    
    def to_dict(self):
        return {
            'id': self.id,
            'character_id': self.character_id,
            'name': self.name,
            'x': self.x,
            'y': self.y,
            'color': self.color
        }
