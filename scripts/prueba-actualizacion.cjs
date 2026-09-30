// Prueba de ACTUALIZACIÓN del banco en una instalación existente (Playwright).
//
// prueba-e2e.cjs usa un perfil nuevo, así que nunca vio el error de v1.11.0:
// el banco reparado no llegaba a quien ya tenía la app (misma versión del banco
// y el sembrado solo agrega, no borra). Esta prueba:
//
//   1. Instala la app con el banco ANTIGUO (4 017 preguntas, commit 4b4a2c8).
//   2. Simula trabajo del usuario sobre preguntas que el banco nuevo elimina:
//      una marcada con estadísticas y tarjeta de repaso, y otra editada.
//   3. Recarga con el banco actual y comprueba que se aplicó meta.reemplazos.
//
// Uso:
//   git show 4b4a2c8:data/banco_inicial.json > /tmp/banco_viejo.json
//   python3 -m http.server 8765 --bind 127.0.0.1     # desde la raíz del repo
//   node scripts/prueba-actualizacion.cjs http://localhost:8765/ /tmp/banco_viejo.json
const fs = require('fs');
const path = require('path');
const { chromium } = (() => { try { return require('playwright'); } catch (_) { return require('/opt/node22/lib/node_modules/playwright'); } })();
const BASE = process.argv[2] || 'http://localhost:8765/';
const VIEJO = process.argv[3] || '/tmp/banco_viejo.json';
let fallas = 0;
const ok = (c, m) => { if (!c) fallas++; console.log(`  ${c ? '✓' : '✗'} ${m}`); };

const bancoViejo = fs.readFileSync(VIEJO, 'utf8');
const idsViejos = new Set(JSON.parse(bancoViejo).preguntas.map((p) => p.id_unico));
const nuevo = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'data', 'banco_inicial.json'), 'utf8'));
const idsNuevos = new Set(nuevo.preguntas.map((p) => p.id_unico));
const reemplazos = nuevo.meta.reemplazos;
// Dos eliminadas que existían en el banco viejo, con supervivientes distintas.
const candidatas = Object.entries(reemplazos).filter(([v, n]) => idsViejos.has(v) && idsNuevos.has(n));
const [marcada, supMarcada] = candidatas[0];
const [editada] = candidatas.find(([, n]) => n !== supMarcada);

// Una pregunta que sobrevive pero cuya justificación se reparó: debe llegar el
// texto nuevo (con el criterio antiguo de "editada" se conservaba el viejo).
const viejasPorId = new Map(JSON.parse(bancoViejo).preguntas.map((p) => [p.id_unico, p]));
const reparada = nuevo.preguntas.find((p) => viejasPorId.has(p.id_unico) && p.id_unico !== supMarcada &&
  viejasPorId.get(p.id_unico).justificacion !== p.justificacion);

// Lee o escribe en IndexedDB desde la página.
const idb = (page, fn, arg) => page.evaluate(([src, a]) => new Promise((res, rej) => {
  const r = indexedDB.open('eunacom_db');
  r.onerror = () => rej(r.error);
  r.onsuccess = () => { const db = r.result; new Function('db', 'a', 'res', src)(db, a, res); };
}), [fn, arg]);

(async () => {
  const browser = await chromium.launch();
  // Sin service worker: así page.route controla qué banco se descarga.
  const context = await browser.newContext({ serviceWorkers: 'block' });
  const page = await context.newPage();
  const errores = [];
  page.on('pageerror', (e) => errores.push(e.message));
  page.on('console', (m) => { if (m.type() === 'error') errores.push(m.text()); if (process.env.DEBUG) console.log('   [consola]', m.type(), m.text().slice(0, 300)); });

  console.log('1) INSTALACIÓN CON EL BANCO ANTIGUO');
  const metaViejo = JSON.stringify({ version: 'reconstruccion_v13_polish', total: idsViejos.size });
  await page.route('**/data/banco_inicial.json', (r) => r.fulfill({ body: bancoViejo, contentType: 'application/json' }));
  await page.route('**/data/banco_meta.json', (r) => r.fulfill({ body: metaViejo, contentType: 'application/json' }));
  await page.goto(BASE);
  await page.waitForSelector('#splash', { state: 'detached', timeout: 120000 });
  const n0 = await idb(page, `const c = db.transaction('preguntas').objectStore('preguntas').count(); c.onsuccess = () => res(c.result);`);
  ok(n0 === idsViejos.size, `sembradas ${n0} preguntas del banco antiguo`);

  console.log(`2) TRABAJO DEL USUARIO: marca+estadísticas+repaso en ${marcada}; edición en ${editada}`);
  await idb(page, `
    const t = db.transaction(['preguntas', 'repaso'], 'readwrite');
    const ps = t.objectStore('preguntas');
    const g1 = ps.get(a.marcada);
    g1.onsuccess = () => { const p = g1.result; p.marcada_revision = true;
      p.estadisticas_usuario = { veces_respondida: 3, veces_correcta: 2, ultima_vez: '2026-09-01T10:00:00.000Z' }; ps.put(p); };
    const g2 = ps.get(a.editada);
    g2.onsuccess = () => { const p = g2.result; p.version_actual = 3; p.enunciado = 'EDITADA POR EL USUARIO ' + p.enunciado;
      p.historial_ediciones = [{ version: 3, fecha: '2026-09-20', fuente: 'Prueba', nota: null }]; ps.put(p); };
    t.objectStore('repaso').put({ ref: 'pregunta:' + a.marcada, tipo: 'pregunta', id: a.marcada, ef: 2.6,
      intervalo: 6, repeticiones: 2, proxima_revision: '2026-10-05', ultima: '2026-09-29' });
    t.oncomplete = () => res(true);`, { marcada, editada });

  console.log('3) ACTUALIZACIÓN AL BANCO ACTUAL');
  await page.unroute('**/data/banco_inicial.json');
  await page.unroute('**/data/banco_meta.json');
  await page.reload();
  await page.waitForSelector('#splash', { state: 'detached', timeout: 120000 });
  await page.waitForTimeout(300);
  const estado = await idb(page, `
    const t = db.transaction(['preguntas', 'repaso', 'config']);
    const ps = t.objectStore('preguntas'), rs = t.objectStore('repaso');
    const out = {};
    const c = ps.count(); c.onsuccess = () => out.n = c.result;
    const a1 = ps.get(a.marcada); a1.onsuccess = () => out.vieja = !!a1.result;
    const a2 = ps.get(a.sup); a2.onsuccess = () => out.sup = a2.result;
    const a3 = ps.get(a.editada); a3.onsuccess = () => out.editada = a3.result;
    const a4 = ps.get(a.reparada); a4.onsuccess = () => out.reparada = a4.result;
    const r1 = rs.get('pregunta:' + a.marcada); r1.onsuccess = () => out.tarjetaVieja = !!r1.result;
    const r2 = rs.get('pregunta:' + a.sup); r2.onsuccess = () => out.tarjetaNueva = r2.result;
    const v = t.objectStore('config').get('seed_banco_version'); v.onsuccess = () => out.version = v.result && v.result.value;
    t.oncomplete = () => res(out);`, { marcada, sup: supMarcada, editada, reparada: reparada.id_unico });

  ok(estado.version === nuevo.meta.version, `versión sembrada: ${estado.version}`);
  ok(estado.n === idsNuevos.size + 1, `quedan ${estado.n} preguntas (${idsNuevos.size} del banco + 1 editada por el usuario)`);
  ok(!estado.vieja, `${marcada} eliminada`);
  ok(estado.sup && estado.sup.marcada_revision === true, `marca traspasada a ${supMarcada}`);
  const e = estado.sup && estado.sup.estadisticas_usuario;
  ok(e && e.veces_respondida === 3 && e.veces_correcta === 2, `estadísticas traspasadas (${e && e.veces_correcta}/${e && e.veces_respondida})`);
  ok(!estado.tarjetaVieja, 'tarjeta de repaso antigua borrada');
  ok(estado.tarjetaNueva && estado.tarjetaNueva.id === supMarcada && estado.tarjetaNueva.intervalo === 6,
    `tarjeta de repaso traspasada (${estado.tarjetaNueva && estado.tarjetaNueva.ref}, intervalo ${estado.tarjetaNueva && estado.tarjetaNueva.intervalo})`);
  ok(estado.reparada && estado.reparada.justificacion === reparada.justificacion,
    `${reparada.id_unico} recibe la justificación reparada del banco nuevo`);
  ok(estado.reparada && (estado.reparada.version_actual || 1) === 1 && !(estado.reparada.historial_ediciones || []).length,
    `${reparada.id_unico} no queda marcada como editada`);
  ok(estado.editada && estado.editada.enunciado.startsWith('EDITADA POR EL USUARIO'), `${editada}, editada por el usuario, se conserva intacta`);
  ok(errores.length === 0, `sin errores de consola${errores.length ? ': ' + errores.slice(0, 3).join(' | ') : ''}`);

  await browser.close();
  console.log(fallas ? `\n${fallas} FALLA(S)` : '\nTODO OK');
  process.exit(fallas ? 1 : 0);
})();
