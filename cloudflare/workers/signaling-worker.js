// Cloudflare Worker for WebRTC Signaling
export default {
  async fetch(request, env) {
    const upgradeHeader = request.headers.get('Upgrade');
    
    if (upgradeHeader && upgradeHeader === 'websocket') {
      return handleWebSocket(request, env);
    }
    
    return new Response('Expected WebSocket connection', { status: 400 });
  }
};

async function handleWebSocket(request, env) {
  const webSocketPair = new WebSocketPair();
  const [client, server] = webSocketPair;
  
  const url = new URL(request.url);
  const roomId = url.pathname.split('/')[1] || 'default';
  
  server.accept();
  
  console.log(`Client connected to room: ${roomId}`);
  
  // Store client in room (simplified)
  if (!env.ROOMS) {
    env.ROOMS = new Map();
  }
  
  const roomClients = env.ROOMS.get(roomId) || [];
  roomClients.push(server);
  env.ROOMS.set(roomId, roomClients);
  
  server.addEventListener('message', async (event) => {
    try {
      const data = JSON.parse(event.data);
      console.log(`Received message from ${data.senderId}: ${data.type}`);
      
      const message = {
        type: data.type,
        payload: data.payload,
        senderId: data.senderId
      };
      
      // Broadcast to all other clients in room
      roomClients.forEach((client, index) => {
        if (client !== server && client.readyState === WebSocket.OPEN) {
          client.send(JSON.stringify(message));
        }
      });
    } catch (err) {
      console.error('Error processing message:', err);
    }
  });
  
  server.addEventListener('close', () => {
    console.log(`Client disconnected from room: ${roomId}`);
    const roomClients = env.ROOMS.get(roomId) || [];
    const index = roomClients.indexOf(server);
    if (index > -1) {
      roomClients.splice(index, 1);
    }
    env.ROOMS.set(roomId, roomClients);
  });
  
  return new Response(null, {
    status: 101,
    webSocket: client
  });
}