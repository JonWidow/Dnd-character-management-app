#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# Add parent directory to path so we can import 'app'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from typing import Dict, Any
from app import app, db
from app.models.character_struct import CharacterClassModel, SubclassModel
from sqlalchemy import func
from api_utils import get_json, API_ROOT, DEFAULT_SLEEP

SLEEP = DEFAULT_SLEEP


def upsert_subclass(class_row: CharacterClassModel, name: str, description: str | None):
    """Idempotently create/update a SubclassModel."""
    existing = (
        SubclassModel.query
        .filter(SubclassModel.class_id == class_row.id)
        .filter(func.lower(SubclassModel.name) == name.lower())
        .first()
    )
    if existing is None:
        db.session.add(SubclassModel(
            name=name.strip(),
            description=description,
            character_class=class_row
        ))
        return True  # created
    else:
        # Update if description changed
        if (existing.description or "") != (description or ""):
            existing.description = description
        return False  # updated


def fetch_and_seed_subclasses_for(class_row: CharacterClassModel, class_index: str):
    """Fetch subclasses from D&D 5e API for a given class."""
    url = f"{API_ROOT}/api/classes/{class_index}/subclasses"
    data = get_json(url)
    if not data or "results" not in data:
        return 0
    
    created = 0
    for sub in data["results"]:
        sub_name = sub.get("name", "").strip()
        if not sub_name:
            continue
        
        # Fetch full subclass details for description
        sub_detail = get_json(f"{API_ROOT}{sub.get('url', '')}")
        sub_desc = None
        if sub_detail:
            # description is usually a list of strings
            desc_list = sub_detail.get("desc") or []
            sub_desc = "\n".join(desc_list) if isinstance(desc_list, list) else (desc_list or None)
        
        if upsert_subclass(class_row, sub_name, sub_desc):
            created += 1
        
        time.sleep(SLEEP)
    
    return created


def main():
    with app.app_context():
        print("DB:", db.engine.url)
        
        # Wipe existing subclasses
        print("Clearing existing subclasses...")
        SubclassModel.query.delete()
        db.session.commit()
        print("Subclasses cleared.")
        
        # Fetch all classes from our database
        classes = CharacterClassModel.query.order_by(CharacterClassModel.name).all()
        print(f"Found {len(classes)} classes in database")
        
        total = 0
        for i, cls_row in enumerate(classes, start=1):
            class_name = cls_row.name
            class_index = class_name.lower().replace(" ", "-")
            
            print(f"({i}/{len(classes)}) {class_name}")
            created = fetch_and_seed_subclasses_for(cls_row, class_index)
            
            if created:
                print(f"  → +{created} subclasses")
                total += created
            else:
                print(f"  → no subclasses found")
            
            db.session.commit()
            time.sleep(SLEEP)
        
        print(f"\n[DONE] Populated {total} subclasses.")
        print("[NOTE] The D&D 5e API free tier only includes 1 subclass per class.")


if __name__ == "__main__":
    main()
