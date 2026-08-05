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
    if (!overlapsModule) return { candidate, legalMoveM };
  }
  throw new Error('No top-row module has a provably legal empty-space move');
}

const expectedSequential30 = Array.from({ length: 30 }, (_, index) => index + 1);
const expectedLeapfrog30 = [
  1,3,5,7,9,11,13,15,17,19,21,23,25,27,29,
  30,28,26,24,22,20,18,16,14,12,10,8,6,4,2,
];

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

  phase('load-full-array-topology');
  const response = await page.goto(`${baseUrl}/browser/workbench.html`, { waitUntil: 'networkidle' });
  assert.equal(response?.status(), 200, 'workbench did not return HTTP 200');
  await page.waitForFunction(() => (
    document.querySelector('#status')?.classList.contains('ok')
    && document.querySelectorAll('#topology-board .string-strip').length === 24
    && document.querySelectorAll('#topology-board .topology-cell').length === 720
    && document.querySelectorAll('#topology-board .mppt-group').length === 12
    && document.querySelectorAll('#rows tr').length === 24
  ), null, { timeout: 30000 });

  assert.equal(await page.locator('#topology-board .string-strip').count(), 24);
  assert.equal(await page.locator('#topology-board .topology-cell').count(), 720);
  assert.equal(await page.locator('#topology-board .mppt-group').count(), 12);
  const identities = await page.locator('#topology-board .string-strip').evaluateAll((items) => items.map((item) => ({
    string: item.dataset.stringId,
    input: item.dataset.inputId,
    mppt: item.dataset.mpptId,
  })));
  assert.equal(new Set(identities.map((item) => item.string)).size, 24);
  assert.equal(new Set(identities.map((item) => item.input)).size, 24);
  assert.equal(new Set(identities.map((item) => item.mppt)).size, 12);

  phase('verify-mobile-readability');
  await page.setViewportSize({ width: 390, height: 844 });
  const mobileStyles = await page.evaluate(() => {
    const header = getComputedStyle(document.querySelector('.mppt-header'));
    const strip = getComputedStyle(document.querySelector('.strip-scroll'));
    const detail = getComputedStyle(document.querySelector('#selected-detail'));
    const detailScroll = getComputedStyle(document.querySelector('#selected-detail .detail-scroll'));
    return {
      contract: document.querySelector('meta[name="mobile-topology-contract"]')?.content ?? '',
      mppt_header_font_size: header.fontSize,
      mppt_header_padding_top: header.paddingTop,
      strip_overflow_x: strip.overflowX,
      strip_touch_action: strip.touchAction,
      selected_summary_position: detail.position,
      selected_diagram_display: detailScroll.display,
      selected_summary_text: document.querySelector('#selected-detail-note')?.textContent ?? '',
    };
  });
  assert.equal(mobileStyles.contract, 'compact-mppt-headers safe-horizontal-strip-scroll sticky-selected-string-summary');
  assert.equal(mobileStyles.mppt_header_font_size, '11px');
  assert.equal(mobileStyles.mppt_header_padding_top, '5px');
  assert.equal(mobileStyles.strip_overflow_x, 'auto');
  assert.match(mobileStyles.strip_touch_action, /pan-x/);
  assert.equal(mobileStyles.selected_summary_position, 'sticky');
  assert.equal(mobileStyles.selected_diagram_display, 'block');
  assert.match(mobileStyles.selected_summary_text, /STR-01/);
  await page.setViewportSize({ width: 1600, height: 1200 });

  phase('verify-v8-traversals');
  await page.locator('#topology-board .string-strip[data-string-id="STR-01"]').click();
  let evidence = await page.evaluate(() => window.__v11TopologyEvidence);
  assert.deepEqual(evidence.leapfrog_order, expectedLeapfrog30);
  assert.deepEqual(evidence.sequential_order, expectedSequential30);
  assert.match(await page.locator('#selected-order').textContent(), /Leapfrog: 1 → 3 → 5/);
  await page.locator('.wiring-mode[data-mode="sequential"]').click();
  assert.match(await page.locator('#selected-order').textContent(), /Sequential: 1 → 2 → 3/);
  await page.locator('.wiring-mode[data-mode="compare"]').click();
  assert.match(await page.locator('#selected-order').textContent(), /Sequential:/);
  assert.match(await page.locator('#selected-order').textContent(), /Leapfrog:/);
  await page.locator('.wiring-mode[data-mode="leapfrog"]').click();

  phase('export-default-package');
  const initialPackage = JSON.parse(await downloadText(page, '#export'));
  assert.equal(initialPackage.reference_boundary.string_count, 24);
  assert.equal(initialPackage.reference_boundary.modules_per_string, 30);
  assert.equal(initialPackage.reference_boundary.module_count, 720);
  assert.equal(initialPackage.layout.modules.length, 720);
  assert.equal(initialPackage.strings.length, 24);
  assert.equal(initialPackage.view_contract.primary_view, 'v8-style-full-array-string-strips');
  assert.equal(initialPackage.view_contract.string_strip_count, 24);
  assert.equal(initialPackage.view_contract.topology_cell_count, 720);
  assert.deepEqual(initialPackage.view_contract.leapfrog_order, expectedLeapfrog30);

  phase('safe-topology-scroll');
  const firstCell = page.locator('#topology-board .topology-cell').first();
  const firstCellBox = await firstCell.boundingBox();
  assert.ok(firstCellBox, 'cannot locate first topology cell');
  await page.mouse.move(firstCellBox.x + firstCellBox.width / 2, firstCellBox.y + firstCellBox.height / 2);
  await page.mouse.down();
  await page.mouse.move(firstCellBox.x + 120, firstCellBox.y + 60, { steps: 5 });
  await page.mouse.up();
  const safePackage = JSON.parse(await downloadText(page, '#export'));
  assert.equal(safePackage.layout.layout_hash, initialPackage.layout.layout_hash, 'topology scrolling/selection changed physical layout');
  assert.equal(safePackage.view_contract.physical_edit_enabled, false);

  phase('physical-edit-lock');
  await page.locator('#show-physical').click();
  await page.waitForSelector('#physical-view:not([hidden])');
  assert.equal(await page.locator('#edit-physical').isChecked(), false);
  const { candidate, legalMoveM } = chooseLegalTopSpaceMove(initialPackage.layout);
  let moduleLocator = page.locator(`#physical-canvas .module[data-id="${candidate.id}"]`);
  let moduleBox = await moduleLocator.boundingBox();
  const canvasBox = await page.locator('#physical-canvas').boundingBox();
  assert.ok(moduleBox && canvasBox, `cannot locate ${candidate.id} or physical canvas`);
  await page.mouse.move(moduleBox.x + moduleBox.width / 2, moduleBox.y + moduleBox.height / 2);
  await page.mouse.down();
  await page.mouse.move(moduleBox.x + 50, moduleBox.y - 50, { steps: 4 });
  await page.mouse.up();
  const lockedPackage = JSON.parse(await downloadText(page, '#export'));
  assert.equal(lockedPackage.layout.layout_hash, initialPackage.layout.layout_hash, 'disabled physical editing changed layout');

  phase('explicit-physical-edit');
  await page.locator('#edit-physical').check();
  moduleLocator = page.locator(`#physical-canvas .module[data-id="${candidate.id}"]`);
  moduleBox = await moduleLocator.boundingBox();
  const screenTransform = await page.locator('#physical-canvas').evaluate((svg) => {
    const matrix = svg.getScreenCTM();
    if (!matrix) return null;
    return { yPixelsPerUnit: Math.hypot(matrix.c, matrix.d) };
  });
  assert.ok(moduleBox && screenTransform?.yPixelsPerUnit > 0);
  const centreX = moduleBox.x + moduleBox.width / 2;
  const centreY = moduleBox.y + moduleBox.height / 2;
  await page.mouse.move(centreX, centreY);
  await page.mouse.down();
  await page.mouse.move(centreX, centreY - legalMoveM * screenTransform.yPixelsPerUnit, { steps: 8 });
  await page.mouse.up();
  await page.waitForFunction(() => document.querySelector('#status')?.classList.contains('ok'), null, { timeout: 30000 });

  const movedPackage = JSON.parse(await downloadText(page, '#export'));
  const movedModule = movedPackage.layout.modules.find((module) => module.id === candidate.id);
  assert.ok(movedModule, `moved package missing ${candidate.id}`);
  assert.equal(movedModule.string_id, candidate.string_id);
  assert.equal(Number(movedModule.electrical_index), Number(candidate.electrical_index));
  assert.notEqual(movedPackage.layout.layout_hash, initialPackage.layout.layout_hash);
  const initialString = findById(initialPackage.strings, candidate.string_id, 'initial package');
  const movedString = findById(movedPackage.strings, candidate.string_id, 'moved package');
  assert.notEqual(movedString.one_way_route_m, initialString.one_way_route_m);

  phase('reject-outside-boundary');
  moduleLocator = page.locator(`#physical-canvas .module[data-id="${candidate.id}"]`);
  moduleBox = await moduleLocator.boundingBox();
  assert.ok(moduleBox);
  await page.mouse.move(moduleBox.x + moduleBox.width / 2, moduleBox.y + moduleBox.height / 2);
  await page.mouse.down();
  await page.mouse.move(canvasBox.x - 200, moduleBox.y + moduleBox.height / 2, { steps: 3 });
  await page.mouse.up();
  await page.waitForFunction(() => document.querySelector('#status')?.classList.contains('ok'), null, { timeout: 30000 });
  const rejectedPackage = JSON.parse(await downloadText(page, '#export'));
  assert.equal(rejectedPackage.layout.layout_hash, movedPackage.layout.layout_hash, 'attempted outside-boundary move changed layout');

  phase('non-default-full-array');
  const values = {
    '#string-count': '12',
    '#modules-per-string': '20',
    '#mppt-count': '6',
    '#inputs-per-mppt': '2',
    '#east-string-count': '6',
    '#strings-per-band': '2',
    '#row-pitch': '4',
  };
  for (const [selector, value] of Object.entries(values)) await page.locator(selector).fill(value);
  await page.locator('#reset').click();
  await page.waitForFunction(() => (
    document.querySelector('#status')?.classList.contains('ok')
    && document.querySelectorAll('#topology-board .string-strip').length === 12
    && document.querySelectorAll('#topology-board .topology-cell').length === 240
    && document.querySelectorAll('#topology-board .mppt-group').length === 6
    && document.querySelectorAll('#rows tr').length === 12
  ), null, { timeout: 30000 });
  assert.equal(await page.locator('#topology-board .string-strip').count(), 12);
  assert.equal(await page.locator('#topology-board .topology-cell').count(), 240);
  assert.equal(await page.locator('#topology-board .mppt-group').count(), 6);

  const customPackage = JSON.parse(await downloadText(page, '#export'));
  assert.equal(customPackage.reference_boundary.string_count, 12);
  assert.equal(customPackage.reference_boundary.modules_per_string, 20);
  assert.equal(customPackage.reference_boundary.module_count, 240);
  assert.equal(customPackage.view_contract.string_strip_count, 12);
  assert.equal(customPackage.view_contract.topology_cell_count, 240);
  assert.equal(customPackage.view_contract.mppt_group_count, 6);
  assert.deepEqual(customPackage.view_contract.sequential_order, Array.from({ length: 20 }, (_, index) => index + 1));

  phase('export-non-default-csv');
  const csv = await downloadText(page, '#export-csv');
  const csvLines = csv.trim().split(/\r?\n/);
  assert.equal(csvLines.length, 13, 'CSV must contain one header and 12 strings');
  assert.equal(new Set(csvLines.slice(1).map((line) => line.split(',')[0])).size, 12);

  phase('verify-browser-errors');
  assert.deepEqual(pageErrors, [], `page errors: ${pageErrors.join(' | ')}`);
  assert.deepEqual(consoleErrors, [], `console errors: ${consoleErrors.join(' | ')}`);

  const elapsedSeconds = (performance.now() - started) / 1000;
  console.log(JSON.stringify({
    schema_version: 'globalgrid2050.v11.full-array-browser-evidence.v1',
    pass: true,
    phase: 'complete',
    browser: executablePath,
    elapsed_seconds: Number(elapsedSeconds.toFixed(3)),
    mobile_readability: mobileStyles,
    default_array: {
      strings: 24,
      modules_per_string: 30,
      modules: 720,
      mppt_groups: 12,
      physical_inputs: 24,
      string_strips: 24,
      topology_cells: 720,
      safe_scroll_layout_hash: safePackage.layout.layout_hash,
      moved_module_id: candidate.id,
      retained_string_id: candidate.string_id,
      retained_electrical_index: Number(candidate.electrical_index),
      layout_hash_after_edit: movedPackage.layout.layout_hash,
    },
    non_default_array: {
      strings: 12,
      modules_per_string: 20,
      modules: 240,
      mppt_groups: 6,
      string_strips: 12,
      topology_cells: 240,
    },
    traversal: {
      sequential_30: expectedSequential30,
      leapfrog_30: expectedLeapfrog30,
    },
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
