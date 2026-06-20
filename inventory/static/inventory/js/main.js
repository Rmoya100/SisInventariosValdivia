// Custom JavaScript for Inventory App
document.addEventListener("DOMContentLoaded", function() {
    console.log("Sistema de Inventario Cargado Correctamente.");
    
    // Add simple animation classes to cards on load
    const cards = document.querySelectorAll('.feature-card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        setTimeout(() => {
            card.style.transition = 'opacity 0.5s ease-in-out, transform 0.3s ease';
            card.style.opacity = '1';
        }, 100 * index);
    });
});
