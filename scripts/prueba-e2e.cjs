// Prueba de punta a punta de InternOS en Chromium (Playwright).
//
// Cubre las regresiones de la auditoría de sept-2026: atajos de teclado del
// runner, «Ver resultados», registro de sesiones (onFinish), anuncios
// accesibles, fecha local en por_dia y el router bajo navegación rápida.
// Contra la v1.10.1 esta prueba falla (atajos muertos, 0 sesiones).
//
// Uso:
//   python3 -m http.server 8765 --bind 127.0.0.1     # desde la raíz del repo
//   node scripts/prueba-e2e.cjs http://localhost:8765/
//
// Requiere Playwright con Chromium. Usa un perfil de navegador nuevo, así que
// la primera carga siembra el banco completo en IndexedDB.
const { chromium } = (() => { try { return require('playwright'); } catch (_) { return require('/opt/node22/lib/node_modules/playwright'); } })();
const BASE = process.argv[2] || 'http://localhost:8765/';
const ok = (c, m) => console.log(`  ${c ? '✓' : '✗'} ${m}`);

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const errores = [];
  page.on('pageerror', (e) => errores.push(e.message));
  page.on('console', (m) => { if (m.type() === 'error') errores.push(m.text()); });

  await page.goto(BASE);
  await page.waitForSelector('#splash', { state: 'detached', timeout: 90000 });
  const nPreg = await page.evaluate(() => new Promise((res) => {
    const r = indexedDB.open('eunacom_db');
    r.onsuccess = () => { const c = r.result.transaction('preguntas').objectStore('preguntas').count(); c.onsuccess = () => res(c.result); };
  }));
  console.log('ARRANQUE');
  ok(nPreg > 0, `banco sembrado en IndexedDB: ${nPreg} preguntas`);

  console.log('SESIÓN VELOZ (respondiendo con el teclado)');
  await page.getByRole('button', { name: /20 preguntas rápidas/ }).click();
  await page.waitForSelector('.opcion');
  const pb = await page.getAttribute('.progress', 'role');
  const pbTxt = await page.getAttribute('.progress', 'aria-valuetext');
  ok(pb === 'progressbar', `barra de progreso con role="progressbar" ("${pbTxt}")`);
  ok(await page.getAttribute('.opciones', 'role') === 'group', 'alternativas agrupadas con role="group"');
  const focoInicial = await page.evaluate(() => document.activeElement && document.activeElement.className);
  ok(focoInicial === 'enunciado__texto', `foco en la pregunta al empezar (${focoInicial})`);

  // Tecla "1" = alternativa A. Antes del fix de runMcq esto no hacía nada.
  await page.keyboard.press('1');
  const bloqueadas = await page.locator('.opcion--bloqueada').count();
  ok(bloqueadas > 0, `atajo de teclado "1" responde la pregunta (${bloqueadas} alternativas bloqueadas)`);
  const anuncio = await page.textContent('[role="status"]');
  ok(/^(Correcto\.|Incorrecto\. La correcta es la [A-E]: .+)$/.test(anuncio), `anuncio para lector de pantalla: "${anuncio.slice(0, 70)}"`);
  const estados = await page.locator('.opcion__estado').allTextContents();
  ok(estados.some((s) => s.includes('Correcta')), `estado en texto, no solo color: [${estados.join(' | ')}]`);
  ok((await page.locator('.opcion[aria-disabled="true"]').count()) === bloqueadas, 'alternativas marcadas aria-disabled tras responder');

  await page.keyboard.press('Enter');
  await page.waitForFunction(() => !document.querySelector('.opcion--bloqueada'));
  const focoSig = await page.evaluate(() => document.activeElement && document.activeElement.className);
  ok(focoSig === 'enunciado__texto', `Enter avanza y el foco pasa a la pregunta nueva (${focoSig})`);

  // Responder el resto con teclado hasta la última.
  for (let k = 0; k < 40; k++) {
    await page.keyboard.press('2');
    const ver = page.getByRole('button', { name: 'Ver resultados' });
    if (await ver.count()) { await ver.click(); break; }
    await page.keyboard.press('Enter');
    await page.waitForFunction(() => !document.querySelector('.opcion--bloqueada'));
  }
  const resultado = await page.locator('h2', { hasText: 'Resultado de la sesión' }).count();
  ok(resultado === 1, '«Ver resultados» muestra la pantalla de resultado');
  await page.waitForTimeout(500);
  const sesiones = await page.evaluate(() => new Promise((res) => {
    const r = indexedDB.open('eunacom_db');
    r.onsuccess = () => {
      const g = r.result.transaction('progreso_usuario').objectStore('progreso_usuario').get('global');
      g.onsuccess = () => res(g.result ? { s: (g.result.sesiones || []).length, dias: Object.keys(g.result.por_dia || {}) } : null);
    };
  }));
  ok(sesiones && sesiones.s >= 1, `onFinish corrió: sesiones registradas = ${sesiones && sesiones.s}`);
  const hoyLocal = await page.evaluate(() => { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`; });
  ok(sesiones && sesiones.dias.includes(hoyLocal), `por_dia usa la fecha local (${hoyLocal})`);

  console.log('ROUTER (navegación rápida durante un render lento)');
  await page.evaluate(() => { location.hash = '#/quiz'; setTimeout(() => { location.hash = '#/progreso'; }, 5); });
  await page.waitForTimeout(2500);
  const hashFinal = await page.evaluate(() => location.hash);
  const titulo = await page.evaluate(() => (document.querySelector('#vista h2') || {}).textContent || '');
  ok(hashFinal === '#/progreso' && !/Quiz|filtr/i.test(titulo), `URL ${hashFinal} y la vista coincide ("${titulo.trim().slice(0, 40)}")`);

  console.log('ERRORES DE CONSOLA');
  const relevantes = errores.filter((e) => !/favicon|manifest/i.test(e));
  ok(relevantes.length === 0, relevantes.length ? relevantes.slice(0, 5).join(' || ') : 'ninguno');
  await browser.close();
})().catch((e) => { console.error('FALLO DE LA PRUEBA:', e.message); process.exit(1); });
