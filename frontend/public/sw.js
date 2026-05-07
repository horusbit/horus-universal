// HORUS Universal - Service Worker v2.0
// Estrategia: Cache-first para assets, Network-first para API

const CACHE_NAME = "horus-v2";
const STATIC_CACHE = "horus-static-v2";
const API_CACHE = "horus-api-v2";

// Assets estáticos a pre-cachear
const STATIC_ASSETS = [
  "/",
  "/manifest.json",
  "/icon-192.png",
  "/icon-512.png",
];

// ── Install: pre-cachear assets estáticos ────────────────────────────────────
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => {
      return cache.addAll(STATIC_ASSETS).catch((err) => {
        console.warn("[HORUS SW] Pre-cache parcial:", err);
      });
    })
  );
  self.skipWaiting();
});

// ── Activate: limpiar caches viejas ─────────────────────────────────────────
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((k) => k !== STATIC_CACHE && k !== API_CACHE)
          .map((k) => caches.delete(k))
      )
    )
  );
  self.clients.claim();
});

// ── Fetch: estrategia inteligente ────────────────────────────────────────────
self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // No interceptar requests del backend (API calls)
  if (url.pathname.startsWith("/api/v1/")) {
    event.respondWith(networkFirst(request));
    return;
  }

  // Assets estáticos: cache-first
  if (
    request.destination === "image" ||
    url.pathname.endsWith(".json") ||
    url.pathname.endsWith(".ico")
  ) {
    event.respondWith(cacheFirst(request));
    return;
  }

  // Navegación: network-first con fallback offline
  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request).catch(() =>
        caches.match("/").then((r) => r || new Response("HORUS Offline", { status: 503 }))
      )
    );
    return;
  }

  // Default: network-first
  event.respondWith(networkFirst(request));
});

// ── Estrategias de caché ─────────────────────────────────────────────────────

async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(STATIC_CACHE);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    return new Response("", { status: 503 });
  }
}

async function networkFirst(request) {
  try {
    const response = await fetch(request);
    return response;
  } catch {
    const cached = await caches.match(request);
    return cached || new Response(JSON.stringify({ error: "Sin conexión" }), {
      status: 503,
      headers: { "Content-Type": "application/json" },
    });
  }
}

// ── Push Notifications ───────────────────────────────────────────────────────
self.addEventListener("push", (event) => {
  if (!event.data) return;
  const data = event.data.json().catch(() => ({ title: "HORUS", body: event.data.text() }));
  event.waitUntil(
    data.then((d) =>
      self.registration.showNotification(d.title || "HORUS Universal", {
        body: d.body || "Tarea completada",
        icon: "/icon-192.png",
        badge: "/icon-192.png",
        vibrate: [100, 50, 100],
        data: { url: d.url || "/" },
      })
    )
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const url = event.notification.data?.url || "/";
  event.waitUntil(clients.openWindow(url));
});
