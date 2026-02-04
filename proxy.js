
const http = require('http');
const httpProxy = require('http-proxy');

const proxy = httpProxy.createProxyServer({});

const server = http.createServer((req, res) => {
  proxy.web(req, res, { target: 'http://127.0.0.1:18789' });
});

server.listen(8080, () => {
  console.log('Proxy server running on port 8080 -> 18789');
});

