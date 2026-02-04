const http = require('http');
const crypto = require('crypto');

function hashWebSocketKey(key) {
  return crypto
    .createHash('sha1')
    .update(key + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11')
    .digest('base64');
}

const server = http.createServer((req, res) => {
  console.log('HTTP request:', req.method, req.url);
  
  // Simple health check
  if (req.url === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'ok', service: 'websocket-proxy' }));
    return;
  }
  
  // Forward HTTP requests
  const options = {
    hostname: '127.0.0.1',
    port: 18789,
    path: req.url,
    method: req.method,
    headers: req.headers
  };

  const proxyReq = http.request(options, (proxyRes) => {
    res.writeHead(proxyRes.statusCode, proxyRes.headers);
    proxyRes.pipe(res, { end: true });
  });

  req.pipe(proxyReq, { end: true });
  
  proxyReq.on('error', (err) => {
    console.error('Proxy error:', err);
    res.writeHead(502);
    res.end('Bad Gateway');
  });
});

server.on('upgrade', (req, socket, head) => {
  console.log('WebSocket upgrade request:', req.url, req.headers['sec-websocket-key']);
  
  // Validate WebSocket handshake
  const key = req.headers['sec-websocket-key'];
  if (!key) {
    socket.destroy();
    return;
  }

  // Connect to backend
  const backendSocket = require('net').connect(18789, '127.0.0.1', () => {
    // Send the WebSocket upgrade response to client
    const acceptKey = hashWebSocketKey(key);
    const headers = [
      'HTTP/1.1 101 Switching Protocols',
      'Upgrade: websocket',
      'Connection: Upgrade',
      `Sec-WebSocket-Accept: ${acceptKey}`,
      '', ''
    ].join('\r\n');
    
    socket.write(headers);
    
    // Pipe data between client and backend
    backendSocket.write(head);
    backendSocket.pipe(socket);
    socket.pipe(backendSocket);
    
    console.log('WebSocket tunnel established');
  });

  backendSocket.on('error', (err) => {
    console.error('Backend socket error:', err);
    socket.destroy();
  });

  socket.on('error', (err) => {
    console.error('Client socket error:', err);
    backendSocket.destroy();
  });

  socket.on('close', () => {
    backendSocket.destroy();
  });

  backendSocket.on('close', () => {
    socket.destroy();
  });
});

server.listen(8080, () => {
  console.log('WebSocket proxy listening on port 8080');
  console.log('Forwarding to OpenClaw gateway on port 18789');
});