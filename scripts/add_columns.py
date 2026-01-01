from app import app, db
from models import Character

HIT_DIE = {"Fighter": 10, "Paladin": 10, "Rogue": 8, "Bard": 8, "Barbarian":12, "Monk":8, "Cleric":8, "Druid":8, "Ranger":10, "Sorcerer":6, "Warlock":8, "Wizard":6}

with app.app_context():
    for char in Character.query.all():
        char.hit_die = HIT_DIE.get(char.char_class, 6)
        char.max_hp = char.calculate_max_hp()
        char.current_hp = char.max_hp
        db.session.add(char)
    db.session.commit()
