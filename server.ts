import express from 'express';
import http from 'node:http';
import { spawn, type ChildProcess } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const currentDir = path.dirname(fileURLToPath(import.meta.url));
const root = path.basename(currentDir) === 'dist' ? path.resolve(currentDir, '..') : currentDir;
const port = Number(process.env.PORT || 3000);
const backendPort = Number(process.env.BACKEND_PORT || 8001);
const backend = `http://127.0.0.1:${backendPort}`;
const origin = process.env.PUBLIC_ORIGIN || `http://127.0.0.1:${port}`;
const python = process.env.PYTHON_BIN || (process.platform === 'win32' ? 'python' : 'python3');
const app = express();
app.disable('x-powered-by');
app.use((_req, res, next) => {
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('Referrer-Policy', 'same-origin');
  res.setHeader('Cache-Control', 'no-store');
  res.setHeader('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self'; media-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'");
  next();
});
let child: ChildProcess | undefined;

function unavailable(res: express.Response) {
  res.status(503).json({ error: 'Serviço clínico indisponível. Tente novamente em instantes.' });
}

app.use('/api', (req, res) => {
  if (req.method === 'POST' && req.headers.origin !== origin) {
    res.status(403).json({ error: 'Origem não permitida.' });
    return;
  }
  const headers: http.OutgoingHttpHeaders = { ...req.headers, host: `127.0.0.1:${backendPort}` };
  delete headers.connection;
  if (req.headers.origin) headers.origin = origin;
  const upstream = http.request(`${backend}${req.originalUrl}`, { method: req.method, headers }, response => {
    res.status(response.statusCode || 502);
    for (const [name, value] of Object.entries(response.headers)) {
      if (value !== undefined && !['connection', 'transfer-encoding'].includes(name)) res.setHeader(name, value);
    }
    response.pipe(res);
  });
  upstream.on('error', () => unavailable(res));
  req.pipe(upstream);
});

app.use('/media', (req, res) => {
  const upstream = http.request(`${backend}${req.originalUrl}`, {
    method: req.method,
    headers: { cookie: req.headers.cookie, range: req.headers.range },
  }, response => {
    res.status(response.statusCode || 502);
    for (const [name, value] of Object.entries(response.headers)) {
      if (value !== undefined && !['connection', 'transfer-encoding'].includes(name)) res.setHeader(name, value);
    }
    response.pipe(res);
  });
  upstream.on('error', () => unavailable(res));
  req.pipe(upstream);
});

app.use(express.static(path.join(root, 'web')));
app.get('*', (_req, res) => res.sendFile(path.join(root, 'web', 'index.html')));

child = spawn(python, [path.join(root, 'server.py'), '--port', String(backendPort)], {
  cwd: root,
  env: { ...process.env, APP_ORIGIN: origin },
  stdio: ['ignore', 'inherit', 'inherit'],
});
child.on('error', error => console.error('Falha ao iniciar serviço clínico:', error));
const server = app.listen(port, '0.0.0.0', () => console.log(`App em ${port}; API clínica em ${backendPort}`));

function shutdown() {
  child?.kill();
  server.close(() => process.exit(0));
}
process.on('SIGTERM', shutdown);
process.on('SIGINT', shutdown);
process.on('message', message => { if (message === 'shutdown') shutdown(); });
