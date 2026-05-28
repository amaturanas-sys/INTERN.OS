// Versión de la app: leída desde data/version.json (estampado por el workflow
// de deploy con SHA corto + fecha). En desarrollo local, los placeholders
// quedan visibles para no confundirse con un build real.
let cache = null;

export async function leerVersion() {
  if (cache) return cache;
  try {
    const res = await fetch("./data/version.json", { cache: "no-cache" });
    const data = await res.json();
    cache = {
      version: data.version === "__APP_VERSION__" ? "dev" : data.version,
      commit: data.commit === "__GIT_SHA__" ? "local" : data.commit,
      fecha_build: data.fecha_build === "__BUILD_DATE__" ? null : data.fecha_build,
    };
  } catch {
    cache = { version: "dev", commit: "local", fecha_build: null };
  }
  return cache;
}

// "v1.0.0 · abc1234" o "dev · local"
export function etiquetaCorta(v) {
  if (!v) return "";
  const sha = v.commit && v.commit !== "local" ? ` · ${v.commit}` : "";
  return `v${v.version}${sha}`;
}
