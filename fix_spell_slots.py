#!/usr/bin/env python3
"""
Fix spell slots in the database to match official D&D 5e rules.
All 9-level full casters have identical spell slot progression.
"""

import sys
sys.path.insert(0, '/app')

from app.run import app
from app.models.spell_slots import ClassSpellSlots
from app.models.character_struct import CharacterClassModel
from app import db

# Official D&D 5e spell slots for 9-level full casters (Wizard, Cleric, Druid, Sorcerer, Bard)
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

# Half-casters (Paladin, Ranger)
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

# Warlock (Pact Magic - different from standard spellcasting)
WARLOCK_SLOTS = {
    1:  [1,0,0,0,0,0,0,0,0],
    2:  [2,0,0,0,0,0,0,0,0],
    3:  [0,2,0,0,0,0,0,0,0],
    4:  [0,2,0,0,0,0,0,0,0],
    5:  [0,0,2,0,0,0,0,0,0],
    6:  [0,0,2,0,0,0,0,0,0],
    7:  [0,0,0,2,0,0,0,0,0],
    8:  [0,0,0,2,0,0,0,0,0],
    9:  [0,0,0,0,2,0,0,0,0],
    10: [0,0,0,0,2,0,0,0,0],
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

def fix_class_slots(class_name, slot_table):
    """Fix spell slots for a class"""
    char_class = CharacterClassModel.query.filter_by(name=class_name).first()
    if not char_class:
        print(f"  ❌ Class '{class_name}' not found")
        return
    
    fixed_count = 0
    for level, slots in slot_table.items():
        slot_row = ClassSpellSlots.query.filter_by(
            class_id=char_class.id,
            class_level=level
        ).first()
        
        if not slot_row:
            print(f"  ❌ Level {level} not found - creating...")
            slot_row = ClassSpellSlots(
                class_id=char_class.id,
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
            db.session.add(slot_row)
            fixed_count += 1
        else:
            # Check if slots match
            current = [slot_row.slot_1, slot_row.slot_2, slot_row.slot_3, slot_row.slot_4,
                      slot_row.slot_5, slot_row.slot_6, slot_row.slot_7, slot_row.slot_8, slot_row.slot_9]
            if current != slots:
                print(f"  ⚠️  Level {level}: {current} → {slots}")
                slot_row.slot_1 = slots[0]
                slot_row.slot_2 = slots[1]
                slot_row.slot_3 = slots[2]
                slot_row.slot_4 = slots[3]
                slot_row.slot_5 = slots[4]
                slot_row.slot_6 = slots[5]
                slot_row.slot_7 = slots[6]
                slot_row.slot_8 = slots[7]
                slot_row.slot_9 = slots[8]
                fixed_count += 1
    
    if fixed_count > 0:
        db.session.commit()
        print(f"  ✓ {class_name}: Fixed {fixed_count} levels")
    else:
        print(f"  ✓ {class_name}: All correct")

if __name__ == "__main__":
    with app.app_context():
        print("Checking and fixing D&D 5e spell slots...\n")
        
        print("Full Casters (Wizard, Cleric, Druid, Sorcerer, Bard):")
        fix_class_slots("Wizard", FULL_CASTER_SLOTS)
        fix_class_slots("Cleric", FULL_CASTER_SLOTS)
        fix_class_slots("Druid", FULL_CASTER_SLOTS)
        fix_class_slots("Sorcerer", FULL_CASTER_SLOTS)
        fix_class_slots("Bard", FULL_CASTER_SLOTS)
        
        print("\nHalf-Casters (Paladin, Ranger):")
        fix_class_slots("Paladin", HALF_CASTER_SLOTS)
        fix_class_slots("Ranger", HALF_CASTER_SLOTS)
        
        print("\nWarlock (Pact Magic):")
        fix_class_slots("Warlock", WARLOCK_SLOTS)
        
        print("\nDone!")
