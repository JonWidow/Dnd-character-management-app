#!/usr/bin/env python3
"""Add Dissonant Whispers spell to the database."""

import sys
sys.path.insert(0, '/opt/dnd')

from app import app, db
from app.models import Spell, CharacterClassModel

def add_dissonant_whispers():
    with app.app_context():
        # Check if spell already exists
        existing = Spell.query.filter_by(name="Dissonant Whispers").first()
        if existing:
            print("✓ Dissonant Whispers already exists in database")
            return
        
        # Create the spell with official D&D 5e stats
        spell = Spell(
            name="Dissonant Whispers",
            level=1,
            school="Enchantment",
            casting_time="1 action",
            range="60 feet",
            duration="Instantaneous",
            description="For each creature you can see within range, choose a creature you can see within range that it can hear. A creature can't choose itself. That creature must make a Wisdom saving throw. On a failed save, it takes 3d6 psychic damage and uses its reaction to move as far away from you as it can. On a successful save, it takes half as much damage and doesn't move away.",
            higher_level="When you cast this spell using a spell slot of 2nd level or higher, the damage increases by 1d6 for each slot level above 1st.",
            components="V",
            material=None,
            ritual=False,
            concentration=False,
            attack_type=None,
            damage="3d6 psychic",
            subclasses="Bard"
        )
        
        db.session.add(spell)
        db.session.commit()
        
        # Add it to Bard class
        bard = CharacterClassModel.query.filter_by(name="Bard").first()
        if bard:
            spell.classes.append(bard)
            db.session.commit()
            print(f"✓ Added Dissonant Whispers to Bard class")
        
        print(f"✓ Dissonant Whispers added successfully!")

if __name__ == "__main__":
    add_dissonant_whispers()
