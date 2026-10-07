if ('serviceWorker' in navigator) navigator.serviceWorker.getRegistrations().then(items => items.forEach(item => item.unregister()));
if ('caches' in window) caches.keys().then(keys => keys.filter(key => key.startsWith('alivio-lombar-')).forEach(key => caches.delete(key)));
