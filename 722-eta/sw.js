const C='busbot_shell_v1';
const A=['./','./index.html','./manifest.webmanifest','./icon.svg'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(C).then(c=>c.addAll(A)));self.skipWaiting();});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==C).map(k=>caches.delete(k)))));self.clients.claim();});
self.addEventListener('fetch',e=>{
  var u=new URL(e.request.url);
  if(u.hostname.includes('data.gov.hk')||u.hostname.includes('etabus.gov.hk')||u.pathname.startsWith('/busbot-api'))return;
  if(e.request.mode==='navigate'){e.respondWith(fetch(e.request).catch(()=>caches.match('./index.html')));return;}
  e.respondWith(caches.match(e.request).then(r=>r||fetch(e.request)));
});
