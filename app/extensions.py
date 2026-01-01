# extensions.py
from flask_socketio import SocketIO

# Single socketio instance for the whole app
socketio = SocketIO(async_mode="eventlet", cors_allowed_origins="*")
