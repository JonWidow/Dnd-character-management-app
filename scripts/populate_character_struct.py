from app import db, app
from models.character_struct import CharacterClass, Race

with app.app_context():
    db.create_all()

    # Populate Character Classes
    if not CharacterClass.query.first():
        for cls_data in CharacterClass.base_classes():
            db.session.add(CharacterClass(**cls_data))
        print("Character classes added.")

    # Populate Races
    if not Race.query.first():
        for race_data in Race.base_races():
            db.session.add(Race(**race_data))
        print("Races added.")

    db.session.commit()
    print("Done.")
