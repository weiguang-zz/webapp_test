const WebSocket = require('ws');

const wss = new WebSocket.Server({ port: 8080 });

// Store rooms and their clients
// Structure: { roomId: Set(ws) }
const rooms = new Map();

wss.on('connection', (ws) => {
  console.log('New client connected');
  ws.roomId = null;

  ws.on('message', (message) => {
    try {
      const data = JSON.parse(message);
      const { type, payload } = data;

      switch (type) {
        case 'join':
          handleJoin(ws, payload);
          break;
        case 'message':
          handleMessage(ws, payload);
          break;
        default:
          console.warn('Unknown message type:', type);
      }
    } catch (e) {
      console.error('Failed to parse message:', e);
    }
  });

  ws.on('close', () => {
    if (ws.roomId && rooms.has(ws.roomId)) {
      const room = rooms.get(ws.roomId);
      room.delete(ws);
      if (room.size === 0) {
        rooms.delete(ws.roomId);
        console.log(`Room ${ws.roomId} deleted (empty)`);
      } else {
         // Optional: Notify others that user left
         broadcastToRoom(ws.roomId, {
             type: 'system',
             payload: { text: 'A user left the room' }
         });
      }
      console.log(`Client disconnected from room ${ws.roomId}`);
    }
  });
});

function handleJoin(ws, { roomId }) {
  if (!roomId) return;

  // Leave previous room if any
  if (ws.roomId && rooms.has(ws.roomId)) {
      rooms.get(ws.roomId).delete(ws);
  }

  if (!rooms.has(roomId)) {
    rooms.set(roomId, new Set());
    console.log(`Room ${roomId} created`);
  }

  const room = rooms.get(roomId);
  room.add(ws);
  ws.roomId = roomId;

  console.log(`Client joined room ${roomId}`);
  
  ws.send(JSON.stringify({
    type: 'system',
    payload: { text: `Joined room ${roomId}` }
  }));
}

function handleMessage(ws, { text }) {
  if (!ws.roomId || !rooms.has(ws.roomId)) return;

  console.log(`Message in ${ws.roomId}: ${text}`);
  
  broadcastToRoom(ws.roomId, {
    type: 'message',
    payload: { text, sender: 'User' } // In a real app, we'd have user IDs
  });
}

function broadcastToRoom(roomId, data) {
    if (!rooms.has(roomId)) return;
    
    const messageStr = JSON.stringify(data);
    rooms.get(roomId).forEach(client => {
        if (client.readyState === WebSocket.OPEN) {
            client.send(messageStr);
        }
    });
}

console.log('WebSocket server started on port 8080');
