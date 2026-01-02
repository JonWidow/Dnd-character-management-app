#!/usr/bin/env python3
"""
Assign unowned characters to an admin user.
Useful for migrating existing characters to the new user system.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from app.models import db, Character, User

def assign_characters(username):
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"✗ User '{username}' not found.")
            return False
        
        # Find all characters with user_id = NULL
        unowned = Character.query.filter(Character.user_id == None).all()
        
        if not unowned:
            print("✓ All characters are already assigned to users.")
            return True
        
        count = len(unowned)
        for char in unowned:
            char.user_id = user.id
        
        db.session.commit()
        print(f"✓ Assigned {count} character(s) to {username}")
        return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python assign_characters.py <username>")
        print("Example: python assign_characters.py Widow")
        sys.exit(1)
    
    assign_characters(sys.argv[1])
