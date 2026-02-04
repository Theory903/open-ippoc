
const http = require('http');
const net = require('net');

const server = http.createServer((req, res) => {
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
    res.writeHead(500);
    res.end('Proxy error');
  });
});

// Handle WebSocket upgrade
server.on('upgrade', (req, socket, head) => {
  const proxySocket = net.connect(18789, '127.0.0.1', () => {
    socket.write('HTTP/1.1 101 Switching Protocols
' +
                 'Upgrade: websocket
' +
                 'Connection: Upgrade
' +
                 '
');
    proxySocket.write(head);
    proxySocket.pipe(socket);
    socket.pipe(proxySocket);
  });
});

server.listen(8080, () => {
  console.log('Proxy server running on port 8080 -> 18789');
});

