from . import db

class Spell(db.Model):
    __tablename__ = 'spell'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    level = db.Column(db.Integer, nullable=False)
    school = db.Column(db.String(64))
    casting_time = db.Column(db.String(64))
    range = db.Column(db.String(64))
    duration = db.Column(db.String(64))
    description = db.Column(db.Text)
    higher_level = db.Column(db.Text)
    components = db.Column(db.String(64))
    material = db.Column(db.Text)
    ritual = db.Column(db.Boolean, default=False)
    concentration = db.Column(db.Boolean, default=False)
    attack_type = db.Column(db.String(64))
    damage = db.Column(db.Text)
    subclasses = db.Column(db.String(128))  # flattened names list from the API (optional)

    # CharacterClassModel <-> Spell
    classes = db.relationship('CharacterClassModel', secondary='spell_classes', back_populates='spells')

    # Character <-> Spell (known spells)
    known_by = db.relationship('Character', secondary='character_spells', back_populates='spells')

    # reverse of Character.prepared_spells
    prepared_by = db.relationship('Character', secondary='character_prepared_spells', back_populates='prepared_spells'    )


    # Convenience, not shadowing the relationship:
    @property
    def class_names(self):
        return ', '.join(c.name for c in self.classes)

    def to_dict(self):
        d = {col.name: getattr(self, col.name) for col in self.__table__.columns}
        d['classes'] = [c.name for c in self.classes]
        return d
