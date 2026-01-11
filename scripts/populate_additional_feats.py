#!/usr/bin/env python3
"""Populate additional feats manually (since the API only has 1 feat)."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from app.models import Feat

# Common D&D 5e feats with their descriptions
FEATS = [
    {
        "name": "Able Mind",
        "description": "Your mind grows sharper with practice.\n\nWhen you gain proficiency in a skill, you can practice your skills to improve your understanding. You gain proficiency in one Intelligence check of your choice.",
        "prerequisites": []
    },
    {
        "name": "Actor",
        "description": "Skilled at mimicry and dramatics, you gain the following benefits:\n\n• Increase your Charisma score by 1, to a maximum of 20.\n• You have advantage on Charisma (Deception) and Charisma (Performance) checks when trying to act in character.\n• You can mimic the speech of another person or the sounds made by other creatures. You must have heard the person speaking, or heard the creature make the sound, for at least 1 minute. A successful Wisdom (Insight) check opposed by your Charisma (Deception) check allows a listener to determine that the effect is faked.",
        "prerequisites": []
    },
    {
        "name": "Alert",
        "description": "Always on the lookout for danger, you gain the following benefits:\n\n• You gain a +5 bonus to initiative.\n• You can't be surprised while you are conscious.\n• Other creatures don't gain advantage on attack rolls against you as a result of being unseen by you.",
        "prerequisites": []
    },
    {
        "name": "Athlete",
        "description": "You have undergone extensive physical training to gain the following benefits:\n\n• Increase your Strength or Dexterity score by 1, to a maximum of 20.\n• When you are prone, standing up uses only 5 feet of your movement.\n• Climbing doesn't cost you extra movement.\n• You can make a running long jump or a running high jump after moving only 5 feet on foot, rather than 10 feet.",
        "prerequisites": []
    },
    {
        "name": "Charmer",
        "description": "You've mastered the art of charming others. You gain the following benefits:\n\n• Increase your Charisma score by 1, to a maximum of 20.\n• Whenever you gain proficiency in the Persuasion skill, treat your proficiency bonus as double for any ability check you make with it.\n• When you make a Charisma (Persuasion) check, you gain advantage on the check if you or your allies aren't fighting any of the creatures you're trying to persuade. If you or your allies are fighting them, you have disadvantage on the check.",
        "prerequisites": []
    },
    {
        "name": "Crossbow Expert",
        "description": "Thanks to extensive practice with the crossbow, you gain these benefits:\n\n• You ignore the loading quality of crossbows with which you are proficient.\n• Being within 5 feet of a hostile creature doesn't impose disadvantage on your ranged attack rolls.\n• When you engage in two-weapon fighting, you can use a hand crossbow.",
        "prerequisites": []
    },
    {
        "name": "Defensive Duelist",
        "description": "When you are wielding a finesse weapon with which you are proficient and another creature hits you with a melee attack, you can use your reaction to add your proficiency bonus to your AC for that attack, potentially causing the attack to miss you.",
        "prerequisites": [{"ability_score": "Dexterity", "minimum_score": 13}]
    },
    {
        "name": "Durable",
        "description": "Hardy and resilient, you gain the following benefits:\n\n• Increase your Constitution score by 1, to a maximum of 20.\n• When you roll a Hit Die to regain hit points, the minimum number of hit points you regain from the roll is twice your Constitution modifier (minimum of 2).",
        "prerequisites": []
    },
    {
        "name": "Dungeon Delver",
        "description": "Alert to the hidden traps and secret doors found in many dungeons, you gain these benefits:\n\n• You have advantage on Wisdom (Perception) and Intelligence (Investigation) checks made to detect the presence of secret doors.\n• You have advantage on saving throws made to avoid or resist traps.\n• You have resistance to the damage dealt by traps.\n• Traveling at a fast pace doesn't impose the normal -5 penalty on your passive Wisdom (Perception) score.",
        "prerequisites": []
    },
    {
        "name": "Elemental Adept",
        "description": "When you gain this feat, choose one of the following damage types: acid, cold, fire, lightning, or thunder.\n\nSpells you cast ignore resistance to damage of the chosen type. In addition, when you roll damage for a spell you cast that deals damage of that type, you can treat any 1 on a damage die as a 2.\n\nYou can select this feat multiple times. Each time you do so, you must choose a different damage type.",
        "prerequisites": [{"requirement": "Spellcasting ability"}]
    },
    {
        "name": "Exceptional Aim",
        "description": "You have a knack for hitting where it counts. You gain the following benefits:\n\n• Increase your Dexterity score by 1, to a maximum of 20.\n• When you score a critical hit with a weapon attack, you gain a bonus to that weapon's damage roll equal to your Dexterity modifier.",
        "prerequisites": []
    },
    {
        "name": "Fey Touched",
        "description": "Your exposure to the Feywild's magic has changed you. You gain the following benefits:\n\n• Increase your Intelligence, Wisdom, or Charisma score by 1, to a maximum of 20.\n• You learn the misty step spell and one 1st-level spell of your choice. The 1st-level spell must be from the divination or enchantment school of magic. You can cast each of these spells without expending a spell slot. Once you cast either spell this way, you can't cast that spell this way again until you finish a short or long rest. You can cast these spells using spell slots you have of the appropriate level.\n• Your spellcasting ability for these spells depends on which ability you increased by 1: if you increased your Intelligence, Wisdom, or Charisma, your spellcasting ability for these spells is that ability.",
        "prerequisites": []
    },
    {
        "name": "Fey Wanderer",
        "description": "Your travels have taken you to the Feywild and its mysterious depths. You gain the following benefits:\n\n• Increase your Intelligence or Wisdom score by 1, to a maximum of 20.\n• You learn the speak with animals spell and one 1st-level spell of your choice. The 1st-level spell must be from the divination or enchantment school of magic. You can cast each of these spells without expending a spell slot. Once you cast either spell this way, you can't cast that spell this way again until you finish a short or long rest. You can cast these spells using spell slots you have of the appropriate level.",
        "prerequisites": []
    },
    {
        "name": "Great Weapon Master",
        "description": "You've learned to put the weight of a weapon to your advantage, letting its momentum empower your strikes. You gain the following benefits:\n\n• On your turn, when you score a critical hit with a melee weapon or reduce a creature to 0 hit points with one, you can make one melee weapon attack as a bonus action.\n• Before you make a melee attack with a heavy weapon that you are proficient with, you can choose to take a -5 penalty to the attack roll. If the attack hits, you add +10 to the attack's damage roll.",
        "prerequisites": []
    },
    {
        "name": "Healer",
        "description": "You are an able physician, allowing you to mend wounds quickly and get the sick back on their feet. You gain the following benefits:\n\n• When you use a healer's kit to stabilize a dying creature, that creature also regains 1 hit point.\n• As an action, you can spend one use of a healer's kit to tend to a creature and restore 1d6 + 4 hit points to it, up to its hit point maximum. A creature can benefit from this action only once every 24 hours.",
        "prerequisites": []
    },
    {
        "name": "Telepathic",
        "description": "You awaken the telepathic power within yourself. You gain the following benefits:\n\n• Increase your Intelligence, Wisdom, or Charisma score by 1, to a maximum of 20.\n• You can speak telepathically to any creature you can see within 60 feet of you. Your telepathic utterances are silent, and you speak directly into the creature's mind.\n• When you cast a divination spell, you can use a bonus action on the same turn you cast the spell to sense the presence of magic of the divination school within 30 feet of you. This benefit doesn't reveal the presence of actual divination magic from your own casts.",
        "prerequisites": []
    },
    {
        "name": "War Caster",
        "description": "You have practiced casting spells in the midst of combat, learning techniques that grant you the following benefits:\n\n• You have advantage on Constitution saving throws that you make to maintain your concentration on a spell when you take damage.\n• You can perform the somatic components of spells even when you have weapons or a shield in one or both hands.\n• When a hostile creature's movement provokes an opportunity attack from you, you can use your reaction to cast a spell at the creature, rather than making an opportunity attack. The spell must have a casting time of 1 action and must target only that creature.",
        "prerequisites": [{"requirement": "Spellcasting ability"}]
    },
    {
        "name": "Weapon Master",
        "description": "You have practiced extensively with a variety of weapons, gaining the following benefits:\n\n• Increase your Strength or Dexterity score by 1, to a maximum of 20.\n• You gain proficiency with four weapons of your choice. Each one must be a simple or martial weapon. If it's a martial weapon, it must lack the heavy property.",
        "prerequisites": []
    },
    {
        "name": "Polearm Master",
        "description": "You can keep your enemies at bay with reach weapons. You gain the following benefits:\n\n• When you take the Attack action and attack with only a glaive, halberd, pike, quarterstaff, or spear, you can use a bonus action to make a melee attack with the opposite end of the weapon. The weapon's damage die for this attack is a d4, and it deals bludgeoning damage.\n• While you are wielding a glaive, halberd, pike, quarterstaff, or spear, other creatures provoke an opportunity attack from you when they enter the reach you have with that weapon.",
        "prerequisites": []
    },
    {
        "name": "Sentinel",
        "description": "You have mastered the handyman's tools, granting you the following benefits:\n\n• When a creature you can see moves into a space within 5 feet of you, you can use your reaction to make a melee weapon attack against that creature.\n• When you hit a creature with an opportunity attack, the creature's speed is reduced to 0 for the rest of the turn.\n• Disarm attempts made against you have disadvantage.\n• When a creature makes an attack against you, you can use your reaction to make a melee weapon attack against that creature.",
        "prerequisites": []
    },
]

def populate_feats():
    with app.app_context():
        print("Populating common D&D 5e feats...")
        
        added_count = 0
        updated_count = 0
        
        for feat_data in FEATS:
            name = feat_data["name"]
            existing = Feat.query.filter_by(name=name).first()
            
            if existing:
                # Update existing
                existing.description = feat_data["description"]
                existing.prerequisites = feat_data["prerequisites"]
                updated_count += 1
                print(f"  ↻ {name}")
            else:
                # Create new
                feat = Feat(
                    name=name,
                    description=feat_data["description"],
                    prerequisites=feat_data["prerequisites"]
                )
                db.session.add(feat)
                added_count += 1
                print(f"  ✓ {name}")
        
        db.session.commit()
        print(f"\n✓ Successfully added {added_count} new feats and updated {updated_count}!")
        
        total = Feat.query.count()
        print(f"Total feats in database: {total}")

if __name__ == "__main__":
    populate_feats()
