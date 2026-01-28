#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from app import app, db
from app.models import Spell, CharacterClassModel
from sqlalchemy import func
from api_utils import get_json, DEFAULT_SLEEP

API_URL = "https://www.dnd5eapi.co/api/spells"
SLEEP = DEFAULT_SLEEP

def upsert_spell(details):
    """Idempotently create/update a Spell."""
    name = details.get("name", "").strip()
    if not name:
        return None
    
    existing = Spell.query.filter(func.lower(Spell.name) == name.lower()).first()
    
    spell_data = {
        "name": name,
        "level": details.get("level", 0),
        "school": (details.get("school") or {}).get("name"),
        "casting_time": details.get("casting_time"),
        "range": details.get("range"),
        "duration": details.get("duration"),
        "description": "\n".join(details.get("desc", [])),
        "higher_level": "\n".join(details.get("higher_level", [])) if details.get("higher_level") else None,
        "components": ", ".join(details.get("components", [])) if details.get("components") else None,
        "material": details.get("material"),
        "ritual": bool(details.get("ritual", False)),
        "concentration": bool(details.get("concentration", False)),
        "attack_type": details.get("attack_type"),
        "damage": (details.get("damage") or {}).get("damage_type", {}).get("name"),
        "subclasses": ", ".join([s["name"] for s in details.get("subclasses", [])]),
    }
    
    if existing is None:
        spell = Spell(**spell_data)
        db.session.add(spell)
        db.session.flush()  # to get the ID
    else:
        for key, val in spell_data.items():
            setattr(existing, key, val)
        spell = existing
    
    # Link to character classes via the spell_classes junction table
    spell.classes = []
    for cls in details.get("classes", []):
        class_name = cls["name"]
        class_row = CharacterClassModel.query.filter(
            func.lower(CharacterClassModel.name) == class_name.lower()
        ).first()
        if class_row:
            spell.classes.append(class_row)
    
    return spell

def main():
    print("=== Spell population started ===")
    
    with app.app_context():
        spell_list = get_json(API_URL)
        if not spell_list:
            print("Could not retrieve spell list. Exiting.")
            return

        total = len(spell_list.get("results", []))
        print(f"Retrieved {total} spells total.")

        success, fail = 0, 0

        for i, spell_info in enumerate(spell_list.get("results", []), start=1):
            name = spell_info["name"]
            print(f"({i}/{total}) Fetching details for: {name}")

            details = get_json(f"https://www.dnd5eapi.co{spell_info['url']}")
            if not details:
                fail += 1
                continue

            try:
                upsert_spell(details)
                success += 1
            except Exception as e:
                print(f"Error inserting {name}: {e}")
                fail += 1

            if i % 10 == 0:
                db.session.commit()
                print(f"Progress saved ({i}/{total})")

            time.sleep(SLEEP)

        db.session.commit()
        print(f"=== Spell population complete ===")
        print(f"Successful: {success}, Failed: {fail}, Total: {total}")

if __name__ == "__main__":
    main()
