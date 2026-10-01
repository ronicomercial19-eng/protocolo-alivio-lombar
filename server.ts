import express from 'express';
import path from 'node:path';
import fs from 'node:fs';
import http from 'node:http';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
const here = path.dirname(fileURLToPath(import.meta.url));
const root = fs.existsSync(path.join(here, 'server.py')) ? here : path.dirname(here);
const port = Number(process.env.PORT || 3000);
const backendPort = Number(process.env.BACKEND_PORT || 8001);
const internalOrigin = `http://127.0.0.1:${backendPort}`;
const app = express();
if (process.env.TRUST_PROXY === '1') app.set('trust proxy', 1);
let available = false;
// Run the persistent, complete API instead of a temporary in-memory mock.
const python = spawn(process.env.PYTHON_BIN || (process.platform === 'win32' ? 'python' : 'python3'),
  [path.join(root, 'server.py'), '--port', String(backendPort)], {
    cwd: root, env: { ...process.env, APP_ORIGIN: internalOrigin,
      APP_DB: process.env.APP_DB || path.join(root, 'data', 'app.sqlite3') },
    stdio: ['ignore', 'inherit', 'inherit'], windowsHide: true,
  });
python.on('error', () => console.error('Backend não iniciou. Configure PYTHON_BIN com Python 3.13+ ou use o Dockerfile.'));
python.on('exit', () => { available = false; });
const probe = setInterval(() => {
  const req = http.get(`${internalOrigin}/api/health`, res => {
    res.resume(); available = res.statusCode === 200;
  });
  req.setTimeout(1500, () => req.destroy());
  req.on('error', () => { available = false; });
}, 1000);
app.use(['/api', '/media'], (req, res) => {
  if (!available) return res.status(503).json({ error: 'O serviço de cadastro está indisponível. A equipe precisa configurar o backend; seus dados não foram enviados.' });
  if (!['GET', 'POST'].includes(req.method)) return res.status(405).json({ error: 'Método não permitido.' });
  if (req.method === 'POST') {
    const origin = req.get('origin');
    const expected = process.env.PUBLIC_ORIGIN || `${req.protocol}://${req.get('host')}`;
    if (!origin || origin !== expected) return res.status(403).json({ error: 'Origem não permitida. Configure PUBLIC_ORIGIN para o endereço desta aplicação.' });
  }
  const headers: http.IncomingHttpHeaders = { ...req.headers, host: `127.0.0.1:${backendPort}`, origin: internalOrigin };
  delete headers['forwarded']; delete headers['x-forwarded-host'];
  const upstream = http.request({ hostname: '127.0.0.1', port: backendPort,
    path: req.originalUrl, method: req.method, headers }, response => {
    res.status(response.statusCode || 502);
    for (const [key, value] of Object.entries(response.headers)) {
      if (value === undefined || ['connection', 'transfer-encoding'].includes(key)) continue;
      if (key === 'set-cookie' && (process.env.PUBLIC_ORIGIN?.startsWith('https://') || req.secure))
        res.setHeader(key, (value as string[]).map(cookie => cookie + '; Secure'));
      else res.setHeader(key, value);
    }
    response.pipe(res);
  });
  upstream.setTimeout(15000, () => upstream.destroy());
  upstream.on('error', () => {
    if (!res.headersSent) res.status(503).json({ error: 'Não foi possível acessar o serviço de cadastro. Tente novamente ou contate a equipe.' });
    else res.end();
  });
  req.pipe(upstream);
});
app.use(express.static(path.join(root, 'web')));
app.get('*', (_req, res) => res.sendFile(path.join(root, 'web', 'index.html')));
const listener = app.listen(port, '0.0.0.0', () => console.log(`Aplicação na porta ${port}. Configure APP_DB em volume persistente.`));
function shutdown() { clearInterval(probe); python.kill(); listener.close(() => process.exit(0)); }
process.on('SIGTERM', shutdown); process.on('SIGINT', shutdown);

process.on('message', message => { if (message === 'shutdown') shutdown(); });
