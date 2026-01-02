#!/usr/bin/env python
"""
Reset a user's password (run in Docker container).

Usage:
    docker exec -it dnd-web python /app/scripts/reset_password.py <username> <new_password>

Example:
    docker exec -it dnd-web python /app/scripts/reset_password.py Widow myNewPassword123
"""

import sys
import os

# Add parent directory to path so we can import app
sys.path.insert(0, '/app')

from app import app, db
from app.models import User

def reset_password(username, new_password):
    """Reset password for a user."""
    with app.app_context():
        user = User.get_by_username(username)
        
        if not user:
            print(f"Error: User '{username}' not found.")
            return False
        
        user.set_password(new_password)
        db.session.commit()
        
        print(f"✓ Password reset for user '{user.username}'")
        return True

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: docker exec -it dnd-web python /app/scripts/reset_password.py <username> <new_password>")
        print("Example: docker exec -it dnd-web python /app/scripts/reset_password.py Widow myNewPassword123")
        sys.exit(1)
    
    username = sys.argv[1]
    new_password = sys.argv[2]
    
    if reset_password(username, new_password):
        sys.exit(0)
    else:
        sys.exit(1)
