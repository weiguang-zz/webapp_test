import asyncio
import json
import websockets

# Store rooms and their clients
# Structure: { roomId: Set(websocket) }
rooms = {}

# Store chat history
# Structure: { roomId: [ { text, sender: {nickName, avatarUrl, userId} } ] }
history = {}

# Store client info
# Structure: { websocket: { nickName, avatarUrl, userId } }
clients = {}

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
    user_info = payload.get('userInfo', {})
    
    if not room_id:
        return current_room_id

    # Leave previous room if any
    if current_room_id:
        await handle_leave(websocket, current_room_id)

    if room_id not in rooms:
        rooms[room_id] = set()
        history[room_id] = []
        print(f"Room {room_id} created")

    rooms[room_id].add(websocket)
    clients[websocket] = user_info
    print(f"Client joined room {room_id} as {user_info.get('nickName', 'Unknown')}")
    
    # Send history
    if history[room_id]:
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
            # Optional: Keep history for a while or delete? 
            # For now, we keep history in memory even if room is empty, 
            # until server restart or explicit cleanup logic.
            # del rooms[room_id]
            # del history[room_id]
            print(f"Room {room_id} is empty")
        else:
            # Optional: Notify others
            pass

async def handle_message(websocket, payload, room_id):
    if not room_id or room_id not in rooms:
        return

    text = payload.get('text')
    sender_info = clients.get(websocket, {'nickName': 'Unknown', 'userId': 'unknown'})
    
    print(f"Message in {room_id}: {text}")
    
    message_data = {
        'text': text,
        'sender': sender_info
    }
    
    # Store in history
    if room_id not in history:
        history[room_id] = []
    history[room_id].append(message_data)
    
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
    # Run in insecure mode
    async with websockets.serve(
        handler, 
        "0.0.0.0", 
        8090,
        # origins=None  # 或者干脆不写这个参数 + 加个参数 create_protocol=websockets.server.WebSocketServerProtocol
    ):
        print("WebSocket server started on port 8090 (ws://)")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
