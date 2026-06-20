// Lógica del Sidebar
document.addEventListener("DOMContentLoaded", function() {
    const sidebar = document.getElementById('sidebar');
    const mainWrapper = document.getElementById('main-wrapper');
    const toggleBtn = document.getElementById('sidebar-toggle');
    const overlay = document.getElementById('sidebar-overlay');

    if (toggleBtn) {
        toggleBtn.addEventListener('click', toggleSidebar);
    }
    if (overlay) {
        overlay.addEventListener('click', toggleSidebar);
    }

    function toggleSidebar() {
        if (window.innerWidth <= 768) {
            if (sidebar) sidebar.classList.toggle('show');
            if (overlay) overlay.classList.toggle('show');
        } else {
            if (sidebar) sidebar.classList.toggle('collapsed');
            if (mainWrapper) mainWrapper.classList.toggle('expanded');
            // Guardar preferencia
            if (sidebar) {
                localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
            }
        }
    }

    // Restaurar estado preferido
    if (localStorage.getItem('sidebarCollapsed') === 'true' && window.innerWidth > 768) {
        if (sidebar) sidebar.classList.add('collapsed');
        if (mainWrapper) mainWrapper.classList.add('expanded');
    }
});
