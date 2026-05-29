#!/usr/bin/env node
// Genera el proyecto Android (TWA) desde twa-manifest.json sin prompts.
// Usa la API programática de @bubblewrap/core para evitar los prompts
// interactivos del CLI (bubblewrap init/update).
//
// Uso:  node scripts/generar-twa.mjs <directorio-destino>
//       node scripts/generar-twa.mjs ./twa

import { readFile } from 'node:fs/promises';
import { existsSync, readdirSync } from 'node:fs';
import { resolve } from 'node:path';

const targetDir = resolve(process.argv[2] || '.');
const manifestPath = resolve(targetDir, 'twa-manifest.json');

console.log(`[generar-twa] target: ${targetDir}`);
console.log(`[generar-twa] manifest: ${manifestPath}`);

if (!existsSync(manifestPath)) {
  console.error(`[generar-twa] ERROR: no existe ${manifestPath}`);
  process.exit(1);
}

let bubblewrap;
try {
  bubblewrap = await import('@bubblewrap/core');
} catch (e) {
  console.error('[generar-twa] ERROR importando @bubblewrap/core:', e.message);
  process.exit(1);
}

console.log('[generar-twa] exports disponibles:', Object.keys(bubblewrap).sort().join(', '));

const { TwaManifest, TwaGenerator, ConsoleLog, Log } = bubblewrap;

if (!TwaManifest || !TwaGenerator) {
  console.error('[generar-twa] ERROR: @bubblewrap/core no expone TwaManifest/TwaGenerator');
  process.exit(1);
}

// ConsoleLog es la implementación concreta; Log puede ser la interfaz/abstract.
const LogImpl = ConsoleLog || Log;
if (!LogImpl) {
  console.error('[generar-twa] ERROR: no encontré ConsoleLog ni Log en @bubblewrap/core');
  process.exit(1);
}

let manifest;
try {
  if (typeof TwaManifest.fromJsonFile === 'function') {
    manifest = await TwaManifest.fromJsonFile(manifestPath);
  } else {
    // Fallback: construir manualmente desde el JSON
    const raw = JSON.parse(await readFile(manifestPath, 'utf8'));
    manifest = new TwaManifest(raw);
  }
} catch (e) {
  console.error('[generar-twa] ERROR cargando twa-manifest.json:', e.message);
  console.error(e.stack);
  process.exit(1);
}

console.log(`[generar-twa] manifest cargado: packageId=${manifest.packageId} name="${manifest.name}"`);

const log = new LogImpl('generar-twa');
const generator = new TwaGenerator();

try {
  await generator.createTwaProject(targetDir, manifest, log);
} catch (e) {
  console.error('[generar-twa] ERROR generando proyecto:', e.message);
  console.error(e.stack);
  process.exit(1);
}

console.log('[generar-twa] proyecto Android generado OK. Contenido:');
for (const f of readdirSync(targetDir).sort()) {
  console.log(`  - ${f}`);
}
