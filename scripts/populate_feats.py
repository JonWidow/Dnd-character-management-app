#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from app import app, db
from app.models import Feat, CharacterClassModel
from sqlalchemy import func
from api_utils import get_json, DEFAULT_SLEEP

API_URL = "https://www.dnd5eapi.co/api/feats"
SLEEP = DEFAULT_SLEEP

def upsert_feat(details):
    """Idempotently create/update a Feat."""
    name = details.get("name", "").strip()
    if not name:
        return None
    
    existing = Feat.query.filter(func.lower(Feat.name) == name.lower()).first()
    
    feat_data = {
        "name": name,
        "description": "\n".join(details.get("desc", [])) if details.get("desc") else None,
        "prerequisites": details.get("prerequisites", []),
    }
    
    if existing:
        # Update existing
        for key, value in feat_data.items():
            setattr(existing, key, value)
        return existing
    else:
        # Create new
        feat = Feat(**feat_data)
        db.session.add(feat)
        return feat

def populate_feats():
    with app.app_context():
        print("Fetching feats from D&D 5e API...")
        feats_list = get_json(API_URL)
        
        if not feats_list or 'results' not in feats_list:
            print("No feats found")
            return
        
        count = 0
        for feat_summary in feats_list['results']:
            feat_url = f"https://www.dnd5eapi.co{feat_summary['url']}"
            feat_details = get_json(feat_url)
            
            if feat_details:
                upsert_feat(feat_details)
                count += 1
                print(f"  ✓ {feat_summary['name']}")
            
            time.sleep(SLEEP)
        
        db.session.commit()
        print(f"\n✓ Successfully populated {count} feats!")

if __name__ == "__main__":
    populate_feats()
