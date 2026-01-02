#!/usr/bin/env python3
"""
Recalculate known spells for all characters.
Ensures that characters only know spells up to their max available spell level.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from app.models import db, Character, Spell


def recalculate_character_spells():
    with app.app_context():
        characters = Character.query.all()
        
        print("=" * 50)
        print("Step 1: Syncing spell slots for all characters")
        print("=" * 50)
        for char in characters:
            char.sync_spell_slots()
            print(f"✓ {char.name}: Synced spell slots")
        
        db.session.commit()
        print()
        
        print("=" * 50)
        print("Step 2: Recalculating known spells")
        print("=" * 50)
        for char in characters:
            # Get max spell level character has slots for
            max_spell_level = 0
            for slot in char.spell_slots:
                if slot.total_slots > 0:
                    max_spell_level = max(max_spell_level, slot.level)
            
            if max_spell_level == 0:
                # No spell slots, remove all spells
                char.spells = []
                print(f"✓ {char.name}: Removed all spells (no spell slots)")
            else:
                # Filter spells to only those up to max level
                valid_spells = [s for s in char.spells if s.level <= max_spell_level]
                removed_count = len(char.spells) - len(valid_spells)
                
                if removed_count > 0:
                    char.spells = valid_spells
                    print(f"✓ {char.name}: Removed {removed_count} spell(s) above level {max_spell_level}")
                else:
                    print(f"✓ {char.name}: All spells valid (max level {max_spell_level})")
        
        db.session.commit()
        print()
        print("=" * 50)
        print("✓ All characters recalculated!")
        print("=" * 50)


if __name__ == "__main__":
    recalculate_character_spells()
