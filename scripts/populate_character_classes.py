#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from typing import Dict, Any, List
from app import app, db
from sqlalchemy import func
from app.models.character_struct import CharacterClassModel, CharacterClassFeature
from api_utils import get_json, API_ROOT, DEFAULT_SLEEP

CLASSES_URL = f"{API_ROOT}/api/classes"

# PHB-style: which character classes actually PREPARE spells (vs know list)
PREPARES_SPELLS = {
    "Cleric": True,
    "Druid": True,
    "Paladin": True,
    "Wizard": True,
    # The rest either don't cast or use "spells known": Bard, Sorcerer, Warlock, Ranger, etc.
}

# polite rate limit
SLEEP = DEFAULT_SLEEP


def upsert_class(row: Dict[str, Any]) -> CharacterClassModel:
    """
    Idempotently create/update a CharacterClassModel by name (case-insensitive).
    Expected row keys: name, hit_die, spellcasting_ability(str|None), prepares_spells(bool), description(str|None)
    """
    name = row["name"].strip()
    existing = (
        CharacterClassModel.query
        .filter(func.lower(CharacterClassModel.name) == name.lower())
        .first()
    )
    if existing is None:
        existing = CharacterClassModel(
            name=name,
            hit_die=row["hit_die"],
            spellcasting_ability=row.get("spellcasting_ability"),
            prepares_spells=bool(row.get("prepares_spells", False)),
            description=row.get("description")
        )
        db.session.add(existing)
    else:
        # keep it up to date in case API/schema values change
        existing.hit_die = row["hit_die"]
        existing.spellcasting_ability = row.get("spellcasting_ability")
        existing.prepares_spells = bool(row.get("prepares_spells", False))
        existing.description = row.get("description")
    return existing


def upsert_feature(cls_row: CharacterClassModel, name: str, level: int, description: str | None):
    """
    Idempotently create/update a CharacterClassFeature for (class_id, name, level).
    """
    q = (
        CharacterClassFeature.query
        .filter(CharacterClassFeature.class_id == cls_row.id)
        .filter(func.lower(CharacterClassFeature.name) == name.lower())
        .filter(CharacterClassFeature.level == level)
    )
    existing = q.first()
    if existing is None:
        db.session.add(CharacterClassFeature(
            name=name.strip(),
            level=int(level),
            description=description,
            character_class=cls_row
        ))
    else:
        # gentle update if description changed
        if (existing.description or "") != (description or ""):
            existing.description = description


def fetch_and_seed_class(class_stub: Dict[str, Any]):
    """
    Given a class stub from /api/classes (e.g., {"index":"wizard","name":"Wizard","url":"/api/classes/wizard"}),
    fetch details, spellcasting, levels->features and seed.
    """
    name = class_stub["name"]
    index = class_stub["index"]

    # /api/classes/{index}
    detail = get_json(f"{API_ROOT}{class_stub['url']}")
    if not detail:
        print(f"[WARN] Skipping {name}: no detail")
        return

    # Base fields
    hit_die = detail.get("hit_die")
    # description isn't provided by the class endpoint; keep None for now (or synthesize)
    description = None

    # /api/classes/{index}/spellcasting (may 404 for non-casters)
    spellcasting = get_json(f"{API_ROOT}/api/classes/{index}/spellcasting")
    spellcasting_ability = None
    if spellcasting and spellcasting.get("spellcasting_ability"):
        spellcasting_ability = (spellcasting["spellcasting_ability"].get("name") or "").upper()[:3] or None

    # prepares_spells by known PHB rule (API doesn’t expose this directly in a consistent way)
    prepares_spells = PREPARES_SPELLS.get(name, False)

    # Upsert class row
    cls_row = upsert_class({
        "name": name,
        "hit_die": f"d{hit_die}" if isinstance(hit_die, int) else (hit_die or "d8"),
        "spellcasting_ability": spellcasting_ability,
        "prepares_spells": prepares_spells,
        "description": description
    })
    db.session.flush()  # ensure cls_row.id

    # Clear existing features for this class (since we’re reseeding fresh)
    CharacterClassFeature.query.filter_by(class_id=cls_row.id).delete()

    # /api/classes/{index}/levels → contains feature refs per level
    levels = get_json(f"{API_ROOT}/api/classes/{index}/levels")
    if not levels or not isinstance(levels, list):
        print(f"[INFO] No levels data for {name}")
        return

    inserted = 0
    for lvl in levels:
        lvl_num = lvl.get("level")
        feats: List[Dict[str, Any]] = lvl.get("features") or []
        if not feats:
            continue
        for feat in feats:
            # follow each feature link to get the full description
            feat_detail = get_json(f"{API_ROOT}{feat['url']}")
            if not feat_detail:
                continue
            feat_name = feat_detail.get("name") or feat.get("name") or "Unnamed Feature"
            # desc is usually a list of strings
            desc_list = feat_detail.get("desc") or []
            feat_desc = "\n".join(desc_list) if isinstance(desc_list, list) else (desc_list or None)
            upsert_feature(cls_row, feat_name, int(lvl_num), feat_desc)
            inserted += 1
            time.sleep(SLEEP)

    if inserted:
        print(f"[OK] {name}: {inserted} features")
    else:
        print(f"[INFO] {name}: no features found")


def main():
    with app.app_context():
        print("DB:", db.engine.url)

        # Start fresh (classes + features only)
        CharacterClassFeature.query.delete()
        CharacterClassModel.query.delete()
        db.session.commit()

        # Fetch class list
        data = get_json(CLASSES_URL)
        if not data or "results" not in data:
            print("[ERROR] Could not fetch classes list")
            return

        classes = data["results"]
        total = len(classes)
        print(f"Found {total} classes in API")

        for i, stub in enumerate(classes, start=1):
            print(f"({i}/{total}) {stub['name']}")
            fetch_and_seed_class(stub)
            db.session.commit()
            time.sleep(SLEEP)

        print("[DONE] Classes & features populated.")


if __name__ == "__main__":
    main()
