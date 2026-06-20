document.addEventListener("DOMContentLoaded", function() {
    // Lógica de Sesión (sessionStorage)
    const sessionData = document.getElementById('session-data');
    if (sessionData) {
        const isAuth = sessionData.dataset.authenticated === 'true';
        const logoutUrl = sessionData.dataset.logoutUrl;
        const csrfToken = sessionData.dataset.csrfToken;

        if (isAuth) {
            if (!sessionStorage.getItem('session_active')) {
                const form = document.createElement('form');
                form.method = 'POST';
                form.action = logoutUrl;
                const csrfInput = document.createElement('input');
                csrfInput.type = 'hidden';
                csrfInput.name = 'csrfmiddlewaretoken';
                csrfInput.value = csrfToken;
                form.appendChild(csrfInput);
                document.body.appendChild(form);
                form.submit();
            } else {
                sessionStorage.setItem('session_active', 'true');
            }
        }
    }

    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', function() {
            sessionStorage.setItem('session_active', 'true');
        });
    }
});
