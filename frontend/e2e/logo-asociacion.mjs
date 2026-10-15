#!/usr/bin/env node
/**
 * End-to-end smoke test for the "Asociación astronómica" screen and the logo.
 *
 * Drives a REAL browser (Chrome or Edge) over the Chrome DevTools Protocol, so it
 * catches things that unit tests and `npm run build` cannot: module resolution
 * failures in the dev server, a broken Vite cache, images that never load, a
 * favicon that is never wired up, React state that does not propagate.
 *
 * It intentionally has ZERO dependencies: it uses Node's built-in fetch and its
 * global WebSocket (Node >= 22).
 *
 * REQUIREMENTS
 *   - both dev servers running:  backend on :8000  and  frontend on :5173
 *   - Chrome or Edge installed
 *
 * USAGE (from frontend/)
 *   npm run e2e                 full run: renders + real click-through
 *   npm run e2e -- --read-only  only reads (touches no data)
 *   npm run e2e -- --headed     show the browser window while it works
 *
 * The full run temporarily changes the association name and logo, then ALWAYS
 * restores the original values (also when an assertion fails).
 *
 * Run it after touching anything that affects module loading. A stale Vite dev
 * server can serve old modules and blank the whole app while the terminal stays
 * clean - only a real browser exposes that.
 */
import { spawn } from 'node:child_process';
import { existsSync, rmSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(HERE, '..', '..');
const LOGO_FIXTURE = path.join(REPO_ROOT, 'backend', 'data', 'imagenes', 'logo.jpg');

const BASE = process.env.E2E_BASE_URL ?? 'http://localhost:5173';
const DEBUG_PORT = Number(process.env.E2E_DEBUG_PORT ?? 9444);
const TIMEOUT_MS = Number(process.env.E2E_TIMEOUT_MS ?? 20000);

const args = process.argv.slice(2);
const READ_ONLY = args.includes('--read-only');
const HEADED = args.includes('--headed');

const NEW_NAME = 'Asociación Astronómica Riguel';
const ROUTES = ['/', '/observaciones', '/observaciones/new', '/admin/filtros', '/admin/asociacion'];

const sleep = ms => new Promise(r => setTimeout(r, ms));

// ---------------------------------------------------------------------------
// tiny reporting helpers
// ---------------------------------------------------------------------------
const failures = [];
const pass = label => console.log(`  PASS  ${label}`);
const fail = label => console.log(`  FAIL  ${label}`);
const info = label => console.log(`        ${label}`);
const section = title => console.log(`\n${title}`);

function check(label, condition, detail = '') {
  if (condition) {
    pass(label);
    return true;
  }
  const line = detail ? `${label} -> ${detail}` : label;
  failures.push(line);
  fail(line);
  return false;
}

// ---------------------------------------------------------------------------
// browser discovery
// ---------------------------------------------------------------------------
function findBrowser() {
  const candidates = [
    process.env.E2E_BROWSER,
    'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
    path.join(process.env.LOCALAPPDATA ?? '', 'Google\\Chrome\\Application\\chrome.exe'),
    'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
    'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe',
    '/usr/bin/google-chrome',
    '/usr/bin/chromium',
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  ].filter(Boolean);

  return candidates.find(p => existsSync(p)) ?? null;
}

// ---------------------------------------------------------------------------
// minimal CDP client (built-in WebSocket)
// ---------------------------------------------------------------------------
async function fetchJson(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status} en ${url}`);
  return res.json();
}

async function waitForDebugger() {
  for (let i = 0; i < 100; i++) {
    try {
      return await fetchJson(`http://127.0.0.1:${DEBUG_PORT}/json/version`);
    } catch {
      await sleep(300);
    }
  }
  throw new Error(`el puerto de depuración ${DEBUG_PORT} nunca respondió`);
}

function connect(wsUrl) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(wsUrl);
    const pending = new Map();
    const listeners = [];
    let seq = 0;

    const send = (method, params) =>
      new Promise((res, rej) => {
        const id = ++seq;
        pending.set(id, { res, rej });
        ws.send(JSON.stringify({ id, method, params: params ?? {} }));
      });

    ws.addEventListener('open', () =>
      resolve({ send, on: cb => listeners.push(cb), close: () => ws.close() }),
    );
    ws.addEventListener('error', () => reject(new Error('no se pudo abrir el WebSocket de CDP')));
    ws.addEventListener('message', ev => {
      const msg = JSON.parse(ev.data);
      if (msg.id && pending.has(msg.id)) {
        const { res, rej } = pending.get(msg.id);
        pending.delete(msg.id);
        if (msg.error) rej(new Error(JSON.stringify(msg.error)));
        else res(msg.result);
      } else {
        for (const cb of listeners) cb(msg);
      }
    });
  });
}

// ---------------------------------------------------------------------------
// app API (through the Vite proxy, so a single base URL is enough)
// ---------------------------------------------------------------------------
const api = {
  get: () => fetchJson(`${BASE}/api/v1/observatorio`),
  put: body =>
    fetch(`${BASE}/api/v1/observatorio`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }).then(r => r.json()),
  deleteLogo: () =>
    fetch(`${BASE}/api/v1/observatorio/logo`, { method: 'DELETE' }).then(r => r.json()),
};

// ---------------------------------------------------------------------------
// the run
// ---------------------------------------------------------------------------
let browser;
let profileDir;
let original = null;

async function main() {
  console.log('E2E: pantalla de asociación + logo (navegador real)');
  console.log(`  base   : ${BASE}`);
  console.log(`  modo   : ${READ_ONLY ? 'solo lectura' : 'click-through completo (restaura el estado)'}`);

  const executable = findBrowser();
  if (!executable) {
    throw new Error('no encontré Chrome ni Edge. Definí E2E_BROWSER con la ruta al ejecutable.');
  }
  info(`navegador: ${executable}`);

  if (!existsSync(LOGO_FIXTURE)) {
    throw new Error(`falta el archivo de prueba ${LOGO_FIXTURE}`);
  }

  try {
    await fetchJson(`${BASE}/api/v1/observatorio`);
  } catch (err) {
    throw new Error(`no responde la app en ${BASE}. ¿Están levantados backend (:8000) y frontend (:5173)? (${err.message})`);
  }

  original = await api.get();
  info(`estado inicial: nombre="${original.nombre}" logo=${original.logo_path ?? '(ninguno)'}`);

  profileDir = path.join(os.tmpdir(), `orq-e2e-${Date.now()}`);
  browser = spawn(executable, [
    HEADED ? '--new-window' : '--headless=new',
    '--disable-gpu',
    '--no-first-run',
    '--no-default-browser-check',
    '--disable-extensions',
    '--mute-audio',
    `--remote-debugging-port=${DEBUG_PORT}`,
    `--user-data-dir=${profileDir}`,
    'about:blank',
  ], { stdio: 'ignore', windowsHide: !HEADED });

  const version = await waitForDebugger();
  info(`conectado a ${version.Browser}`);

  const targets = await fetchJson(`http://127.0.0.1:${DEBUG_PORT}/json/list`);
  const page = targets.find(t => t.type === 'page');
  if (!page) throw new Error('el navegador no expuso ninguna pestaña');

  const cdp = await connect(page.webSocketDebuggerUrl);
  await cdp.send('Page.enable');
  await cdp.send('Runtime.enable');
  await cdp.send('Log.enable');
  await cdp.send('DOM.enable');
  await cdp.send('Network.enable');

  const consoleErrors = [];
  cdp.on(msg => {
    if (msg.method === 'Runtime.exceptionThrown') {
      const d = msg.params.exceptionDetails;
      consoleErrors.push(d?.exception?.description ?? d?.text ?? 'excepción desconocida');
    } else if (msg.method === 'Log.entryAdded' && msg.params.entry.level === 'error') {
      consoleErrors.push(msg.params.entry.text);
    } else if (msg.method === 'Runtime.consoleAPICalled' && msg.params.type === 'error') {
      consoleErrors.push(msg.params.args.map(a => a.value ?? a.description ?? '').join(' '));
    }
  });

  const evaluate = async expression => {
    const r = await cdp.send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
    if (r.exceptionDetails) {
      throw new Error(`evaluación falló: ${r.exceptionDetails.exception?.description ?? r.exceptionDetails.text}`);
    }
    return r.result.value;
  };

  const goto = async route => {
    await cdp.send('Page.navigate', { url: BASE + route });
    await sleep(250);
    for (let i = 0; i < 60; i++) {
      if (await evaluate(`!!document.querySelector('aside')`)) break;
      await sleep(150);
    }
    await sleep(500);
  };

  const waitUntil = async (expression, label, timeout = TIMEOUT_MS) => {
    const deadline = Date.now() + timeout;
    while (Date.now() < deadline) {
      if (await evaluate(expression)) return true;
      await sleep(200);
    }
    throw new Error(`timeout esperando ${label}`);
  };

  // -- 1. la app renderiza y el logo está en todas las pantallas ------------
  section('1. Logo y nombre en todas las pantallas');
  for (const route of ROUTES) {
    await goto(route);
    const snap = await evaluate(`(() => {
      const aside = document.querySelector('aside');
      const logo = aside?.querySelector('img') ?? null;
      return {
        route: location.pathname,
        mounted: !!aside,
        nombre: aside?.querySelector('h1')?.innerText.trim() ?? null,
        logo: logo ? {
          src: logo.getAttribute('src'),
          natural: logo.naturalWidth + 'x' + logo.naturalHeight,
          rendered: Math.round(logo.getBoundingClientRect().width) + 'x' + Math.round(logo.getBoundingClientRect().height),
        } : null,
      };
    })()`);

    check(`${route} renderiza la app`, snap.mounted, 'el sidebar no existe (¿página en blanco?)');
    check(`${route} muestra el nombre`, snap.nombre === original.nombre, `esperaba "${original.nombre}", obtuve "${snap.nombre}"`);

    if (original.logo_path) {
      check(`${route} muestra el logo`, snap.logo?.src === `/imagenes/${original.logo_path}`, `src="${snap.logo?.src}"`);
      check(`${route} carga la imagen de verdad`, snap.logo && !snap.logo.natural.startsWith('0x'), `naturalSize=${snap.logo?.natural}`);
    } else {
      check(`${route} no muestra logo si no hay ninguno`, snap.logo === null);
    }
    if (snap.logo) info(`${route} -> ${snap.logo.src} (natural ${snap.logo.natural}, visible ${snap.logo.rendered})`);
  }

  // -- 2. controles de la pantalla ------------------------------------------
  section('2. Controles de /admin/asociacion');
  await goto('/admin/asociacion');
  const controls = await evaluate(`(() => {
    const input = Array.from(document.querySelectorAll('input')).find(i => i.id && document.querySelector('label[for="'+i.id+'"]'));
    const file = document.querySelector('input[type=file]');
    const preview = document.querySelector('img[alt="Logo de la asociación"]');
    const favicon = document.querySelector('link[rel="icon"]');
    return {
      heading: document.querySelector('main h1')?.innerText.trim() ?? null,
      label: input?.closest('div')?.querySelector('label')?.innerText.trim() ?? null,
      value: input?.value ?? null,
      accept: file?.getAttribute('accept') ?? null,
      previewSrc: preview?.getAttribute('src') ?? null,
      previewNatural: preview ? preview.naturalWidth + 'x' + preview.naturalHeight : null,
      favicon: favicon?.getAttribute('href') ?? null,
      buttons: Array.from(document.querySelectorAll('button')).map(b => b.innerText.trim()),
      hasFileInput: !!file,
    };
  })()`);

  check('la pantalla tiene su título', controls.heading === 'Asociación astronómica', `título="${controls.heading}"`);
  check('la etiqueta está asociada al campo', controls.label === 'Nombre de la asociación astronómica', `label="${controls.label}"`);
  check('el campo trae el nombre actual', controls.value === original.nombre, `valor="${controls.value}"`);
  check('existe el selector de archivo', controls.hasFileInput);
  check('el selector solo acepta JPG y PNG', controls.accept === 'image/jpeg,image/png', `accept="${controls.accept}"`);
  check('hay un botón Guardar', controls.buttons.includes('Guardar'));

  if (original.logo_path) {
    check('la vista previa apunta al logo actual', controls.previewSrc === `/imagenes/${original.logo_path}`, `src="${controls.previewSrc}"`);
    check('el favicon usa el logo', controls.favicon === `/imagenes/${original.logo_path}`, `favicon="${controls.favicon}"`);
  }

  // -- 3. click-through real ------------------------------------------------
  if (READ_ONLY) {
    section('3. Click-through');
    console.log('  SKIP  --read-only');
  } else {
    section('3. Click-through real');

    // 3a. guardar el nombre desde la UI
    await evaluate(`(() => {
      const el = Array.from(document.querySelectorAll('input')).find(i => i.id && document.querySelector('label[for="'+i.id+'"]'));
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      setter.call(el, ${JSON.stringify(NEW_NAME)});
      el.dispatchEvent(new Event('input', { bubbles: true }));
      return true;
    })()`);
    await sleep(150);
    await evaluate(`(() => {
      Array.from(document.querySelectorAll('button')).find(b => b.innerText.trim() === 'Guardar').click();
      return true;
    })()`);
    await waitUntil(`document.body.innerText.includes('Guardado')`, 'el mensaje de confirmación');

    const saved = await evaluate(`(() => {
      const img = document.querySelector('aside img');
      return {
        sidebarNombre: document.querySelector('aside h1')?.innerText.trim() ?? null,
        sidebarLogo: img ? { src: img.getAttribute('src'), cargado: img.naturalWidth > 0 } : null,
        api: null,
      };
    })()`);
    const persisted = await api.get();

    check('el nombre se guarda en el backend', persisted.nombre === NEW_NAME, `backend dice "${persisted.nombre}"`);
    check('el sidebar refleja el nombre nuevo', saved.sidebarNombre === NEW_NAME, `sidebar dice "${saved.sidebarNombre}"`);
    check('el logo del sidebar sigue cargando', !original.logo_path || saved.sidebarLogo?.cargado === true);

    // 3b. subir el logo desde la UI
    const beforeUpload = await evaluate(`document.querySelector('img[alt="Logo de la asociación"]')?.getAttribute('src') ?? null`);
    const { root } = await cdp.send('DOM.getDocument');
    const { nodeId } = await cdp.send('DOM.querySelector', { nodeId: root.nodeId, selector: 'input[type=file]' });
    if (!nodeId) throw new Error('no encontré el input de archivo para subir el logo');

    await cdp.send('DOM.setFileInputFiles', { files: [LOGO_FIXTURE], nodeId });
    await waitUntil(
      `(document.querySelector('img[alt="Logo de la asociación"]')?.getAttribute('src') ?? null) !== ${JSON.stringify(beforeUpload)}`,
      'que la vista previa cambie tras subir el logo',
    );
    await sleep(600);

    const uploaded = await evaluate(`(() => {
      const img = document.querySelector('aside img');
      const preview = document.querySelector('img[alt="Logo de la asociación"]');
      return {
        previewSrc: preview?.getAttribute('src') ?? null,
        previewLoaded: !!preview && preview.naturalWidth > 0,
        favicon: document.querySelector('link[rel="icon"]')?.getAttribute('href') ?? null,
        sidebarSrc: img?.getAttribute('src') ?? null,
        sidebarLoaded: !!img && img.naturalWidth > 0,
        inputCleared: document.querySelector('input[type=file]').value === '',
        hasRemoveButton: Array.from(document.querySelectorAll('button')).some(b => b.innerText.trim() === 'Quitar logo'),
      };
    })()`);
    const afterUploadApi = await api.get();

    check('el nuevo logo quedó guardado en el backend', afterUploadApi.logo_path !== original.logo_path, `logo_path="${afterUploadApi.logo_path}"`);
    check('la vista previa muestra el logo subido', uploaded.previewSrc === `/imagenes/${afterUploadApi.logo_path}`, `src="${uploaded.previewSrc}"`);
    check('la vista previa carga la imagen', uploaded.previewLoaded);
    check('el sidebar usa el logo subido', uploaded.sidebarSrc === `/imagenes/${afterUploadApi.logo_path}`, `src="${uploaded.sidebarSrc}"`);
    check('el favicon se actualiza solo', uploaded.favicon === `/imagenes/${afterUploadApi.logo_path}`, `favicon="${uploaded.favicon}"`);
    check('el selector de archivo se limpia', uploaded.inputCleared);
    check('aparece el botón Quitar logo', uploaded.hasRemoveButton);

    // 3c. quitar el logo desde la UI
    await evaluate('window.confirm = () => true');
    await evaluate(`(() => {
      Array.from(document.querySelectorAll('button')).find(b => b.innerText.trim() === 'Quitar logo').click();
      return true;
    })()`);
    await waitUntil(`document.body.innerText.includes('Sin logo')`, 'que aparezca el placeholder "Sin logo"');
    await sleep(400);

    const removed = await evaluate(`(() => ({
      placeholder: document.body.innerText.includes('Sin logo'),
      previewGone: !document.querySelector('img[alt="Logo de la asociación"]'),
      sidebarLogoGone: !document.querySelector('aside img'),
      sidebarNombre: document.querySelector('aside h1')?.innerText.trim() ?? null,
      removeButtonGone: !Array.from(document.querySelectorAll('button')).some(b => b.innerText.trim() === 'Quitar logo'),
    }))()`);
    const afterRemoveApi = await api.get();

    check('el logo se borra en el backend', afterRemoveApi.logo_path === null, `logo_path="${afterRemoveApi.logo_path}"`);
    check('se muestra el placeholder "Sin logo"', removed.placeholder);
    check('la vista previa desaparece', removed.previewGone);
    check('el logo desaparece del sidebar', removed.sidebarLogoGone);
    check('el botón Quitar logo se oculta', removed.removeButtonGone);
    check('el nombre se mantiene al quitar el logo', removed.sidebarNombre === NEW_NAME, `sidebar dice "${removed.sidebarNombre}"`);
  }

  // -- 4. navegación SPA ----------------------------------------------------
  section('4. Navegación SPA');
  await goto('/admin/asociacion');
  await evaluate(`(() => {
    Array.from(document.querySelectorAll('aside a')).find(a => a.innerText.includes('Observaciones')).click();
    return true;
  })()`);
  await sleep(900);
  const spa = await evaluate(`(() => ({
    path: location.pathname,
    hasSidebar: !!document.querySelector('aside'),
    navCount: document.querySelectorAll('aside a').length,
  }))()`);
  check('navega sin recargar', spa.path === '/observaciones', `path="${spa.path}"`);
  check('el sidebar persiste tras navegar', spa.hasSidebar && spa.navCount === 5, `navItems=${spa.navCount}`);

  // -- 5. consola limpia ----------------------------------------------------
  section('5. Consola del navegador');
  const realErrors = consoleErrors.filter(e => !e.includes('favicon.ico'));
  check('sin errores ni excepciones', realErrors.length === 0, realErrors.join(' | '));
  for (const e of realErrors.slice(0, 10)) info(e);

  cdp.close();
}

// ---------------------------------------------------------------------------
// cleanup: always put the app back the way we found it
// ---------------------------------------------------------------------------
async function restore() {
  if (!original) return;
  section('Restaurando el estado original');
  try {
    const current = await api.get();
    if (current.logo_path !== original.logo_path) {
      // DELETE removes the file we uploaded; it never touches the bundled logo.jpg
      await api.deleteLogo();
      info('logo de prueba eliminado');
    }
    const restored = await api.put({ nombre: original.nombre, logo_path: original.logo_path });
    info(`nombre="${restored.nombre}" logo=${restored.logo_path ?? '(ninguno)'}`);
  } catch (err) {
    console.log(`  WARN  no pude restaurar el estado: ${err.message}`);
    console.log(`        dejalo así a mano -> nombre="${original.nombre}" logo_path="${original.logo_path}"`);
  }
}

// ---------------------------------------------------------------------------
try {
  await main();
} catch (err) {
  failures.unshift(err?.message ?? String(err));
  console.log(`\nERROR  ${err?.message ?? err}`);
  if (process.env.E2E_DEBUG) console.log(err?.stack ?? '');
} finally {
  browser?.kill();
  await sleep(300);
  if (profileDir) {
    try {
      rmSync(profileDir, { recursive: true, force: true });
    } catch {
      /* el perfil temporal puede quedar bloqueado un momento; es inofensivo */
    }
  }
  await restore();
}

console.log('');
if (failures.length === 0) {
  console.log('TODO OK');
  process.exit(0);
}
console.log(`${failures.length} verificación(es) fallaron:`);
for (const f of failures) console.log(`  - ${f}`);
process.exit(1);
