import { test } from 'node:test';
import assert from 'node:assert/strict';
import { fork, execFileSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { setTimeout as delay } from 'node:timers/promises';

test('cadastro → sessão → triagem → fila clínica, com persistência e CSRF', async () => {
  const folder = fs.mkdtempSync(path.join(os.tmpdir(), 'lombar-gateway-'));
  const python = process.env.PYTHON_BIN || (process.platform === 'win32' ? 'python' : 'python3');
  const env = { ...process.env, APP_DB: path.join(folder, 'test.sqlite3'), PORT: '8092', BACKEND_PORT: '8093', DEFAULT_CLINICIAN_EMAIL: 'clinic@example.test' };
  execFileSync(python, ['-c', "import server; server.initialize(); db=__import__('sqlite3').connect(server.DB); db.execute(\"INSERT INTO users(name,email,password,role,state) VALUES(?,?,?,'clinician','ativo')\",('Equipe fictícia','clinic@example.test',server.password('fictional-test-password'))); db.commit(); db.close()"], { env });
  let child;
  const start = async () => {
    child = fork('dist/server.js', [], { env, stdio: ['ignore', 'ignore', 'inherit', 'ipc'] });
    for (let i = 0; i < 60; i++) {
      try { if ((await fetch('http://127.0.0.1:8092/api/health')).ok) return; } catch {}
      await delay(100);
    }
    throw Error('Backend não iniciou');
  };
  const stop = async () => { const exited = new Promise(resolve => child.once('exit', resolve)); child.send('shutdown'); await exited; await delay(200); };
  let cookie = '', csrf = '';
  const call = async (route, body, origin = 'http://127.0.0.1:8092') => {
    const response = await fetch(`http://127.0.0.1:8092/api/${route}`, { method: body === undefined ? 'GET' : 'POST', headers: { Cookie: cookie, Origin: origin, 'Content-Type': 'application/json', 'X-CSRF-Token': csrf }, body: body === undefined ? undefined : JSON.stringify(body) });
    if (response.headers.get('set-cookie')) cookie = response.headers.get('set-cookie').split(';')[0];
    return { status: response.status, body: await response.json() };
  };
  try {
    await start();
    for (const asset of ['/', '/app.js', '/care.js', '/staff.js', '/medical.js', '/educator.js', '/startup.js', '/icon.svg']) {
      assert.equal((await fetch(`http://127.0.0.1:8092${asset}`)).status, 200, asset);
    }
    assert.equal((await call('me')).status, 401);
    assert.equal((await call('unknown')).status, 401); // JSON, never the SPA HTML.
    assert.equal((await call('register', { name: 'Piloto fictício', email: 'pilot@example.test', password: 'fictional-test-password', consent: false })).status, 400);
    assert.equal((await call('register', { name: 'Piloto fictício', email: 'pilot@example.test', password: 'fictional-test-password', consent: true })).status, 200);
    let me = (await call('me')).body;
    csrf = me.csrf;
    assert.equal(me.state, 'triagem_pendente');
    assert.equal(me.careTeam.name, 'Equipe fictícia');
    assert.equal((await call('triage', { duration: '3 meses ou mais', newSymptoms: 'nao', goal: 'Subir escadas' }, 'https://evil.test')).status, 403);
    assert.equal((await call('triage', { duration: '3 meses ou mais', newSymptoms: 'nao', neurologicConcern: 'nao', seriousCondition: 'nao', goal: 'Subir escadas' })).status, 200);
    assert.equal((await call('me')).body.state, 'em_revisao');
    assert.equal((await call('session/start', {})).status, 403);
    await stop(); await start();
    assert.equal((await call('me')).body.state, 'em_revisao');
    cookie = ''; csrf = '';
    assert.equal((await call('login', { email: 'clinic@example.test', password: 'fictional-test-password' })).status, 200);
    const queue = (await call('patients')).body;
    assert.equal(queue.length, 1);
    assert.equal(queue[0].state, 'em_revisao');
    assert.ok(queue[0].records.some(r => r.kind === 'triage'));
  } finally {
    if (child && child.exitCode === null) await stop();
    if (path.dirname(folder) === os.tmpdir() && path.basename(folder).startsWith('lombar-gateway-')) fs.rmSync(folder, { recursive: true });
  }
});
