from . import db
from app.models import CharacterClassModel

class ClassSpellSlots(db.Model):
    __tablename__ = "class_spell_slots"

    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey("character_classes.id"), nullable=False)
    class_level = db.Column(db.Integer, nullable=False)

    slot_1 = db.Column(db.Integer, default=0)
    slot_2 = db.Column(db.Integer, default=0)
    slot_3 = db.Column(db.Integer, default=0)
    slot_4 = db.Column(db.Integer, default=0)
    slot_5 = db.Column(db.Integer, default=0)
    slot_6 = db.Column(db.Integer, default=0)
    slot_7 = db.Column(db.Integer, default=0)
    slot_8 = db.Column(db.Integer, default=0)
    slot_9 = db.Column(db.Integer, default=0)

    # Optional relationship for easier joins
    character_class = db.relationship("CharacterClassModel", backref="spell_slot_tables")


class CharacterSpellSlot(db.Model):
    __tablename__ = "character_spell_slots"
    __table_args__ = (
        db.Index("idx_character_level", "character_id", "level"),
    )

    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey("character.id"), nullable=False)
    level = db.Column(db.Integer, nullable=False)  # Spell level (1..9)
    total_slots = db.Column(db.Integer, nullable=False, default=0)  # Total slots for this level
    remaining_slots = db.Column(db.Integer, nullable=False, default=0)  # Slots remaining

    # Relationship back to character
    character = db.relationship("Character", backref=db.backref("spell_slots", cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<CharacterSpellSlot char_id={self.character_id} level={self.level} total={self.total_slots} remaining={self.remaining_slots}>"

    def use_slot(self, amount=1):
        """Consume spell slots of this level."""
        if self.remaining_slots >= amount:
            self.remaining_slots -= amount
            return True
        return False

    def recover_slot(self, amount=1):
        """Recover spell slots of this level, up to total_slots."""
        self.remaining_slots = min(self.total_slots, self.remaining_slots + amount)

    def reset_slots(self):
        """Reset all remaining slots to total slots (e.g., after a long rest)."""
        self.remaining_slots = self.total_slots

