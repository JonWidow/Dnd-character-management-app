# models/__init__.py
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

# Import models so SQLAlchemy registers mappers once db exists
# (order chosen to make secondary table names available)
from .character_struct import CharacterClassModel, SubclassModel, SubclassFeature, CharacterClassFeature, RaceModel, RaceFeature  # noqa: F401
from .user import User  # noqa: F401
from .character import Character  # noqa: F401
from .spell import Spell  # noqa: F401
from .encounter import Encounter, CombatParticipant  # noqa: F401
from .skill import Skill
from .spell_slots import ClassSpellSlots, CharacterSpellSlot  # noqa: F401
