# copy_character.py
from app import app, db
from models import Character

# Make sure app context is pushed
app.app_context().push()

def copy_character_full(character_id: int, new_name: str):
    char = Character.query.get(character_id)
    if not char:
        print("Character not found")
        return None

    # Copy main attributes
    new_char = Character(
        name=new_name,
        char_class=char.char_class,
        race=char.race,
        level=char.level,
        ability_scores=[char.str_sc, char.dex_sc, char.con_sc, char.int_sc, char.wis_sc, char.cha_sc]
    )
    
    # Copy additional fields
    new_char.notes = char.notes
    new_char.is_favorite = False  # Don't favorite the copy

    db.session.add(new_char)
    db.session.flush()  # assign new_char.id

    # Copy relationships
    for feat in char.features:
        new_char.features.append(feat)
    for spell in char.spells:
        new_char.spells.append(spell)
    for spell in char.prepared_spells:
        new_char.prepared_spells.append(spell)

    db.session.commit()
    print(f"Character copied! New ID: {new_char.id}")
    return new_char

if __name__ == "__main__":
    old_id = int(input("Enter character ID to copy: "))
    new_name = input("Enter name for the new character: ")
    copy_character_full(old_id, new_name)
