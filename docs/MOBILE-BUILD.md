# Build nativo Android (Capacitor)

Esta es la pipeline que produce el `.apk` descargable de InternOS publicado
en GitHub Releases. La APK contiene **todos los JS/CSS/JSON/imágenes
embebidos**, así que no necesita el dominio público de GitHub Pages para
funcionar — instálala una vez y la app trabaja sin internet jamás.

## Arquitectura

```
PWA en raíz (sigue vivo)        →  GitHub Pages (workflow deploy-pages)
       │
       │  scripts/build-mobile.mjs copia los assets a dist/
       ▼
   dist/    →  npx cap sync android  →  android/app/src/main/assets/public/
                                                            │
                                                            ▼
                                                 ./gradlew assembleDebug
                                                            │
                                                            ▼
                                          internos-native-v<VERSION>-<build>.apk
```

- **No mantenemos `android/` en el repo**: la regenera el CI con
  `npx cap add android` cada vez. Customizaciones puntuales (versionName,
  versionCode) se aplican con `sed` antes de compilar.
- **Mismos archivos web** que el PWA: el código compartido vive en `src/`,
  `styles/`, `data/`, `assets/`. Solo cambia el *envoltorio*.
- **Service Worker** queda dentro de la APK, pero como Capacitor ya sirve
  los assets desde `https://localhost/...`, el SW funciona como cache
  redundante (no estorba).

## Build local (opcional)

Requisitos: Node 20+, JDK 17, Android SDK con build-tools 34+ y un
`ANDROID_HOME` apuntando a la SDK.

```bash
# 1. Instalar deps
npm install

# 2. Empaquetar el PWA a dist/
npm run build:web

# 3. Generar el wrapper Android (solo la primera vez)
npx cap add android

# 4. Sincronizar dist/ → android/
npx cap sync android

# 5. Compilar APK debug
cd android && ./gradlew assembleDebug
# APK queda en: android/app/build/outputs/apk/debug/app-debug.apk
```

Para iterar tras cambios al código web: repetir pasos 2 + 4 + 5.

## Build CI (GitHub Actions)

Workflow: [`build-android-app.yml`](../.github/workflows/build-android-app.yml)

- Se dispara en cada push a `main` que toque la PWA o la configuración.
- También se puede correr a mano (`workflow_dispatch`).
- Cada build produce:
  - **Artefacto** descargable desde la pestaña *Actions* (90 días).
  - **GitHub Release** con tag `v<VERSION>-native` (re-creado en cada
    build para que siempre apunte al binario más reciente).

### Identificadores

- **Package ID**: `cl.internos.offline` (distinto al TWA `cl.internos.app`
  para que ambos puedan convivir en el mismo dispositivo). Se evita la
  raíz `native` porque es palabra reservada de Java.
- **Nombre visible**: `InternOS`.
- **versionName**: viene del archivo `VERSION` del repo.
- **versionCode**: el `github.run_number` del workflow (monótono creciente
  por construcción).

## Limitaciones conocidas

- **Firma debug**: la APK la firma Gradle con el keystore debug por
  defecto. Es perfecto para uso personal e instalación lateral, pero no
  apta para Play Store. Para release-grade habría que añadir un keystore
  propio (igual que ya hace `build-apk.yml` para la versión TWA).
- **Splash screen**: queda el splash blanco por defecto de Capacitor.
  Para un splash personalizado bastaría con activar
  `@capacitor/splash-screen` y dejar una imagen en `resources/splash.png`.
- **Tamaño**: la APK ronda los **10-12 MB** (banco de preguntas + assets +
  WebView wrapper). El banco completo se sembra en IndexedDB en la
  primera apertura, igual que en el PWA.

## Actualizar la app después de instalada

Al ser una APK lateral (no Play Store), el dispositivo no recibe updates
automáticos. Cuando salga una versión nueva:

1. El usuario abre la página de releases.
2. Descarga la APK nueva.
3. La instala encima de la anterior (Android la actualiza preservando
   los datos de IndexedDB porque el `appId` es el mismo).

Los datos del usuario (ediciones de biblioteca, subtemas custom,
progreso, repaso SM-2) **persisten** entre updates mientras no se
desinstale la app.
