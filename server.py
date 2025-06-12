from flask import Flask, send_from_directory
from flask_socketio import SocketIO, join_room, leave_room, emit
from pyngrok import ngrok

# Inicia túnel ngrok na porta 5000
public_url = ngrok.connect(5000)
print(f" * Ngrok tunnel URL: {public_url}")

app = Flask(__name__, static_folder='public')
socketio = SocketIO(app, cors_allowed_origins='*', async_mode='threading')

# rooms: cada sala guarda task, votos, flag revealed, lista de participantes
rooms = {}

@app.route('/')
def index():
    return send_from_directory('public', 'index.html')

@app.route('/<path:path>')
def serve(path):
    return send_from_directory('public', path)

@socketio.on('join')
def on_join(data):
    room = data['room']
    user = data['user']
    join_room(room)
    if room not in rooms:
        rooms[room] = {'task':'', 'votes':{}, 'revealed':False, 'participants':[]}
    if user not in rooms[room]['participants']:
        rooms[room]['participants'].append(user)
    emit_room_data(room)

@socketio.on('leave')
def on_leave(data):
    room = data['room']
    user = data['user']
    leave_room(room)
    if room in rooms:
        rooms[room]['participants'] = [u for u in rooms[room]['participants'] if u!=user]
        rooms[room]['votes'].pop(user, None)
        emit_room_data(room)

@socketio.on('set_task')
def on_set_task(data):
    room = data['room']
    task = data['task']
    rooms[room]['task'] = task
    rooms[room]['votes'] = {}
    rooms[room]['revealed'] = False
    emit_room_data(room)

@socketio.on('vote')
def on_vote(data):
    room = data['room']
    user = data['user']
    value = data['value']
    rooms[room]['votes'][user] = value
    emit_room_data(room)

@socketio.on('reveal')
def on_reveal(data):
    room = data['room']
    rooms[room]['revealed'] = True
    emit_room_data(room)

@socketio.on('reset')
def on_reset(data):
    room = data['room']
    rooms[room]['task'] = ''
    rooms[room]['votes'] = {}
    rooms[room]['revealed'] = False
    emit_room_data(room)

# Função auxiliar para emitir estado completo da sala
def emit_room_data(room):
    state = rooms[room]
    payload = {
        'task': state['task'],
        'participants': state['participants'],
        'voted': list(state['votes'].keys()),
        'votes': state['votes'] if state['revealed'] else {},
        'revealed': state['revealed']
    }
    emit('room_data', payload, to=room)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)