# InternOS — contexto del proyecto

PWA de estudio para el **EUNACOM** (examen médico nacional chileno), diseñada
para funcionar **100% offline** en tablet Android. Todo el contenido está en
español de Chile.

## Stack

- **JavaScript vanilla con módulos ES**. Sin framework, sin bundler, sin
  build step para la web: `index.html` carga `src/app.js` como `type="module"`.
- **IndexedDB** como única persistencia (wrapper propio en `src/db/db.js`,
  sin librerías). Versión de esquema actual: **3**.
- **Service Worker** cache-first (`service-worker.js`).
- **Capacitor 6** para el APK Android nativo (assets embebidos, offline desde
  la instalación).
- CSS plano con variables en `:root` (`styles/app.css`). **Dos paletas
  conviven**: la general de la app es teal (`--accent: #0d8a8c`) y la de
  biblioteca es café/crema tomada del logo (`--b-accent: #6b4423`).

No agregar dependencias npm al runtime web. Las únicas dependencias del repo
(`package.json`) son de Capacitor y solo se usan para compilar el APK.

## Estructura

```
src/
  app.js              arranque, registro del SW, router
  db/db.js            wrapper IndexedDB + cache in-memory de getAll()
  db/seed.js          siembra inicial desde data/*.json
  db/stats.js         progreso del usuario
  repaso/sm2.js       repetición espaciada SM-2
  ui/                 dom.js (el/mount/modal/toast), router.js, mcq.js,
                      home.js, ajustes.js, progreso.js, iconos.js, imagen.js
  modos/              quiz-temas, casos-clinicos, definiciones, biblioteca,
                      marcadas, listado-preguntas
  editor/editor.js    edición con trazabilidad (fuente obligatoria)
  importar/           parser .md e importación
data/
  banco_inicial.json          4 017 preguntas (8 MB, JSON compacto en 1 línea)
  biblioteca.json             332 entradas / 23 unidades (pretty-print, indent 2)
  casos_iniciales.json        26 casos clínicos
  definiciones_iniciales.json 50 definiciones
  referencias/
    perfil_eunacom_2026.json   1 557 ítems del Perfil oficial (ASOFAMECh)
    cobertura_banco_2026.json  cobertura del banco por código del Perfil
```

**Formato de los JSON de datos**: `banco_inicial.json` va **compacto**
(`separators=(',',':')`, una sola línea); `biblioteca.json` va
**pretty-print con `indent=2`**. Respetarlo o el diff se vuelve ilegible.

## Convenciones

- **Idioma**: todo el contenido, los comentarios del código, los mensajes de
  commit y la UI van en **español**. Los identificadores en el código van en
  español también (`vistaBiblioteca`, `cargarEntradas`, `sanitizarHTML`).
- **HTML de biblioteca**: cada entrada usa bloques
  `<div class="section-subsection">` con un `<h3>` por sección. Todo HTML que
  se inyecta pasa por `sanitizarHTML()` (allow-list de tags/atributos).
- **Blob URLs**: se trackean por vista y se liberan en el evento
  `vista:cambia` para no filtrar memoria.
- **Íconos**: SVG inline en `src/ui/iconos.js`. No usar CDN de íconos ni de
  fuentes — rompe el modo offline.
- **Versionado**: `VERSION` en la raíz. Los placeholders `__APP_VERSION__`,
  `__GIT_SHA__` y `__BUILD_DATE__` los sella el workflow de deploy.

## Git

- Rama de trabajo: **`claude/eunacom-android-app-hTWHI`**. Desarrollar y
  pushear ahí, luego merge a `main` con `--no-ff`.
- Nunca pushear a otra rama sin permiso explícito.
- No crear pull requests salvo que se pidan.

## CI / despliegue

| Workflow | Dispara | Produce |
|---|---|---|
| `deploy-pages.yml` | push a `main` | PWA en GitHub Pages |
| `build-android-app.yml` | push a `main` que toque la PWA | APK nativo (Capacitor) → release `v<VERSION>-native` |
| `build-apk.yml` | tag `v*` o manual | APK TWA firmado (envuelve la URL pública) |

El APK de Capacitor (`cl.internos.offline`) es el que funciona sin red desde
la instalación. El TWA (`cl.internos.app`) depende de GitHub Pages.

Trampas conocidas del CI: `ubuntu-latest` ya **no** trae ImageMagick
preinstalado, y `native` es palabra reservada de Java (no usarla en el
`appId`).

## Verificación antes de dar algo por terminado

```bash
node --check src/<archivo>.js          # sintaxis de cada JS tocado
python3 -c "import json; json.load(open('data/<archivo>.json'))"   # JSON válido
```

Para cambios de datos, comprobar además el conteo de entradas antes/después.

## Skills instaladas

Ver [`.claude/SKILLS.md`](.claude/SKILLS.md). Las más pertinentes aquí:
`systematic-debugging`, `verification-before-completion`, `writing-plans`,
`accessibility` y los subagents `javascript-pro`, `code-reviewer`,
`accessibility-tester`, `mobile-developer`.
