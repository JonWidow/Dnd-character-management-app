#!/usr/bin/env python3
"""Populate spell slots for all spellcasting classes."""

import sys
sys.path.insert(0, '/opt/dnd')

from app import app, db
from app.models.spell_slots import ClassSpellSlots
from app.models.character_struct import CharacterClassModel

# D&D 5e spell slot progressions
FULL_CASTER_SLOTS = {
    1:  [2,0,0,0,0,0,0,0,0],
    2:  [3,0,0,0,0,0,0,0,0],
    3:  [4,2,0,0,0,0,0,0,0],
    4:  [4,3,0,0,0,0,0,0,0],
    5:  [4,3,2,0,0,0,0,0,0],
    6:  [4,3,3,0,0,0,0,0,0],
    7:  [4,3,3,1,0,0,0,0,0],
    8:  [4,3,3,2,0,0,0,0,0],
    9:  [4,3,3,3,1,0,0,0,0],
    10: [4,3,3,3,2,0,0,0,0],
    11: [4,3,3,3,2,1,0,0,0],
    12: [4,3,3,3,2,1,0,0,0],
    13: [4,3,3,3,2,1,1,0,0],
    14: [4,3,3,3,2,1,1,0,0],
    15: [4,3,3,3,2,1,1,1,0],
    16: [4,3,3,3,2,1,1,1,0],
    17: [4,3,3,3,2,1,1,1,1],
    18: [4,3,3,3,3,1,1,1,1],
    19: [4,3,3,3,3,2,1,1,1],
    20: [4,3,3,3,3,2,2,1,1],
}

HALF_CASTER_SLOTS = {
    1:  [0,0,0,0,0,0,0,0,0],
    2:  [2,0,0,0,0,0,0,0,0],
    3:  [3,0,0,0,0,0,0,0,0],
    4:  [3,0,0,0,0,0,0,0,0],
    5:  [4,2,0,0,0,0,0,0,0],
    6:  [4,2,0,0,0,0,0,0,0],
    7:  [4,3,0,0,0,0,0,0,0],
    8:  [4,3,0,0,0,0,0,0,0],
    9:  [4,3,2,0,0,0,0,0,0],
    10: [4,3,2,0,0,0,0,0,0],
    11: [4,3,3,0,0,0,0,0,0],
    12: [4,3,3,0,0,0,0,0,0],
    13: [4,3,3,1,0,0,0,0,0],
    14: [4,3,3,1,0,0,0,0,0],
    15: [4,3,3,2,0,0,0,0,0],
    16: [4,3,3,2,0,0,0,0,0],
    17: [4,3,3,3,1,0,0,0,0],
    18: [4,3,3,3,1,0,0,0,0],
    19: [4,3,3,3,2,0,0,0,0],
    20: [4,3,3,3,2,0,0,0,0],
}

WARLOCK_SLOTS = {
    1:  [1,0,0,0,0,0,0,0,0],
    2:  [2,0,0,0,0,0,0,0,0],
    3:  [2,0,0,0,0,0,0,0,0],
    4:  [2,0,0,0,0,0,0,0,0],
    5:  [2,2,0,0,0,0,0,0,0],
    6:  [2,2,0,0,0,0,0,0,0],
    7:  [2,2,2,0,0,0,0,0,0],
    8:  [2,2,2,0,0,0,0,0,0],
    9:  [2,2,2,2,0,0,0,0,0],
    10: [2,2,2,2,0,0,0,0,0],
    11: [3,3,3,3,1,0,0,0,0],
    12: [3,3,3,3,1,0,0,0,0],
    13: [3,3,3,3,2,0,0,0,0],
    14: [3,3,3,3,2,0,0,0,0],
    15: [3,3,3,3,3,0,0,0,0],
    16: [3,3,3,3,3,0,0,0,0],
    17: [4,4,4,4,3,2,0,0,0],
    18: [4,4,4,4,3,2,0,0,0],
    19: [4,4,4,4,3,2,1,0,0],
    20: [4,4,4,4,3,2,1,0,0],
}

def populate_for_class(class_name, slots_dict):
    cls = CharacterClassModel.query.filter_by(name=class_name).first()
    if not cls:
        print(f"Class {class_name} not found!")
        return
    
    # Delete existing
    ClassSpellSlots.query.filter_by(class_id=cls.id).delete()
    
    for level, slots in slots_dict.items():
        row = ClassSpellSlots(
            class_id=cls.id,
            class_level=level,
            slot_1=slots[0], slot_2=slots[1], slot_3=slots[2],
            slot_4=slots[3], slot_5=slots[4], slot_6=slots[5],
            slot_7=slots[6], slot_8=slots[7], slot_9=slots[8]
        )
        db.session.add(row)
    
    db.session.commit()
    print(f"✓ Populated {class_name}")

if __name__ == "__main__":
    with app.app_context():
        populate_for_class("Wizard", FULL_CASTER_SLOTS)
        populate_for_class("Cleric", FULL_CASTER_SLOTS)
        populate_for_class("Druid", FULL_CASTER_SLOTS)
        populate_for_class("Bard", FULL_CASTER_SLOTS)
        populate_for_class("Sorcerer", FULL_CASTER_SLOTS)
        
        populate_for_class("Paladin", HALF_CASTER_SLOTS)
        populate_for_class("Ranger", HALF_CASTER_SLOTS)
        
        populate_for_class("Warlock", WARLOCK_SLOTS)
        
        print("✓ All spell slots populated!")
