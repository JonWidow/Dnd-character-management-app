from . import db

class Skill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    ability_score = db.Column(db.String(10), nullable=False)
    description = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "ability_score": self.ability_score,
            "description": self.description
        }

# Skills dictionary
skills = {
    "str_sc": ["athletics"],
    "dex_sc": ["acrobatics", "stealth", "sleight_of_hand"],
    "int_sc": ["arcana", "history", "investigation", "nature", "religion"],
    "wis_sc": ["animal_handling", "insight", "medicine", "perception", "survival"],
    "cha_sc": ["deception", "intimidation", "performance", "persuasion"]
}

def populate_skills():
    for ability, skill_list in skills.items():
        for skill_name in skill_list:
            if not Skill.query.filter_by(name=skill_name).first():
                db.session.add(Skill(name=skill_name, ability_score=ability))
    db.session.commit()
