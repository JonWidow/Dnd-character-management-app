#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import requests
from typing import Dict, Any, List
from app import app, db
from app.models.character_struct import RaceModel, RaceFeature
from sqlalchemy import func
from api_utils import get_json, API_ROOT, DEFAULT_SLEEP

RACES_URL = f"{API_ROOT}/api/races"
SLEEP = DEFAULT_SLEEP


def upsert_race(row: Dict[str, Any]) -> RaceModel:
    name = row["name"].strip()
    existing = (
        RaceModel.query
        .filter(func.lower(RaceModel.name) == name.lower())
        .first()
    )
    if existing is None:
        existing = RaceModel(
            name=name,
            speed=row.get("speed", 30),
            ability_bonuses=row.get("ability_bonuses", {}),
            alignment=row.get("alignment"),
            age=row.get("age"),
            size=row.get("size"),
            size_description=row.get("size_description"),
            languages=row.get("languages", []),
            description=row.get("description"),
            url=row.get("url"),
        )
        db.session.add(existing)
    else:
        # update existing fields
        for key in ["speed", "ability_bonuses", "alignment", "age", "size", "size_description", "languages", "description", "url"]:
            setattr(existing, key, row.get(key, getattr(existing, key)))
    return existing


def upsert_race_feature(race: RaceModel, name: str, description: str | None):
    existing = (
        RaceFeature.query
        .filter(RaceFeature.race_id == race.id)
        .filter(func.lower(RaceFeature.name) == name.lower())
        .first()
    )
    if existing is None:
        db.session.add(RaceFeature(
            name=name.strip(),
            description=description,
            race=race
        ))
    else:
        if (existing.description or "") != (description or ""):
            existing.description = description


def fetch_and_seed_race(race_stub: Dict[str, Any]):
    name = race_stub["name"]
    index = race_stub["index"]

    race_detail = get_json(f"{API_ROOT}{race_stub['url']}")
    if not race_detail:
        print(f"[WARN] Skipping {name}: no detail")
        return

    # ability bonuses
    ability_bonuses = {ab["ability_score"]["name"]: ab["bonus"] for ab in race_detail.get("ability_bonuses", [])}
    # languages
    languages = []
    for lang in race_detail.get("languages", []):
        lang_detail = get_json(f"{API_ROOT}{lang['url']}")
        lang_desc = lang_detail.get("desc") if lang_detail else None
        languages.append({"name": lang.get("name"), "desc": lang_desc})
        time.sleep(SLEEP)
    # description (general)
    desc_list = race_detail.get("desc") or []
    description = "\n".join(desc_list) if isinstance(desc_list, list) else (desc_list or None)

    race_row = upsert_race({
        "name": name,
        "speed": race_detail.get("speed", 30),
        "ability_bonuses": ability_bonuses,
        "alignment": race_detail.get("alignment"),
        "age": race_detail.get("age"),
        "size": race_detail.get("size"),
        "size_description": race_detail.get("size_description"),
        "languages": languages,
        "description": description,
        "url": race_detail.get("url"),
    })
    db.session.flush()

    # clear existing features
    RaceFeature.query.filter_by(race_id=race_row.id).delete()

    # fetch traits/features
    traits = race_detail.get("traits", [])
    inserted = 0
    for trait in traits:
        trait_detail = get_json(f"{API_ROOT}{trait['url']}")
        if not trait_detail:
            continue
        trait_name = trait_detail.get("name") or "Unnamed Trait"
        trait_desc_list = trait_detail.get("desc") or []
        trait_desc = "\n".join(trait_desc_list) if isinstance(trait_desc_list, list) else (trait_desc_list or None)
        upsert_race_feature(race_row, trait_name, trait_desc)
        inserted += 1
        time.sleep(SLEEP)

    if inserted:
        print(f"[OK] {name}: {inserted} features/traits")
    else:
        print(f"[INFO] {name}: no features/traits found")


def main():
    with app.app_context():
        print("DB:", db.engine.url)

        # Drop previous races and features
        RaceFeature.query.delete()
        RaceModel.query.delete()
        db.session.commit()

        # Fetch race list
        data = get_json(RACES_URL)
        if not data or "results" not in data:
            print("[ERROR] Could not fetch races list")
            return

        races = data["results"]
        total = len(races)
        print(f"Found {total} races in API")

        for i, stub in enumerate(races, start=1):
            print(f"({i}/{total}) {stub['name']}")
            fetch_and_seed_race(stub)
            db.session.commit()
            time.sleep(SLEEP)

        print("[DONE] Races & features populated.")


if __name__ == "__main__":
    main()
