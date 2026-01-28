#!/usr/bin/env python3
"""
Migration script to add chooses_spells_to_know column to character_classes table
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from sqlalchemy import inspect, text

with app.app_context():
    # Check if column already exists
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns('character_classes')]
    
    if 'chooses_spells_to_know' in columns:
        print("Column 'chooses_spells_to_know' already exists.")
    else:
        # Add the column
        print("Adding 'chooses_spells_to_know' column...")
        with db.engine.begin() as connection:
            connection.execute(text('ALTER TABLE character_classes ADD COLUMN chooses_spells_to_know BOOLEAN DEFAULT 0'))
        print("✓ Column added successfully")
        
        # Set specific classes to TRUE
        classes_that_choose = ['Bard', 'Sorcerer', 'Warlock', 'Wizard']
        for class_name in classes_that_choose:
            with db.engine.begin() as connection:
                connection.execute(text(f"UPDATE character_classes SET chooses_spells_to_know = 1 WHERE name = '{class_name}'"))
            print(f"✓ Set {class_name} to choose spells")
        
        print("\n✓ Migration complete!")
