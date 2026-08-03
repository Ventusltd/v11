#!/usr/bin/env node
import assert from 'node:assert/strict';
import { access, readFile } from 'node:fs/promises';
import { spawn } from 'node:child_process';
import { chromium } from 'playwright-core';

const port = Number(process.env.V11_E2E_PORT ?? 8765);
const baseUrl = `http://127.0.0.1:${port}`;
let server;
let browser;
let testTimeout;
let currentPhase = 'initialise';

function phase(name) {
  currentPhase = name;
  console.log(JSON.stringify({ event: 'phase', phase: name }));
}

async function requirePlaywrightChromium() {
  const executablePath = chromium.executablePath();
  try {
    await access(executablePath);
  } catch {
    throw new Error(`Pinned Playwright Chromium is not installed at ${executablePath}; provision it before starting the 100-second browser test`);
  }
  return executablePath;
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

function footprint(module, xM = Number(module.x_m), yM = Number(module.y_m)) {
  const rotation = ((Number(module.rotation_deg) || 0) % 180 + 180) % 180;
  const widthM = rotation === 90 ? Number(module.height_m) : Number(module.width_m);
  const heightM = rotation === 90 ? Number(module.width_m) : Number(module.height_m);
  return {
    left: xM - widthM / 2,
    right: xM + widthM / 2,
    bottom: yM - heightM / 2,
    top: yM + heightM / 2,
  };
}

function intersects(left, right) {
  return Math.min(left.right, right.right) > Math.max(left.left, right.left)
    && Math.min(left.top, right.top) > Math.max(left.bottom, right.bottom);
}

function chooseLegalTopSpaceMove(layout) {
  const snapM = 0.05;
  const maximumY = Math.max(...layout.modules.map((module) => Number(module.y_m)));
  const topRow = layout.modules
    .filter((module) => Math.abs(Number(module.y_m) - maximumY) <= 1e-9)
    .sort((left, right) => Number(left.x_m) - Number(right.x_m));
  const centre = (Number(layout.boundary.x_min) + Number(layout.boundary.x_max)) / 2;
  const candidates = [...topRow].sort((left, right) => (
    Math.abs(Number(left.x_m) - centre) - Math.abs(Number(right.x_m) - centre)
  ));

  for (const candidate of candidates) {
    const current = footprint(candidate);
    const clearanceM = Number(layout.boundary.y_max) - current.top;
    const legalMoveM = Math.min(0.5, Math.floor((clearanceM * 0.5) / snapM) * snapM);
    if (legalMoveM < 2 * snapM) continue;
    const target = footprint(candidate, Number(candidate.x_m), Number(candidate.y_m) + legalMoveM);
    const insideBoundary = target.left >= Number(layout.boundary.x_min) - 1e-12
      && target.right <= Number(layout.boundary.x_max) + 1e-12
      && target.bottom >= Number(layout.boundary.y_min) - 1e-12
      && target.top <= Number(layout.boundary.y_max) + 1e-12;
    if (!insideBoundary) continue;
    const overlapsModule = layout.modules.some((module) => (
      module.id !== candidate.id && intersects(target, footprint(module))
    ));
    const overlapsObstacle = (layout.obstacles ?? []).some((obstacle) => intersects(target, {
      left: Number(obstacle.x_min),
      right: Number(obstacle.x_max),
      bottom: Number(obstacle.y_min),
      top: Number(obstacle.y_max),
    }));
    if (!overlapsModule && !overlapsObstacle) return { candidate, legalMoveM };
  }
  throw new Error('No top-row module has a provably legal empty-space move');
}

try {
  phase('require-browser');
  const executablePath = await requirePlaywrightChromium();
  const started = performance.now();
  testTimeout = setTimeout(() => {
    console.error(JSON.stringify({ pass: false, phase: currentPhase, error: 'Chromium workbench acceptance exceeded 100 seconds' }));
    process.exit(124);
  }, 100_000);

  phase('start-server');
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

  phase('launch-browser');
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

  phase('load-workbench');
  const response = await page.goto(`${baseUrl}/browser/workbench.html`, { waitUntil: 'networkidle' });
  assert.equal(response?.status(), 200, 'workbench did not return HTTP 200');
  await page.waitForFunction(() => (
    document.querySelector('#status')?.classList.contains('ok')
    && document.querySelectorAll('#canvas .module').length === 720
    && document.querySelectorAll('#rows tr').length === 24
  ), null, { timeout: 30000 });
  assert.equal(await page.locator('#canvas .module').count(), 720);
  assert.equal(await page.locator('#rows tr').count(), 24);

  phase('export-initial-json');
  const initialPackage = JSON.parse(await downloadText(page, '#export'));
  assert.equal(initialPackage.reference_boundary.string_count, 24);
  assert.equal(initialPackage.reference_boundary.modules_per_string, 30);
  assert.equal(initialPackage.reference_boundary.module_count, 720);
  assert.equal(initialPackage.layout.modules.length, 720);
  assert.equal(initialPackage.strings.length, 24);

  const { candidate, legalMoveM } = chooseLegalTopSpaceMove(initialPackage.layout);
  assert.ok(candidate?.string_id, 'top-row drag candidate has no string identity');
  assert.ok(Number.isInteger(Number(candidate.electrical_index)));
  const initialString = findById(initialPackage.strings, candidate.string_id, 'initial engineering package');

  phase('legal-drag');
  let moduleLocator = page.locator(`#canvas .module[data-id="${candidate.id}"]`);
  const moduleBox = await moduleLocator.boundingBox();
  const canvasBox = await page.locator('#canvas').boundingBox();
  const screenTransform = await page.locator('#canvas').evaluate((svg) => {
    const matrix = svg.getScreenCTM();
    if (!matrix) return null;
    return { yPixelsPerUnit: Math.hypot(matrix.c, matrix.d) };
  });
  assert.ok(moduleBox && canvasBox, `cannot locate ${candidate.id} or canvas`);
  assert.ok(screenTransform?.yPixelsPerUnit > 0, 'canvas has no usable SVG screen transform');

  const centreX = moduleBox.x + moduleBox.width / 2;
  const centreY = moduleBox.y + moduleBox.height / 2;
  const legalMovePixels = legalMoveM * screenTransform.yPixelsPerUnit;
  await page.mouse.move(centreX, centreY);
  await page.mouse.down();
  await page.mouse.move(centreX, centreY - legalMovePixels, { steps: 8 });
  await page.mouse.up();
  await page.waitForFunction(() => document.querySelector('#status')?.classList.contains('ok'), null, { timeout: 30000 });

  phase('verify-legal-drag');
  const movedPackage = JSON.parse(await downloadText(page, '#export'));
  const movedModule = movedPackage.layout.modules.find((module) => module.id === candidate.id);
  assert.ok(movedModule, `moved package missing ${candidate.id}`);
  assert.equal(movedModule.string_id, candidate.string_id, 'drag changed string identity');
  assert.equal(Number(movedModule.electrical_index), Number(candidate.electrical_index), 'drag changed electrical index');
  assert.ok(Number(movedModule.y_m) > Number(candidate.y_m), 'geometry-derived drag did not move the module into empty top space');
  assert.ok(Math.abs((Number(movedModule.y_m) - Number(candidate.y_m)) - legalMoveM) <= 0.051,
    'rendered drag did not match the geometry-derived legal movement');
  assert.notEqual(movedPackage.layout.layout_hash, initialPackage.layout.layout_hash, 'legal drag did not change layout hash');
  const movedString = findById(movedPackage.strings, candidate.string_id, 'moved engineering package');
  assert.notEqual(movedString.one_way_route_m, initialString.one_way_route_m, 'legal drag did not change route length');
  assert.notEqual(movedString.sequential.loss_w, initialString.sequential.loss_w, 'legal drag did not change electrical loss');

  phase('reject-boundary-drag');
  moduleLocator = page.locator(`#canvas .module[data-id="${candidate.id}"]`);
  const movedBox = await moduleLocator.boundingBox();
  assert.ok(movedBox, 'cannot measure moved module');
  await page.mouse.move(movedBox.x + movedBox.width / 2, movedBox.y + movedBox.height / 2);
  await page.mouse.down();
  await page.mouse.move(canvasBox.x - 10, movedBox.y + movedBox.height / 2, { steps: 1 });
  await page.waitForFunction(() => document.querySelector('#status')?.classList.contains('error'), null, { timeout: 5000 });
  assert.match(await page.locator('#status').textContent(), /outside boundary/i);
  await page.mouse.up();
  await page.waitForFunction(() => document.querySelector('#status')?.classList.contains('ok'), null, { timeout: 30000 });

  phase('verify-rejection');
  const rejectedPackage = JSON.parse(await downloadText(page, '#export'));
  const rejectedModule = rejectedPackage.layout.modules.find((module) => module.id === candidate.id);
  assert.ok(rejectedModule, `post-rejection package missing ${candidate.id}`);
  assert.equal(rejectedPackage.layout.layout_hash, movedPackage.layout.layout_hash, 'rejected boundary move changed layout hash');
  assert.equal(Number(rejectedModule.x_m), Number(movedModule.x_m), 'rejected boundary move changed x geometry');
  assert.equal(Number(rejectedModule.y_m), Number(movedModule.y_m), 'rejected boundary move changed y geometry');

  phase('export-csv');
  const csv = await downloadText(page, '#export-csv');
  const csvLines = csv.trim().split(/\r?\n/);
  assert.equal(csvLines.length, 25, 'CSV must contain one header and 24 strings');
  assert.ok(csvLines[0].startsWith('string_id,module_count,one_way_route_m'));
  assert.equal(new Set(csvLines.slice(1).map((line) => line.split(',')[0])).size, 24);

  phase('verify-browser-errors');
  assert.deepEqual(pageErrors, [], `page errors: ${pageErrors.join(' | ')}`);
  assert.deepEqual(consoleErrors, [], `console errors: ${consoleErrors.join(' | ')}`);

  const elapsedSeconds = (performance.now() - started) / 1000;
  console.log(JSON.stringify({
    pass: true,
    phase: 'complete',
    browser: executablePath,
    elapsed_seconds: Number(elapsedSeconds.toFixed(3)),
    modules: 720,
    strings: 24,
    moved_module_id: candidate.id,
    retained_string_id: candidate.string_id,
    retained_electrical_index: Number(candidate.electrical_index),
    legal_move_m: legalMoveM,
    route_before_m: initialString.one_way_route_m,
    route_after_m: movedString.one_way_route_m,
    sequential_loss_before_w: initialString.sequential.loss_w,
    sequential_loss_after_w: movedString.sequential.loss_w,
  }, null, 2));
} catch (error) {
  console.error(JSON.stringify({
    pass: false,
    phase: currentPhase,
    error: error.message,
    stack: error.stack,
  }, null, 2));
  process.exitCode = 1;
} finally {
  if (testTimeout) clearTimeout(testTimeout);
  if (browser) await browser.close().catch(() => {});
  if (server && !server.killed) server.kill('SIGTERM');
}
