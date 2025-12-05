import asyncio
import json
import websockets
import os

# Store rooms and their clients
# Structure: { roomId: Set(websocket) }
rooms = {}

# Store chat history
# Structure: { roomId: [ { text, sender: {nickName, avatarUrl, userId} } ] }
history = {}

# Store room passwords
# Structure: { roomId: password }
room_passwords = {}

# Store client info
# Structure: { websocket: { nickName, avatarUrl, userId } }
clients = {}

DATA_FILE = 'data.json'

def load_data():
    global history, room_passwords
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                history = data.get('history', {})
                room_passwords = data.get('room_passwords', {})
                print(f"Loaded data from {DATA_FILE}")
        except Exception as e:
            print(f"Failed to load data: {e}")

def save_data():
    data = {
        'history': history,
        'room_passwords': room_passwords
    }
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Failed to save data: {e}")

async def handler(websocket):
    print("New client connected")
    current_room_id = None
    
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get('type')
                payload = data.get('payload')

                if msg_type == 'join':
                    current_room_id = await handle_join(websocket, payload, current_room_id)
                elif msg_type == 'message':
                    await handle_message(websocket, payload, current_room_id)
                else:
                    print(f"Unknown message type: {msg_type}")
            except json.JSONDecodeError:
                print("Failed to parse message")
            except Exception as e:
                print(f"Error handling message: {e}")

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        if current_room_id:
            await handle_leave(websocket, current_room_id)
        print("Client disconnected")

async def handle_join(websocket, payload, current_room_id):
    room_id = payload.get('roomId')
    password = payload.get('password')
    create_mode = payload.get('create', False)
    user_info = payload.get('userInfo', {})
    
    if not room_id:
        return current_room_id

    # Leave previous room if any
    if current_room_id:
        await handle_leave(websocket, current_room_id)

    # Strict Create/Join Logic
    # Check if room exists in memory OR persistence
    room_exists = room_id in rooms or room_id in room_passwords or room_id in history

    if create_mode:
        if room_exists:
            await websocket.send(json.dumps({
                'type': 'error',
                'payload': {'text': '房间已存在'}
            }))
            return None
        
        # Create new room
        # Password is optional for creation
        room_passwords[room_id] = password if password else ""
        save_data()
        print(f"Room {room_id} created (Password: {'Yes' if password else 'No'})")
        
        rooms[room_id] = set()
        if room_id not in history:
            history[room_id] = []
            
    else: # Join Mode
        if not room_exists:
            await websocket.send(json.dumps({
                'type': 'error',
                'payload': {'text': '房间不存在'}
            }))
            return None
        
        # Resurrect room if it exists in persistence but not active
        if room_id not in rooms:
            rooms[room_id] = set()
            print(f"Resurrected room {room_id} from persistence")
        
        # Check password
        stored_password = room_passwords.get(room_id, "")
        if stored_password and stored_password != password:
             await websocket.send(json.dumps({
                'type': 'error',
                'payload': {'text': '需要密码'}
            }))
             return None

    rooms[room_id].add(websocket)
    clients[websocket] = user_info
    print(f"Client joined room {room_id} with info: {user_info}")
    
    # Send history
    if history.get(room_id):
        await websocket.send(json.dumps({
            'type': 'history',
            'payload': history[room_id]
        }))
    
    await websocket.send(json.dumps({
        'type': 'system',
        'payload': {'text': f'Joined room {room_id}'}
    }))
    
    return room_id

async def handle_leave(websocket, room_id):
    if room_id in rooms:
        rooms[room_id].discard(websocket)
        if websocket in clients:
            del clients[websocket]
            
        if not rooms[room_id]:
            print(f"Room {room_id} is empty")
        else:
            # Optional: Notify others
            pass

async def handle_message(websocket, payload, room_id):
    if not room_id or room_id not in rooms:
        return

    text = payload.get('text')
    sender_info = clients.get(websocket, {'nickName': 'Unknown', 'userId': 'unknown'})
    
    print(f"Message in {room_id}: {text}, sender: {sender_info}")
    
    message_data = {
        'text': text,
        'sender': sender_info
    }
    
    # Store in history
    if room_id not in history:
        history[room_id] = []
    history[room_id].append(message_data)
    save_data()
    
    await broadcast_to_room(room_id, {
        'type': 'message',
        'payload': message_data
    })

async def broadcast_to_room(room_id, data):
    if room_id not in rooms:
        return
    
    message_str = json.dumps(data)
    clients_in_room = rooms[room_id]
    if clients_in_room:
        await asyncio.gather(
            *[client.send(message_str) for client in clients_in_room],
            return_exceptions=True
        )

async def main():
    load_data()
    # Run in insecure mode
    async with websockets.serve(
        handler, 
        "0.0.0.0", 
        8090,
    ):
        print("WebSocket server started on port 8090 (ws://)")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
