const OFFLINE_URL = "./offline.html";
const VERSION = "eesi-sw-v2";   // ← bumped

self.addEventListener("install", (event) => {
  event.waitUntil(
    Promise.all([
      caches.open(VERSION).then((cache) => cache.addAll([OFFLINE_URL])).catch((err) => {
        console.warn("[sw] offline.html cache failed:", err);
      }),
      self.skipWaiting()        // ← now awaited
    ])
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== VERSION).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.mode !== "navigate") return;
  event.respondWith(
    fetch(req, { cache: "no-store" })    // ← always try fresh HTML
      .catch(() => caches.match(OFFLINE_URL))
  );
});

// Handle notification clicks
self.addEventListener("notificationclick", function (event) {
  event.notification.close();

  event.waitUntil(
    clients.matchAll({ type: "window", includeUncontrolled: true }).then(function (clientList) {
      const targetOrigin = new URL("./", self.location.href).origin;   // ← match by origin
      for (let i = 0; i < clientList.length; i++) {
        const client = clientList[i];
        try {
          if (new URL(client.url).origin === targetOrigin && "focus" in client) {
            return client.focus();
          }
        } catch (_) { /* ignore invalid URLs */ }
      }
      if (clients.openWindow) {
        return clients.openWindow("./");
      }
    })
  );
});