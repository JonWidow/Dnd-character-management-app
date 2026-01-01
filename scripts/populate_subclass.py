# populate_subclass.py
from app import app, db  # use the SAME app/db as your web app
from models.character_struct import CharacterClassModel, SubclassModel
from sqlalchemy import func

def fetch_subclasses_for_class(class_name: str) -> list[dict]:
    """
    TODO: Replace with real API call.
    Return [{"name": "...", "description": "..."}, ...]
    """
    demo = {
        "Wizard": [{"name": "Evocation", "description": "Masters of damage magic"}],
        "Fighter": [{"name": "Champion", "description": "Improved critical"}],
        "Rogue": [{"name": "Thief", "description": "Fast Hands, Second-Story Work"}],
    }
    return demo.get(class_name, [])

def upsert_subclasses_for(class_row: CharacterClassModel):
    subs = fetch_subclasses_for_class(class_row.name)
    created = updated = 0
    for s in subs:
        sname = s["name"].strip()
        sdesc = s.get("description")
        existing = SubclassModel.query.filter(func.lower(SubclassModel.name) == sname.lower()).first()
        if existing:
            changed = False
            if existing.class_id != class_row.id:
                existing.class_id = class_row.id; changed = True
            if (existing.description or "") != (sdesc or ""):
                existing.description = sdesc; changed = True
            if changed:
                updated += 1
        else:
            db.session.add(SubclassModel(name=sname, description=sdesc, character_class=class_row))
            created += 1
    if created or updated:
        print(f"[OK] {class_row.name}: +{created} / ~{updated}")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # ensure tables exist with the new model
        for cls in CharacterClassModel.query.all():
            upsert_subclasses_for(cls)
        db.session.commit()
        print("Done.")
