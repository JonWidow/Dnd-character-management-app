#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import sqlite3
import time
import json
from datetime import datetime

DB_PATH = "instance/characters.db"
API_URL = "https://www.dnd5eapi.co/api/spells"
LOG_FILE = "populate_spells.log"

# Map class names to IDs for the spell_classes relation
CLASS_NAME_TO_ID = {
    "Barbarian": 1,
    "Bard": 2,
    "Cleric": 3,
    "Druid": 4,
    "Fighter": 5,
    "Monk": 6,
    "Paladin": 7,
    "Ranger": 8,
    "Rogue": 9,
    "Sorcerer": 10,
    "Warlock": 11,
    "Wizard": 12,
}

def log(message):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {message}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def get_json(url):
    for attempt in range(3):
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                return r.json()
            else:
                log(f"HTTP {r.status_code} for {url}")
        except requests.exceptions.RequestException as e:
            log(f"Attempt {attempt+1}/3 failed for {url}: {e}")
            time.sleep(2)
    log(f"Failed to fetch {url}")
    return None

def main():
    log("=== Spell population started ===")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Create tables
    c.execute("""
        CREATE TABLE IF NOT EXISTS spell (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            level INTEGER,
            school TEXT,
            casting_time TEXT,
            range TEXT,
            duration TEXT,
            description TEXT,
            higher_level TEXT,
            components TEXT,
            material TEXT,
            ritual BOOLEAN,
            concentration BOOLEAN,
            attack_type TEXT,
            damage TEXT,
            classes TEXT,
            subclasses TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS spell_classes (
            spell_id INTEGER,
            class_id INTEGER,
            PRIMARY KEY (spell_id, class_id)
        )
    """)

    spell_list = get_json(API_URL)
    if not spell_list:
        log("Could not retrieve spell list. Exiting.")
        return

    total = len(spell_list["results"])
    log(f"Retrieved {total} spells total.")

    success, fail = 0, 0

    for i, spell_info in enumerate(spell_list["results"], start=1):
        name = spell_info["name"]
        log(f"({i}/{total}) Fetching details for: {name}")

        details = get_json(f"https://www.dnd5eapi.co{spell_info['url']}")
        if not details:
            fail += 1
            continue

        try:
            spell_data = (
                details.get("name"),
                details.get("level"),
                (details.get("school") or {}).get("name"),
                details.get("casting_time"),
                details.get("range"),
                details.get("duration"),
                "\n".join(details.get("desc", [])),
                "\n".join(details.get("higher_level", [])),
                ", ".join(details.get("components", [])) if details.get("components") else None,
                details.get("material"),
                details.get("ritual"),
                details.get("concentration"),
                details.get("attack_type"),
                (details.get("damage") or {}).get("damage_type", {}).get("name"),
                ", ".join([c["name"] for c in details.get("classes", [])]),
                ", ".join([s["name"] for s in details.get("subclasses", [])])
            )

            c.execute("""
                INSERT OR IGNORE INTO spell (
                    name, level, school, casting_time, range, duration,
                    description, higher_level, components, material,
                    ritual, concentration, attack_type, damage, classes, subclasses
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, spell_data)

            spell_id = c.lastrowid

            # Populate spell_classes table
            for cls in details.get("classes", []):
                class_name = cls["name"]
                class_id = CLASS_NAME_TO_ID.get(class_name)
                if class_id and spell_id:
                    c.execute("INSERT OR IGNORE INTO spell_classes (spell_id, class_id) VALUES (?, ?)",
                              (spell_id, class_id))

            success += 1

        except Exception as e:
            log(f"Error inserting {name}: {e}")
            fail += 1

        if i % 10 == 0:
            conn.commit()
            log(f"Progress saved ({i}/{total})")

        time.sleep(0.2)

    conn.commit()
    conn.close()
    log(f"=== Spell population complete ===")
    log(f"Successful: {success}, Failed: {fail}, Total: {total}")

if __name__ == "__main__":
    main()
