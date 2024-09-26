from flask import Flask, request
from flask_socketio import SocketIO
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])  # Autorise l'origine localhost:3000
socketio = SocketIO(app, cors_allowed_origins=["http://localhost:3000"])

@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")

@socketio.on('message')
def handle_message(msg):
    print(f"Message reçu : {msg['message']}")
    socketio.emit('message', {"message": {"text": "test"}}, room=request.sid)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
