from flask import Flask, render_template
from flask_socketio import SocketIO
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])  # Autorise l'origine localhost:3000
socketio = SocketIO(app, cors_allowed_origins=["http://localhost:3000"])

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('message')
def handle_message(msg):
    print(f"Message reçu : {msg}")
    socketio.send(msg)  # renvoie le message à tous les clients

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
