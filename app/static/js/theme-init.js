// Loaded synchronously in <head> so the saved theme applies before first
// paint, avoiding a light flash for dark-mode users.
(function () {
    try {
        if (localStorage.getItem('darkMode') === 'true') {
            document.documentElement.setAttribute('data-bs-theme', 'dark');
        }
    } catch (e) {
        // Storage can be blocked (privacy modes); fall back to light.
    }
})();
