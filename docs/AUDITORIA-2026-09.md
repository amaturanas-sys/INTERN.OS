# Auditoría InternOS — septiembre 2026

Versión auditada: **1.10.1** · rama `claude/eunacom-android-app-hTWHI`

Alcance: código (`src/`, `service-worker.js`), datos (`data/`), accesibilidad
(WCAG 2.2 AA) y contenido contra el material fuente del Dr. Guevara.

Todos los hallazgos marcados **[verificado]** fueron comprobados leyendo el
código o ejecutando un script sobre los datos reales, no inferidos.

---

## Resumen ejecutivo

| # | Hallazgo | Alcance | Severidad | Estado |
|---|---|---|---|---|
| 1 | `runMcq` se auto-cancela al montarse: `onFinish` nunca corre | Todas las sesiones | 🔴 Crítico | ✅ v1.10.2 |
| 2 | Bug del parser: justificación pegada a una opción incorrecta | 1.502 preguntas (37%) | 🔴 Crítico | ✅ v1.11.0 — quedan 15 |
| 3 | El banco tiene 4.017 preguntas pero ~2.500 distintas | 2.957 preguntas (74%) | 🔴 Crítico | ✅ v1.11.0 |
| 4 | La app queda inutilizable offline tras cada deploy | Todos los usuarios | 🔴 Crítico | ✅ v1.10.2 |
| 5 | Re-sembrar borra marcas, ediciones y estadísticas | Todos los usuarios | 🔴 Crítico | ✅ v1.10.2 |
| 6 | 15 grupos con respuesta correcta contradictoria | 16 grupos | 🟠 Alto | ✅ v1.11.0 |
| 7 | Etiquetas `tema_validado` no confiables | 6 temas mayores | 🟠 Alto | ✅ mitigado v1.11.0 |
| 8 | El router descarta navegaciones | Navegación rápida | 🟠 Alto | ⏳ pendiente |
| 9 | Recarga forzada durante la primera instalación | Primera visita | 🟠 Alto | ⏳ pendiente |
| 10 | Accesibilidad: contraste, ARIA, `aria-live` | Pantalla principal | 🟡 Medio | ⏳ pendiente |
| 11 | Corrupción de ligadura fl→fi del PDF original | 306 preguntas | 🟠 Alto | ✅ v1.11.0 |

### Hallazgo 11 — descubierto durante la reparación

La extracción del PDF original corrompió la ligadura tipográfica **fl → fi**
en 306 preguntas: `refiejos`, `infiuenza`, `infiamatorio`, `fiujo`,
`hiperfiexión`. Apareció al revisar los "grupos contradictorios": 11 de los 16
no eran contradicciones sino la misma respuesta con el texto corrompido.

Tiene una consecuencia de orden: **hay que corregirlo antes de deduplicar**, o
las copias con `refiejos` y con `reflejos` no se ven iguales y ambas
sobreviven. En la primera corrida quedaron 21 duplicados por esto.

---

## 1. 🔴 `runMcq` se auto-cancela al montarse — `onFinish` nunca se ejecuta

**[verificado con simulación del orden de eventos]**

`src/ui/mcq.js:216` registra un listener de `vista:cambia` sobre `document`:

```js
document.addEventListener("vista:cambia", limpiezaPorRuta, { signal: limpieza.signal });
```

y `src/ui/mcq.js:260` llama `mount(cont)`, que en `src/ui/dom.js:49` despacha
**ese mismo evento de forma síncrona**, antes incluso del `appendChild`:

```js
document.dispatchEvent(new CustomEvent("vista:cambia"));
root.appendChild(view);
```

El runner se escucha a sí mismo. Al montarse ejecuta `limpiezaPorRuta()`, que
pone `terminada = true` y aborta el `AbortController`.

Simulación con el orden real:

```
tras mount():  terminada = true | signal.aborted = true
finalizar():   onFinish llamado = false
```

**Qué rompe:**

- **Los atajos de teclado 1-9 y a-e quedan muertos** desde el primer ítem (el
  listener de `keydown` comparte el signal abortado).
- **«Ver resultados» y «Salir» no hacen nada**: `finalizar()` sale en el guard
  `if (terminada) return`.
- **Ninguna sesión se registra**. `onFinish` → `registrarSesion` nunca corre,
  así que el historial de sesiones queda permanentemente vacío.

**Qué sigue funcionando** (y por eso el problema pasa desapercibido): responder
y avanzar con el mouse/dedo funciona, porque son handlers de elemento. Y las
estadísticas por pregunta sí se guardan, porque `onAnswer` se llama en
`mcq.js:163`, fuera de este camino.

**Arreglo:** mover `mount(cont)` **antes** de registrar los listeners, o
diferir el registro con `queueMicrotask`.

---

## 2. 🔴 Bug del parser en 1.502 preguntas, no en 25

**[verificado con dos señales independientes + muestreo manual]**

En v1.9.1 se corrigieron 25 preguntas donde la justificación quedaba pegada al
final de la última opción. Esas 25 eran las que el curador encontró estudiando,
no el universo del problema.

| Señal | Preguntas |
|---|---:|
| Última opción desproporcionada (>2,2× la mayor del resto, >90 chars) | 1.713 |
| Justificación que empieza en minúscula (truncada a media frase) | 2.281 |
| **Ambas** | **1.502 (37,4%)** |
| Al menos una | 2.492 (62%) |

Muestra aleatoria de 8 casos inspeccionados a mano: **8/8 genuinos**, sin
falsos positivos.

**En el 100% de los 1.502 casos el texto pegado está en una opción incorrecta.**
Es la peor configuración: el estudiante ve un párrafo explicativo colgando de
una alternativa, ese párrafo argumenta a favor de *otra*, y la justificación
que debería aclararlo arranca cortada.

Ejemplo, `R00001` (correcta = **b**):

> **e)** Iniciar atenolol y controlar en 3 meses más *Actualmente el objetivo de
> control de presión arterial en pacientes en general, es menor a 140/90…*
>
> **justificación:** *"debió haber iniciado directamente con tratamiento
> farmacológico…"*

**Nota metodológica:** una primera medición automatizada dio 341 casos. Usaba un
umbral de ~200 caracteres para la última opción y perdía los casos cortos
(`R01825` = 96 chars, `R00454` = 94 chars), que son igual de reales. El umbral
correcto es 90.

**Arreglo:** el patrón es consistente y reparable de forma programática —
cortar el texto de la última opción donde arranca la justificación y reponerlo
al inicio de esta. Validar sobre muestra antes de aplicar al banco completo.

---

## 3. 🔴 El banco tiene 4.017 preguntas pero ~2.500 distintas

**[verificado]**

| | |
|---|---:|
| Preguntas en el banco | 4.017 |
| **Enunciados distintos** | **2.498** |
| Grupos duplicados | 1.438 |
| Preguntas involucradas | **2.957 (73,6%)** |

Los IDs `R0xxxx` y `GUEV-<ESP>-xxxx` son el mismo pool importado dos o tres
veces.

**Consecuencias:**

- El repaso espaciado **SM-2 asume ítems únicos**. Con 74% de duplicados
  programa como "nuevo" algo ya respondido, y el acierto se infla.
- La tarjeta del Home anuncia 4.017 preguntas: un 60% más de lo real.

---

## 4. 🔴 La app queda inutilizable offline tras cada deploy

**[reportado por la revisión de código]**

`banco_inicial.json` (8 MB) está deliberadamente fuera de `ASSETS`, pero
`service-worker.js:69` borra en `activate` **todas** las cachés cuyo nombre no
coincida con el `CACHE` nuevo — incluida la copia bajo demanda del banco.

Secuencia: usuario con la PWA sembrada → se publica un deploy (rota el SHA) →
el SW nuevo purga la caché vieja → el usuario abre la app **sin red** →
`banco_meta.json` sí está precacheado y reporta versión nueva → no coincide con
`seed_banco_version` → `seedIfNeeded` intenta re-sembrar → el `fetch` del banco
falla → `respondWith(undefined)` lanza `TypeError` → `app.js:76-79` muestra
"Error al cargar el banco inicial" y **retorna sin llamar a `iniciarRouter()`**.

La app se queda en el splash **teniendo las 4.017 preguntas intactas en
IndexedDB**.

**Arreglo (los tres son necesarios):**
1. `seedIfNeeded` debe devolver `{sembrado:false}` si ya hay preguntas y el
   banco no se puede descargar.
2. `app.js` debe arrancar el router igual si la siembra falla con la DB poblada.
3. `activate` debe preservar `data/*.json` al purgar.

---

## 5. 🔴 Re-sembrar borra marcas, ediciones y estadísticas del usuario

**[reportado por la revisión de código]**

`src/db/seed.js:47` hace `bulkPut("preguntas", banco.preguntas)`, que
**reemplaza los registros completos**. Pero el estado del usuario vive dentro de
esos mismos registros: `marcada_revision` (`mcq.js:25`), `estadisticas_usuario`
(`stats.js:32-35`) y las ediciones del editor (`editor.js:199`).

Un usuario que marca 40 preguntas y corrige 10 las pierde todas, sin aviso, la
próxima vez que se publique una versión del banco.

**Arreglo:** merge campo a campo con lo existente, o mover el estado de usuario
a un store aparte.

---

## 6. 🟠 Quince grupos con respuesta correcta contradictoria

**[verificado]**

Mismo enunciado, mismas opciones, distinta alternativa marcada como correcta
según la copia:

> *"Embarazada de 30 semanas… lesiones eritematosas… prurito"* (sarna en embarazo)
>
> - `R00264` → **e) Vaselina azufrada**
> - `R01572` → **d) Permetrina tópica al 5%**
> - `GUEV-OBS-0110` → **d) Permetrina tópica al 5%**

Permetrina 5% es el estándar actual en embarazo; `R00264` quedó con la conducta
antigua. Según qué copia le toque, el estudiante aprende una cosa u otra.

---

## 7. 🟠 Las etiquetas `tema_validado` no son confiables

**[verificado]**

Midiendo si cada pregunta menciona su propio tema:

| Tema | Preguntas | Coherentes |
|---|---:|---:|
| Valvulopatias | 31 | **3%** |
| Acne | 40 | **12%** |
| Arritmias | 25 | 24% |
| Control_prenatal | 24 | 21% |
| Epilepsia | 18 | 28% |
| Antibioticoterapia | 13 | 38% |
| Ca_prostata | 15 | 100% ✓ |
| Diabetes_MI | 17 | 94% ✓ |
| Cefalea | 23 | 91% ✓ |

Hay bloques correctos y bloques asignados por lote. Las 31 preguntas de
"Valvulopatias" incluyen **una sola** sobre valvulopatías.

**Impacto sobre el indexado de v1.10.1:** de las 504 preguntas marcadas
`tema_directo` confiando en esa etiqueta, **~140 tienen el `codigo_perfil` mal
asignado**. También afecta al filtro por tema del quiz.

---

## 8. 🟠 El router descarta navegaciones

`src/ui/router.js:43-50` mantiene `renderEnCurso = true` durante todo el
`await m.handler(...)`, que en vistas como `vistaQuizFiltros` incluye un
`getAll("preguntas")` de 4.017 registros (cientos de ms en tablet). Un
`hashchange` en esa ventana **se pierde para siempre**: la URL ya cambió pero
la vista no, y nada vuelve a renderizar.

Repro: desde Inicio tocar "Quiz" y, sin esperar, tocar "Progreso".

---

## 9. 🟠 Recarga forzada durante la primera instalación

`src/app.js:93-98` no distingue la primera toma de control del SW de una
actualización real. En la primera visita el SW instala → `skipWaiting()` →
`clients.claim()` → dispara `controllerchange` → `location.reload()` **mientras
se están descargando los 8 MB**. El usuario baja el banco dos veces.

**Arreglo:** guardar `const habiaControlador = !!navigator.serviceWorker.controller`
al inicio y recargar solo si era `true`.

---

## 10. 🟡 Accesibilidad (WCAG 2.2 AA)

**[afirmaciones verificadas contra el CSS y el JS reales]**

| Archivo | Problema | Criterio |
|---|---|---|
| `app.css:261` | `.btn:disabled { opacity: .45 }` baja el contraste bajo 4.5:1 | 1.4.3 |
| `mcq.js:102` | Feedback de respuesta sin `aria-live` — quien usa lector de pantalla no sabe si acertó | 4.1.3 |
| `mcq.js:106` | Opciones sin rol ARIA: se anuncian como "botón" genérico | 4.1.2 |
| `mcq.js:88` | Barra de progreso sin `role="progressbar"` | 1.3.1 |
| `mcq.js:196` | Atajos aceptan `a`–`i` cuando el máximo son 5 opciones | 2.4.1 |
| `dom.js:76` | `foco_previo.focus()` sin validar que siga en el DOM | 2.4.3 |

---

## 11. Otros hallazgos de código (medio / bajo)

- **`dom.js:69-128`** — los modales sobreviven al cambio de vista. Con el botón
  Atrás de Android el overlay queda tapando la pantalla con su focus-trap activo,
  y cada modal huérfano acumula un listener.
- **`dom.js:49`** — `vista:cambia` se despacha cuando la vista entrante ya
  construyó sus recursos. En `biblioteca.js:582` las blob URLs se registran antes
  del `mount()` de la línea 604, que las revoca. Hoy suele salvarse por carrera;
  bajo presión de memoria las imágenes quedan en blanco. Misma causa raíz que #1.
- **`db.js:21-39`** — `_dbPromise` cachea el rechazo de forma permanente. Si
  `open()` falla por `onblocked`, toda operación posterior falla hasta recargar.
  Falta `db.onversionchange`.
- **`db.js:104-151`** — `put`/`del`/`clearStore` resuelven en `request.onsuccess`,
  no en `transaction.oncomplete`, y nadie escucha `onabort`. Un abort posterior
  se traga en silencio: el toast dice "Guardado" y el cambio nunca llegó a disco.
  `bulkPut` puede además **nunca settlear** si la transacción aborta sin error,
  dejando la siembra colgada en "Indexando preguntas…".
- **`dom.js:4` y `stats.js:5`** — `toISOString().slice(0,10)` devuelve fecha
  **UTC** pese a que el comentario dice "local". En Chile el día rueda a las
  21:00: estudiar a las 20:00 y a las 21:30 del mismo día **sube la racha +1**.
  Afecta también a `proxima_revision` de SM-2.
- **`imagen.js:3-10`** — imágenes sin límite de tamaño guardadas *dentro* del
  registro de la pregunta. Una foto de 8 MB son ~11 MB de base64 en el store
  `preguntas`, que además queda residente en RAM por el cache de `getAll`.
- **`service-worker.js:89-99`** — network-first sin timeout. Con portal cautivo
  el splash se cuelga un minuto aunque todo esté cacheado.
- **`router.js:56-64`** — `innerHTML` con `e.message` sin escapar. No explotable
  hoy (todos los `throw` usan strings constantes) pero es XSS latente.
- **`service-worker.js:111`** — fallback a `index.html` para cualquier
  subrecurso, incluidos `.js`. Produce errores de MIME type incomprensibles.

---

## 12. Dos preguntas rotas y activas

`R00781` y `GUEV-PED-0017` tienen **una sola opción** y están marcadas
`utilizable: true`. (`R01681` tiene el mismo defecto pero sí está desactivada.)

---

## ✅ Lo que salió limpio

- **Biblioteca**: 0 entradas vacías, 0 ids duplicados, 0 unidades huérfanas,
  0 inconsistencias de `placeholder`. Las 332 entradas están bien.
- **Índice al Perfil 2026**: 0 códigos inexistentes, 0 títulos desalineados en
  las 2.538 preguntas con ítem específico.
- **Reporte de cobertura**: recalculado desde el banco actual, calza exacto en
  los 1.557 ítems.
- **Estructura de preguntas**: 0 con múltiples correctas, 0 con enunciado u
  opciones vacías. Las 17 sin respuesta correcta están correctamente marcadas
  `utilizable: false`.
- **Cola de escrituras de `stats.js`**: la serialización con `_colaProgreso` es
  correcta, sin pérdida de conteos.
- **Matching de rutas del router**: rutas anidadas, segmentos vacíos y el
  `try/catch` de `decodeURIComponent` están bien.
- **Sellado del SW en el APK**: `build-mobile.mjs` estampa un SHA único por
  build; el cache name rota bien también en la ruta nativa.

---

## Sobre el material fuente

Los 22 `.docx` de `material-fuente/` son **apuntes de estudiantes** (Trini
Larraín, Fernanda Ramírez), no material del Dr. Guevara. Son un buen mapa de
temas pero **no son autoridad**.

Caso comprobado: el banco marca *"Retinoides tópicos"* como primera línea del
acné comedoniano; el apunte de Dermatología dice *"queratolíticos → peróxido de
benzoilo"*. La entrada de biblioteca coincide con el banco.

**Criterio para el resto de la verificación de contenido:** donde difieran,
mandan el banco y los PDF del Dr. Guevara.

### Gaps de biblioteca detectados en Dermatología

Temas que la fuente cubre y la biblioteca no: rosácea (el banco tiene 4
preguntas), pitiriasis rosada de Gibert, alopecia androgénica y areata,
vitiligo, pitiriasis alba, pénfigo y penfigoide como entidades propias,
dermatomiositis, lupus cutáneo/discoide, prúrigo insectario, eritema indurado
de Bazin, eritema pérneo, **fitodermatosis por litre** (clásico chileno de
EUNACOM), dishidrosis, queratosis seborreica y lentigo solar.

---

## Corrección a `CLAUDE.md`

El archivo dice "paleta de marca café/crema". Eso es solo la paleta de
biblioteca (`--b-accent: #6b4423`). La paleta general de la app es **teal**
(`--accent: #0d8a8c`). Hay dos sistemas de color conviviendo.

---

## Estado de la reparación

### ✅ Fase 1 — lo que rompía la app (v1.10.2)

1. `runMcq`: el listener de `vista:cambia` se registra después de `mount()`.
2. Arranque offline: `seedIfNeeded` devuelve `{offline:true}` en vez de lanzar,
   `app.js` arranca el router igual, y el SW preserva `data/*.json` al purgar.
3. `fundirConUsuario()` en `seed.js` preserva marcas, estadísticas y ediciones.

### ✅ Fase 2 — integridad del banco (v1.11.0)

Script: `scripts/reparar-banco.py` (corre en simulación por defecto).

```
preguntas               4.017 → 2.477
bug del parser          1.502 → 15
ligaduras fl→fi           306 → 0
enunciados duplicados   1.438 grupos → 0
```

Cero contenido perdido: los enunciados únicos normalizados son los mismos
antes y después (2.473 → 2.473).

Reindexado con `scripts/indexar-perfil.py` y regenerada la cobertura.

### ⏳ Fase 3 — pendiente

1. Accesibilidad: `aria-live` en el feedback del MCQ y contraste de `:disabled`.
2. Router que descarta navegaciones (#8).
3. Recarga forzada en la primera instalación (#9).
4. Fecha UTC en vez de local, que corrompe la racha (#11 de la lista larga).
5. Las 15 preguntas con el corte del parser pendiente de revisión manual.
6. Imágenes sin límite de tamaño dentro del registro de la pregunta.

### Lección sobre el orden

Se aprendió probando, no de antemano: **ligaduras → deduplicar → parser**.
Corregir las ligaduras después de deduplicar deja pasar duplicados; reparar el
parser antes de deduplicar arregla tres veces la misma pregunta.
