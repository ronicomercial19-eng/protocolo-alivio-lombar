import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

test('scripts da interface compartilham funções da entrada e do guia', () => {
  const html = readFileSync(new URL('../web/index.html', import.meta.url), 'utf8');
  const scripts = [...html.matchAll(/<script(?![^>]*type="module")[^>]*src="\/([^"]+\.js)"/g)].map(x => x[1]);
  assert.ok(scripts.includes('review-ui.js'));
  assert.ok(scripts.includes('app.js'));
  const app = {
    innerHTML: '',
    querySelectorAll: () => [],
    querySelector: () => null,
  };
  const context = vm.createContext({
    document: { querySelector: () => app, documentElement: { dataset: {} } },
    localStorage: { getItem: () => null },
    navigator: {},
    window: {},
    fetch: () => new Promise(() => {}),
    setTimeout, clearTimeout, setInterval, clearInterval,
    console,
  });
  for (const path of scripts) {
    const source = readFileSync(new URL('../web/' + path, import.meta.url), 'utf8');
    vm.runInContext(source, context, { filename: path });
  }
  assert.match(vm.runInContext('landingHome()', context), /Uma experiência, quatro responsabilidades/);
  const guide = vm.runInContext('medicalGuide()', context);
  assert.match(guide, /Parecer por item/);
  assert.equal((guide.match(/Produção pendente/g) || []).length, 9);
});
