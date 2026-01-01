from app import app
from .extensions import socketio

if __name__ == "__main__":
    # Use socketio.run for Flask-SocketIO apps
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
