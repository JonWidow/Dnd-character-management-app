from . import db

# secondary table is declared here, but others will reference it by string name
spell_classes = db.Table(
    'spell_classes',
    db.Column('spell_id', db.Integer, db.ForeignKey('spell.id'), primary_key=True),
    db.Column('class_id', db.Integer, db.ForeignKey('character_classes.id'), primary_key=True),
)

# Feats <-> Classes (many-to-many)
feat_classes = db.Table(
    'feat_classes',
    db.Column('feat_id', db.Integer, db.ForeignKey('feat.id'), primary_key=True),
    db.Column('class_id', db.Integer, db.ForeignKey('character_classes.id'), primary_key=True),
)

# Feats <-> Characters (many-to-many)
character_feats = db.Table(
    'character_feats',
    db.Column('character_id', db.Integer, db.ForeignKey('character.id'), primary_key=True),
    db.Column('feat_id', db.Integer, db.ForeignKey('feat.id'), primary_key=True),
)

class CharacterClassModel(db.Model):
    __tablename__ = 'character_classes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    hit_die = db.Column(db.Integer, nullable=False)
    spellcasting_ability = db.Column(db.String(3))
    prepares_spells = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text)
    subclass_unlock_level = db.Column(db.Integer, default=3)  # Most classes unlock at level 3
    
    # Proficiencies stored as JSON lists
    skill_proficiencies = db.Column(db.JSON, default=list)  # e.g., ["Acrobatics", "Athletics"]
    skill_choice_count = db.Column(db.Integer, default=0)  # How many skills to choose from the list
    armor_proficiencies = db.Column(db.JSON, default=list)  # e.g., ["light armor", "medium armor"]
    weapon_proficiencies = db.Column(db.JSON, default=list)  # e.g., ["simple melee weapons"]
    tool_proficiencies = db.Column(db.JSON, default=list)  # e.g., ["musical instruments"]
    saving_throw_proficiencies = db.Column(db.JSON, default=list)  # e.g., ["STR", "CON"]

    # IMPORTANT: name must be 'spells' to match Spell.classes back_populates
    spells = db.relationship('Spell', secondary='spell_classes', back_populates='classes')

    def features_up_to(self, level: int):
        return (self.features
                .filter(CharacterClassFeature.level <= level)
                .order_by(CharacterClassFeature.level.asc(), CharacterClassFeature.name.asc())
                .all())


class SubclassModel(db.Model):
    __tablename__ = 'subclasses'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text)

    # link to parent character class
    class_id = db.Column(db.Integer, db.ForeignKey('character_classes.id'), nullable=False)
    character_class = db.relationship(
        'CharacterClassModel',
        backref=db.backref('subclasses', lazy='dynamic', cascade='all, delete-orphan')
    )
    __table_args__ = (
       db.UniqueConstraint('class_id', 'name', name='uq_subclass_per_class'),
    )

    # Relationship to subclass features
    features = db.relationship(
        'SubclassFeature',
        backref='subclass',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )


class SubclassFeature(db.Model):
    __tablename__ = 'subclass_features'
    id = db.Column(db.Integer, primary_key=True)
    # e.g. "Empowered Evocation", "Arcane Recovery"
    name = db.Column(db.String(80), nullable=False)
    # Level the feature becomes available
    level = db.Column(db.Integer, nullable=False)
    # Full rules text
    description = db.Column(db.Text)
    # Uses, recharges etc
    uses = db.Column(db.String(32))
    # At higher levels
    scaling = db.Column(db.JSON, default=dict)
    # Link to the subclass this feature belongs to
    subclass_id = db.Column(db.Integer, db.ForeignKey('subclasses.id'), nullable=False)
    __table_args__ = (
        db.UniqueConstraint('subclass_id', 'name', 'level', name='uq_feature_per_subclass_level'),
    )
    # Lists feature's choices
    choices = db.Column(db.JSON, default=list)


class CharacterClassFeature(db.Model):
    __tablename__ = 'character_class_features'
    id = db.Column(db.Integer, primary_key=True)
    # e.g. "Action Surge", "Channel Divinity"
    name = db.Column(db.String(80), nullable=False)
    # Level the feature becomes available
    level = db.Column(db.Integer, nullable=False)
    # Full rules text
    description = db.Column(db.Text)
    # Uses, recharges etc
    uses = db.Column(db.String(32))
    # At higher levels
    scaling = db.Column(db.JSON, default=dict)
    # Link to the character class this feature belongs to
    class_id = db.Column(db.Integer, db.ForeignKey('character_classes.id'), nullable=False)
    character_class = db.relationship(
        'CharacterClassModel',
        backref=db.backref('features', lazy='dynamic', cascade='all, delete-orphan')
    )
    __table_args__ = (
        db.UniqueConstraint('class_id', 'name', 'level', name='uq_feature_per_class_level'),
    )

    # Lists feature's choices. Needs to be expanded upon.
    choices = db.Column(db.JSON, default=list)

    # Optional metadata you may want later:
             # e.g. "PB/day", "1/short rest"
    # 


class Feat(db.Model):
    __tablename__ = 'feat'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    description = db.Column(db.Text)
    prerequisites = db.Column(db.JSON, default=list)  # e.g., [{"ability_score": "STR", "minimum_score": 13}]
    
    # Relationships
    # Classes that can take this feat
    classes = db.relationship('CharacterClassModel', secondary='feat_classes', backref='available_feats')
    
    # Characters that have taken this feat
    known_by = db.relationship('Character', secondary='character_feats', backref='feats')
    
    def __repr__(self):
        return f"<Feat {self.name}>"


class RaceModel(db.Model):
    __tablename__ = 'races'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    speed = db.Column(db.Integer, nullable=False)
    ability_bonuses = db.Column(db.JSON, default=dict)  # e.g., {"STR":2,"CON":1}
    alignment = db.Column(db.Text)                       # "Half-orcs inherit a tendency toward chaos ..."
    age = db.Column(db.Text)                             # "Half-orcs mature a little faster than humans..."
    size = db.Column(db.String(20))                      # "Medium"
    size_description = db.Column(db.Text)               # "Half-orcs are somewhat larger and bulkier than humans..."
    languages = db.Column(db.JSON, default=list)        # list of {"name":..., "desc":...}
    description = db.Column(db.Text)                    # optional overall description
    url = db.Column(db.String(100))                     # store API URL if needed

    # link to race features (traits)
    features = db.relationship(
        'RaceFeature',
        backref='race',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    @staticmethod
    def id_to_name(race_id):
        race = RaceModel.query.get(race_id)
        return race.name if race else None

    @staticmethod
    def name_to_id(race_name):
        race = RaceModel.query.filter(
            db.func.lower(RaceModel.name) == race_name.lower()
        ).first()
        return race.id if race else None



class RaceFeature(db.Model):
    __tablename__ = 'race_features'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text)
    race_id = db.Column(db.Integer, db.ForeignKey('races.id'), nullable=False)
    additional_data = db.Column(db.JSON, default=dict)  # store things like scaling, uses, etc


class ClassLevel(db.Model):
    __tablename__ = 'class_levels'

    id = db.Column(db.Integer, primary_key=True)

    # Link to the class
    class_id = db.Column(db.Integer, db.ForeignKey('character_classes.id'), nullable=False)
    character_class = db.relationship(
        'CharacterClassModel',
        backref=db.backref('levels', lazy='dynamic', cascade='all, delete-orphan')
    )

    # Level number
    level = db.Column(db.Integer, nullable=False)

    # Proficiency bonus at this level
    proficiency_bonus = db.Column(db.Integer)

    # Spell slots at this level; JSON object with keys "1", "2", "3", etc.
    spell_slots = db.Column(db.JSON, default=dict)

    # Cantrips known (optional)
    cantrips_known = db.Column(db.Integer)

    # Spells known (optional)
    spells_known = db.Column(db.Integer)

    # Feature IDs (list of integers from CharacterClassFeature table)
    feature_ids = db.Column(db.JSON, default=list)

    # Subclass unlock flag
    unlocks_subclass = db.Column(db.Boolean, default=False)

    __table_args__ = (
        db.UniqueConstraint('class_id', 'level', name='uq_class_level'),
    )

    def __repr__(self):
        return f"<ClassLevel class_id={self.class_id} level={self.level}>"

    def get_features(self):
       # Returns CharacterClassFeature objects corresponding to feature_ids.

        if not self.feature_ids:
            return []
        return CharacterClassFeature.query.filter(
            CharacterClassFeature.id.in_(self.feature_ids)
        ).all()

    def grant_features_to_character(self, character):
        #Grants all features of this level to a character.
        #Assumes character has a method like character.add_feature(feature_obj)
        features = self.get_features()
        for f in features:
            character.add_feature(f)
