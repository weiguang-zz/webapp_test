import asyncio
import json
import websockets

# Store rooms and their clients
# Structure: { roomId: Set(websocket) }
rooms = {}

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
    if not room_id:
        return current_room_id

    # Leave previous room if any
    if current_room_id:
        await handle_leave(websocket, current_room_id)

    if room_id not in rooms:
        rooms[room_id] = set()
        print(f"Room {room_id} created")

    rooms[room_id].add(websocket)
    print(f"Client joined room {room_id}")
    
    await websocket.send(json.dumps({
        'type': 'system',
        'payload': {'text': f'Joined room {room_id}'}
    }))
    
    return room_id

async def handle_leave(websocket, room_id):
    if room_id in rooms:
        rooms[room_id].discard(websocket)
        if not rooms[room_id]:
            del rooms[room_id]
            print(f"Room {room_id} deleted (empty)")
        else:
            # Optional: Notify others
            await broadcast_to_room(room_id, {
                'type': 'system',
                'payload': {'text': 'A user left the room'}
            })

async def handle_message(websocket, payload, room_id):
    if not room_id or room_id not in rooms:
        return

    text = payload.get('text')
    print(f"Message in {room_id}: {text}")
    
    await broadcast_to_room(room_id, {
        'type': 'message',
        'payload': {'text': text, 'sender': 'User'}
    })

async def broadcast_to_room(room_id, data):
    if room_id not in rooms:
        return
    
    message_str = json.dumps(data)
    # Create a list of tasks to send messages to all clients in the room
    # websockets.broadcast is available in newer versions, but manual loop is safer for compatibility
    clients = rooms[room_id]
    if clients:
        await asyncio.gather(
            *[client.send(message_str) for client in clients],
            return_exceptions=True
        )



async def main():
    # Run in insecure mode
    async with websockets.serve(
        handler,
        "0.0.0.0",
        8090,
        create_protocol=websockets.server.WebSocketServerProtocol
    ):
        print("WebSocket server started on port 8090 (ws://)")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
