const CACHE = "shattered-marches-mobile-v1";
const ASSETS = [
  "/",
  "/mobile.html",
  "/mobile.css",
  "/mobile.js",
  "/manifest.json",
];

self.addEventListener("install", event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(ASSETS)));
});

self.addEventListener("fetch", event => {
  if (event.request.url.includes("/api/")) {
    event.respondWith(fetch(event.request).catch(() => new Response(
      JSON.stringify({error: "The mobile server is unavailable."}),
      {headers: {"Content-Type": "application/json"}, status: 503}
    )));
    return;
  }
  event.respondWith(
    caches.match(event.request).then(cached => cached || fetch(event.request))
  );
});
