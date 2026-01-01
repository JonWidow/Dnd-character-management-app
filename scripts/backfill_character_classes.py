from app import app, db
from models import Character, CharacterClassModel

with app.app_context():
    for char in Character.query.all():
        if char.char_class_id is None:
            cls = CharacterClassModel.query.filter_by(
                name=char.char_class_name
            ).first()

            if not cls:
                print(f"Missing class for {char.name}: {char.char_class_name}")
                continue

            char.char_class = cls
            print(f"Linked {char.name} to {cls.name}")

    db.session.commit()
