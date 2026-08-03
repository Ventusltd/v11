#!/usr/bin/env node
import assert from 'node:assert/strict';
import { access, readFile } from 'node:fs/promises';
import { spawn } from 'node:child_process';
import { chromium } from 'playwright-core';

const started = performance.now();
const port = Number(process.env.V11_E2E_PORT ?? 8765);
const baseUrl = `http://127.0.0.1:${port}`;
let server;
let browser;

async function firstExecutable(candidates) {
  for (const candidate of candidates.filter(Boolean)) {
    try {
      await access(candidate);
      return candidate;
    } catch {}
  }
  throw new Error('No system Chromium/Chrome executable found');
}

async function waitForServer() {
  let lastError;
  for (let attempt = 0; attempt < 40; attempt += 1) {
    try {
      const response = await fetch(`${baseUrl}/browser/workbench.html`);
      if (response.ok) return;
      lastError = new Error(`HTTP ${response.status}`);
    } catch (error) {
      lastError = error;
    }
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  throw new Error(`Workbench server did not become ready: ${lastError?.message ?? 'unknown error'}`);
}

async function downloadText(page, selector) {
  const [download] = await Promise.all([
    page.waitForEvent('download'),
    page.locator(selector).click(),
  ]);
  const filePath = await download.path();
  assert.ok(filePath, `${selector} did not produce a readable download`);
  return readFile(filePath, 'utf8');
}

function findById(items, id, label) {
  const item = items.find((candidate) => candidate.string_id === id);
  assert.ok(item, `${label} missing ${id}`);
  return item;
}

try {
  server = spawn('python3', ['-m', 'http.server', String(port), '--bind', '127.0.0.1'], {
    cwd: process.cwd(),
    stdio: ['ignore', 'ignore', 'pipe'],
  });
  let serverError = '';
  server.stderr.on('data', (chunk) => { serverError += chunk.toString(); });
  server.once('exit', (code) => {
    if (code && code !== 0) serverError += `\nserver exited ${code}`;
  });
  await waitForServer();

  const executablePath = await firstExecutable([
    process.env.CHROME_PATH,
    '/usr/bin/google-chrome',
    '/usr/bin/google-chrome-stable',
    '/usr/bin/chromium',
    '/usr/bin/chromium-browser',
  ]);
  browser = await chromium.launch({
    executablePath,
    headless: true,
    args: ['--no-sandbox', '--disable-dev-shm-usage'],
  });
  const context = await browser.newContext({ acceptDownloads: true, viewport: { width: 1600, height: 1200 } });
  const page = await context.newPage();
  const pageErrors = [];
  const consoleErrors = [];
  page.on('pageerror', (error) => pageErrors.push(error.message));
  page.on('console', (message) => {
    if (message.type() === 'error') consoleErrors.push(message.text());
  });
  await page.route('**/favicon.ico', (route) => route.fulfill({ status: 204, body: '' }));

  const response = await page.goto(`${baseUrl}/browser/workbench.html`, { waitUntil: 'networkidle' });
  assert.equal(response?.status(), 200, 'workbench did not return HTTP 200');
  await page.waitForFunction(() => (
    document.querySelector('#status')?.classList.contains('ok')
    && document.querySelectorAll('#canvas .module').length === 720
    && document.querySelectorAll('#rows tr').length === 24
  ), null, { timeout: 30000 });
  assert.equal(await page.locator('#canvas .module').count(), 720);
  assert.equal(await page.locator('#rows tr').count(), 24);

  const initialPackage = JSON.parse(await downloadText(page, '#export'));
  assert.equal(initialPackage.reference_boundary.string_count, 24);
  assert.equal(initialPackage.reference_boundary.modules_per_string, 30);
  assert.equal(initialPackage.reference_boundary.module_count, 720);
  assert.equal(initialPackage.layout.modules.length, 720);
  assert.equal(initialPackage.strings.length, 24);

  const minimumY = Math.min(...initialPackage.layout.modules.map((module) => Number(module.y_m)));
  const firstRow = initialPackage.layout.modules.filter((module) => Math.abs(Number(module.y_m) - minimumY) <= 1e-9);
  const candidate = firstRow.reduce((selected, module) => (
    Number(module.x_m) > Number(selected.x_m) ? module : selected
  ));
  assert.ok(candidate.string_id);
  assert.ok(Number.isInteger(Number(candidate.electrical_index)));
  const initialString = findById(initialPackage.strings, candidate.string_id, 'initial engineering package');

  let moduleLocator = page.locator(`#canvas .module[data-id="${candidate.id}"]`);
  const moduleBox = await moduleLocator.boundingBox();
  assert.ok(moduleBox, `cannot locate ${candidate.id}`);
  const centreX = moduleBox.x + moduleBox.width / 2;
  const centreY = moduleBox.y + moduleBox.height / 2;
  await page.mouse.move(centreX, centreY);
  await page.mouse.down();
  await page.mouse.move(centreX + 3, centreY, { steps: 4 });
  await page.mouse.up();
  await page.waitForFunction(() => document.querySelector('#status')?.classList.contains('ok'), null, { timeout: 30000 });

  const movedPackage = JSON.parse(await downloadText(page, '#export'));
  const movedModule = movedPackage.layout.modules.find((module) => module.id === candidate.id);
  assert.ok(movedModule, `moved package missing ${candidate.id}`);
  assert.equal(movedModule.string_id, candidate.string_id, 'drag changed string identity');
  assert.equal(Number(movedModule.electrical_index), Number(candidate.electrical_index), 'drag changed electrical index');
  assert.notEqual(movedPackage.layout.layout_hash, initialPackage.layout.layout_hash, 'legal drag did not change layout hash');
  const movedString = findById(movedPackage.strings, candidate.string_id, 'moved engineering package');
  assert.notEqual(movedString.one_way_route_m, initialString.one_way_route_m, 'legal drag did not change route length');
  assert.notEqual(movedString.sequential.loss_w, initialString.sequential.loss_w, 'legal drag did not change electrical loss');

  moduleLocator = page.locator(`#canvas .module[data-id="${candidate.id}"]`);
  const movedBox = await moduleLocator.boundingBox();
  const canvasBox = await page.locator('#canvas').boundingBox();
  assert.ok(movedBox && canvasBox, 'cannot measure moved module or canvas');
  const xBeforeRejectedMove = await moduleLocator.getAttribute('x');
  await page.mouse.move(movedBox.x + movedBox.width / 2, movedBox.y + movedBox.height / 2);
  await page.mouse.down();
  await page.mouse.move(canvasBox.x - 10, movedBox.y + movedBox.height / 2, { steps: 4 });
  await page.waitForFunction(() => document.querySelector('#status')?.classList.contains('error'), null, { timeout: 5000 });
  assert.match(await page.locator('#status').textContent(), /outside boundary/i);
  await page.mouse.up();
  await page.waitForFunction(() => document.querySelector('#status')?.classList.contains('ok'), null, { timeout: 30000 });
  const xAfterRejectedMove = await page.locator(`#canvas .module[data-id="${candidate.id}"]`).getAttribute('x');
  assert.equal(xAfterRejectedMove, xBeforeRejectedMove, 'rejected boundary move changed geometry');

  const csv = await downloadText(page, '#export-csv');
  const csvLines = csv.trim().split(/\r?\n/);
  assert.equal(csvLines.length, 25, 'CSV must contain one header and 24 strings');
  assert.ok(csvLines[0].startsWith('string_id,module_count,one_way_route_m'));
  assert.equal(new Set(csvLines.slice(1).map((line) => line.split(',')[0])).size, 24);

  assert.deepEqual(pageErrors, [], `page errors: ${pageErrors.join(' | ')}`);
  assert.deepEqual(consoleErrors, [], `console errors: ${consoleErrors.join(' | ')}`);

  const elapsedSeconds = (performance.now() - started) / 1000;
  console.log(JSON.stringify({
    pass: true,
    browser: executablePath,
    elapsed_seconds: Number(elapsedSeconds.toFixed(3)),
    modules: 720,
    strings: 24,
    moved_module_id: candidate.id,
    retained_string_id: candidate.string_id,
    retained_electrical_index: Number(candidate.electrical_index),
    route_before_m: initialString.one_way_route_m,
    route_after_m: movedString.one_way_route_m,
    sequential_loss_before_w: initialString.sequential.loss_w,
    sequential_loss_after_w: movedString.sequential.loss_w,
  }, null, 2));
} catch (error) {
  console.error(error.stack ?? error.message);
  process.exitCode = 1;
} finally {
  if (browser) await browser.close().catch(() => {});
  if (server && !server.killed) server.kill('SIGTERM');
}
