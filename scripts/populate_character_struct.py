#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import db, app
from app.models.character_struct import CharacterClassModel, RaceModel

with app.app_context():
    db.create_all()
    print("Database tables created.")
    print("Note: Character Classes and Races are populated via populate_character_classes.py and populate_races.py")
    print("Subclasses are populated via populate_subclass.py")
    print("Spells are populated via populate_spells.py")
