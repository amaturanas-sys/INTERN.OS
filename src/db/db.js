// Capa de acceso a IndexedDB. Wrapper de promesas propio (sin dependencias)
// para que la app funcione 100% offline sin librerías externas.

const DB_NAME = "eunacom_db";
const DB_VERSION = 1;

const STORES = {
  preguntas: { keyPath: "id_unico" },
  casos_clinicos: { keyPath: "id" },
  definiciones: { keyPath: "id" },
  repaso: { keyPath: "ref" },          // SM-2 por ítem: ref = "tipo:id"
  progreso_usuario: { keyPath: "id" }, // doc "global" + sesiones
  config: { keyPath: "key" },
};

let _dbPromise = null;

function openDB() {
  if (_dbPromise) return _dbPromise;
  if (typeof indexedDB === "undefined") {
    return Promise.reject(new Error(
      "IndexedDB no disponible. Revisa que el navegador no esté en modo privado."));
  }
  _dbPromise = new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = (e) => {
      const db = req.result;
      const oldVersion = e.oldVersion;
      runMigrations(db, oldVersion);
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
    req.onblocked = () => reject(new Error("IndexedDB bloqueada por otra pestaña"));
  });
  return _dbPromise;
}

function runMigrations(db, oldVersion) {
  // Migración v0 -> v1: crear stores e índices.
  if (oldVersion < 1) {
    const preguntas = db.createObjectStore("preguntas", { keyPath: "id_unico" });
    preguntas.createIndex("especialidad", "especialidad_principal", { unique: false });
    preguntas.createIndex("tema", "tema_validado", { unique: false });
    preguntas.createIndex("sistema_behrens", "sistema_behrens", { unique: false });
    preguntas.createIndex("dificultad", "dificultad_estimada", { unique: false });
    preguntas.createIndex("frecuencia", "frecuencia_eunacom", { unique: false });
    preguntas.createIndex("utilizable", "utilizable", { unique: false });

    const casos = db.createObjectStore("casos_clinicos", { keyPath: "id" });
    casos.createIndex("especialidad", "especialidad", { unique: false });
    casos.createIndex("tema", "tema", { unique: false });

    const defs = db.createObjectStore("definiciones", { keyPath: "id" });
    defs.createIndex("tipo", "tipo", { unique: false });
    defs.createIndex("especialidad", "especialidad", { unique: false });

    const repaso = db.createObjectStore("repaso", { keyPath: "ref" });
    repaso.createIndex("proxima_revision", "proxima_revision", { unique: false });
    repaso.createIndex("tipo", "tipo", { unique: false });

    db.createObjectStore("progreso_usuario", { keyPath: "id" });
    db.createObjectStore("config", { keyPath: "key" });
  }
  // Futuras migraciones: if (oldVersion < 2) { ... }
}

function tx(db, store, mode) {
  return db.transaction(store, mode).objectStore(store);
}

function reqToPromise(req) {
  return new Promise((resolve, reject) => {
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

export async function put(store, value) {
  const db = await openDB();
  return reqToPromise(tx(db, store, "readwrite").put(value));
}

export async function bulkPut(store, values) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const t = db.transaction(store, "readwrite");
    const os = t.objectStore(store);
    for (const v of values) os.put(v);
    t.oncomplete = () => resolve(values.length);
    t.onerror = () => reject(t.error);
  });
}

export async function get(store, key) {
  const db = await openDB();
  return reqToPromise(tx(db, store, "readonly").get(key));
}

export async function getAll(store) {
  const db = await openDB();
  return reqToPromise(tx(db, store, "readonly").getAll());
}

export async function del(store, key) {
  const db = await openDB();
  return reqToPromise(tx(db, store, "readwrite").delete(key));
}

export async function count(store) {
  const db = await openDB();
  return reqToPromise(tx(db, store, "readonly").count());
}

export async function clearStore(store) {
  const db = await openDB();
  return reqToPromise(tx(db, store, "readwrite").clear());
}

// Config helpers
export async function getConfig(key, fallback = null) {
  const row = await get("config", key);
  return row ? row.value : fallback;
}
export async function setConfig(key, value) {
  return put("config", { key, value });
}
