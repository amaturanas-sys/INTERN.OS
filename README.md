# InternOS — PWA de estudio EUNACOM offline

Plataforma de estudio EUNACOM como **Progressive Web App instalable**, pensada para
una **tablet Android** y diseñada para funcionar **100% offline**. Tres modos de
estudio, banco editable con trazabilidad, soporte de imágenes, importación de
material `.md` y repaso espaciado SM-2.

> Fuente del contenido: material del Dr. Guevara + síntesis de guías clínicas
> 2024-2026 (GINA, GOLD, ESC, AHA, ADA, AACE, SSC, ACG). Banco actual: **4 017
> preguntas**, **26 casos clínicos** y **50 definiciones** (fármacos, conceptos,
> herramientas y guías).

## Qué incluye

- **Modo 1 · Quiz por temas** — MCQ clásico con filtros (especialidad, tema, sistema
  Behrens, dificultad, frecuencia EUNACOM), feedback inmediato y estadísticas.
- **Modo 2 · Casos clínicos** — casos paso a paso, **lineales con feedback** (si te
  equivocas el caso continúa), con resumen y evaluación global.
- **Modo 3 · Definiciones** — conceptos, fármacos y herramientas diagnósticas en formato MCQ.
- **Editor con trazabilidad** — edición completa de cualquier ítem, con **fuente
  obligatoria**, nota opcional, **historial de versiones** y badge "editado".
- **Imágenes de apoyo** — adjuntables a cualquier ítem desde un fichero local; preguntas
  que *requieren* imagen quedan fuera del quiz hasta adjuntarla.
- **Importación `.md`** — selector de archivos, previsualización e incorporación a IndexedDB.
- **Repaso espaciado (SM-2)** — capa opcional sobre los tres modos ("práctica libre" vs "modo repaso").
- **Respaldo** — exportar / restaurar todo el banco y el progreso como JSON.

## Cómo instalarla en la tablet Android

La app es estática; necesita servirse por **HTTPS** (requisito de las PWA). La vía más
simple es **GitHub Pages**:

1. En el repositorio: *Settings → Pages → Build and deployment → Source: "Deploy from a
   branch"*, rama `claude/eunacom-android-app-hTWHI` (o `main` tras el merge), carpeta `/ (root)`.
2. Abre la URL pública (`https://<usuario>.github.io/<repo>/`) en **Chrome** en la tablet.
3. Menú de Chrome → **"Agregar a la pantalla de inicio" / "Instalar app"**.
4. Ábrela desde el ícono: se ejecuta a pantalla completa y, tras la primera carga,
   **funciona sin conexión** (el Service Worker cachea todo y los datos viven en IndexedDB).

### Prueba local (en el computador)

```bash
python3 -m http.server 8099
# abrir http://localhost:8099
```

## Estructura del proyecto

```
.
├── index.html                  shell de la PWA
├── manifest.webmanifest        configuración de instalación
├── service-worker.js           cache offline de toda la app
├── styles/app.css
├── src/
│   ├── app.js                  entrada: rutas, seed, registro del SW
│   ├── db/                     IndexedDB (db.js: schema+migraciones, seed.js, stats.js)
│   ├── modos/                  quiz-temas.js · casos-clinicos.js · definiciones.js
│   ├── editor/editor.js        corrección manual + historial + imágenes
│   ├── importar/               md-parser.js (convención .md) + importar.js
│   ├── repaso/sm2.js           algoritmo de repaso espaciado
│   └── ui/                     dom, router, mcq runner, home, progreso, ajustes, imagen
├── data/
│   ├── banco_inicial.json      preguntas precargadas (Modo 1)
│   ├── casos_iniciales.json    casos (Modo 2)
│   └── definiciones_iniciales.json (Modo 3)
├── assets/                     íconos PWA
└── scripts/gen_icons.py        generador de íconos PNG
```

Sin backend, sin dependencias externas y sin paso de build: JavaScript vanilla con
módulos ES, para cargar rápido y cachear de forma confiable offline.

## Cargar el banco completo (2.610 preguntas)

Dos opciones:

1. **Reemplazar el JSON precargado:** sustituye `data/banco_inicial.json` por el banco
   completo (mismo schema de 27 campos + `version_actual`, `historial_ediciones`,
   `estadisticas_usuario` e `imagen`). En la primera apertura se siembra en IndexedDB.
   Para reseed en un dispositivo ya usado: *Ajustes → Borrar todos los datos*.
2. **Importador `.md`:** genera archivos `.md` con la convención de abajo y cárgalos
   desde *Inicio → Importar material*.

## Convención del formato `.md`

Front-matter YAML + cuerpo estructurado. Un archivo puede contener varios ítems, cada uno
con su propio front-matter. La marca `(x)` indica la alternativa correcta. Tras `|` en una
opción puedes añadir feedback (útil en casos).

**Pregunta (mcq):**
```markdown
---
tipo: mcq
especialidad: cardio
tema: HTA
dificultad: intermedia
---
# Pregunta
Hombre de 65 años, diabético, PA 160/95...

## Opciones
- (x) Iniciar IECA
- ( ) Iniciar betabloqueador
- ( ) Observar

## Justificación
En diabéticos, los IECA son primera línea porque...
```

**Definición (definicion):** añade `concepto:` y `subtipo:` (`farmaco` / `concepto` /
`herramienta`); usa `## Explicación` en vez de `## Justificación`.

**Caso (caso):** estructura el cuerpo en etapas:
```markdown
---
tipo: caso
titulo: Dolor torácico en adulto mayor
especialidad: cardio
tema: SCA
dificultad: intermedia
---
## Etapa: anamnesis
Hombre de 65 años con dolor torácico. ¿Qué preguntar?
### Opciones
- (x) Caracterizar el dolor | Correcto, orienta a SCA
- ( ) Antecedentes quirúrgicos | Poco relevante

## Etapa: manejo
ECG con SDST inferior. ¿Conducta?
### Opciones
- (x) Angioplastia primaria
- ( ) Observar

## Resumen
IAM con SDST: reperfundir dentro de los tiempos.
```

## Estado respecto a las fases del documento

| Fase | Estado |
|---|---|
| 0 · Preparación de datos | Schema implementado; banco de **muestra** cardiología (falta integrar las 2.610 reales) |
| 1 · Esqueleto PWA offline | ✅ index + manifest + service worker + IndexedDB sembrada |
| 2 · Modo 1 (Quiz) | ✅ filtros, feedback, estadísticas, imágenes |
| 3 · Editor + imágenes | ✅ editor completo, historial, badge, adjuntar/“requiere” imagen |
| 4 · Modo 3 (Definiciones) | ✅ funcional (falta extracción masiva de los `_extractos.md`) |
| 5 · Modo 2 (Casos) | ✅ etapas lineales con feedback (faltan casos masivos desde transcripciones) |
| 6 · Repaso espaciado | ✅ SM-2 como capa opcional en los tres modos |
| 7 · Importación `.md` | ✅ parser + selector + previsualización para los tres tipos |

Lo pendiente es **contenido** (poblar el banco real y construir casos/definiciones a partir
del material de Guevara), no infraestructura: la app ya soporta todo el flujo.
```
