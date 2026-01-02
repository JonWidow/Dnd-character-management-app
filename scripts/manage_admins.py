#!/usr/bin/env python3
"""
Script to manage admin users.
Can check existing admins and promote/demote users.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from app.models import db, User

def list_admins():
    with app.app_context():
        admins = User.query.filter_by(is_admin=True).all()
        if admins:
            print("Current admin users:")
            for admin in admins:
                print(f"  - {admin.username} (ID: {admin.id})")
        else:
            print("No admin users found.")
        return admins

def make_admin(username):
    with app.app_context():
        user = User.get_by_username(username)
        if not user:
            print(f"✗ User '{username}' not found.")
            return False
        
        if user.is_admin:
            print(f"✓ {username} is already an admin.")
            return True
        
        user.is_admin = True
        db.session.commit()
        print(f"✓ {username} is now an admin!")
        return True

def remove_admin(username):
    with app.app_context():
        user = User.get_by_username(username)
        if not user:
            print(f"✗ User '{username}' not found.")
            return False
        
        if not user.is_admin:
            print(f"✓ {username} is not an admin.")
            return True
        
        user.is_admin = False
        db.session.commit()
        print(f"✓ {username} is no longer an admin.")
        return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python manage_admins.py <command> [username]")
        print("Commands:")
        print("  list          - List all admin users")
        print("  make <user>   - Make user an admin")
        print("  remove <user> - Remove admin from user")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "list":
        list_admins()
    elif command == "make" and len(sys.argv) > 2:
        make_admin(sys.argv[2])
    elif command == "remove" and len(sys.argv) > 2:
        remove_admin(sys.argv[2])
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
