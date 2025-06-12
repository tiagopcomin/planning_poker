from flask import Flask, send_from_directory
from flask_socketio import SocketIO, join_room, emit

app = Flask(__name__, static_folder='public')
# Usando threading para assincronismo leve
socketio = SocketIO(app, cors_allowed_origins='*', async_mode='threading')

rooms = {}  # estado simples: map de salas para votos

@app.route('/')
def index():
    return send_from_directory('public', 'index.html')

@app.route('/<path:path>')
def serve(path):
    return send_from_directory('public', path)

@socketio.on('join')
def on_join(data):
    room = data['room']
    join_room(room)
    rooms.setdefault(room, {})
    emit('state', rooms[room], to=room)

@socketio.on('vote')
def on_vote(data):
    room = data['room']
    user = data['user']
    value = data['value']
    rooms.setdefault(room, {})[user] = value
    emit('state', rooms[room], to=room)

@socketio.on('reset')
def on_reset(data):
    room = data['room']
    rooms[room] = {}
    emit('state', rooms[room], to=room)

if __name__ == '__main__':
    # host 0.0.0.0 para aceitar conexões externas
    socketio.run(app, host='0.0.0.0', port=5000)