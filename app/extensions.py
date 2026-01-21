# extensions.py
from flask_socketio import SocketIO

# Single socketio instance for the whole app
socketio = SocketIO(
    async_mode="threading",
    cors_allowed_origins="*",
    ping_timeout=10,
    ping_interval=5
)

