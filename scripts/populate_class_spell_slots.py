#!/usr/bin/env python3

from app import app
from models import db
from models.spell_slots import ClassSpellSlots
from models.character_struct import CharacterClassModel

# -----------------------------
# SPELL SLOT PROGRESSION DATA
# -----------------------------
# This example is for a FULL CASTER (e.g. Wizard, Cleric)
# Levels 120, spell slots 19

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
    20: [4,3,3,3,3,2,1,1,1],
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
    3:  [0,0,2,0,0,0,0,0,0],
    4:  [0,0,2,0,0,0,0,0,0],
    5:  [0,0,0,2,0,0,0,0,0],
    6:  [0,0,0,2,0,0,0,0,0],
    7:  [0,0,0,0,2,0,0,0,0],
    8:  [0,0,0,0,2,0,0,0,0],
    9:  [0,0,0,0,0,2,0,0,0],
    10: [0,0,0,0,0,2,0,0,0],
    11: [0,0,0,0,0,3,0,0,0],
    12: [0,0,0,0,0,3,0,0,0],
    13: [0,0,0,0,0,3,0,0,0],
    14: [0,0,0,0,0,3,0,0,0],
    15: [0,0,0,0,0,3,0,0,0],
    16: [0,0,0,0,0,3,0,0,0],
    17: [0,0,0,0,0,4,0,0,0],
    18: [0,0,0,0,0,4,0,0,0],
    19: [0,0,0,0,0,4,0,0,0],
    20: [0,0,0,0,0,4,0,0,0],
}

# Non-casters: everything 0
NON_CASTER_SLOTS = {lvl: [0]*9 for lvl in range(1, 21)}


# -----------------------------
# MAIN POPULATION LOGIC
# -----------------------------

def populate_for_class(class_name, slot_table):
    character_class = CharacterClassModel.query.filter_by(name=class_name).first()

    if not character_class:
        raise RuntimeError(f"Class '{class_name}' not found")

    for level, slots in slot_table.items():
        existing = ClassSpellSlots.query.filter_by(
            class_id=character_class.id,
            class_level=level
        ).first()

        if existing:
            continue  # skip if already populated

        row = ClassSpellSlots(
            class_id=character_class.id,
            class_level=level,
            slot_1=slots[0],
            slot_2=slots[1],
            slot_3=slots[2],
            slot_4=slots[3],
            slot_5=slots[4],
            slot_6=slots[5],
            slot_7=slots[6],
            slot_8=slots[7],
            slot_9=slots[8],
        )

        db.session.add(row)

    db.session.commit()
    print(f"Populated spell slots for {class_name}")


if __name__ == "__main__":
    with app.app_context():
        populate_for_class("Wizard", FULL_CASTER_SLOTS)
        populate_for_class("Cleric", FULL_CASTER_SLOTS)
        populate_for_class("Druid", FULL_CASTER_SLOTS)
        populate_for_class("Bard", FULL_CASTER_SLOTS)
        populate_for_class("Sorcerer", FULL_CASTER_SLOTS)

        populate_for_class("Paladin", HALF_CASTER_SLOTS)
        populate_for_class("Ranger", HALF_CASTER_SLOTS)

        populate_for_class("Barbarian",NON_CASTER_SLOTS)
        populate_for_class("Fighter",NON_CASTER_SLOTS)
        populate_for_class("Rogue",NON_CASTER_SLOTS)
        populate_for_class("Monk",NON_CASTER_SLOTS)

        populate_for_class("Warlock",WARLOCK_SLOTS)
