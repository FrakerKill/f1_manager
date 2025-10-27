// Funciones JavaScript globales
document.addEventListener('DOMContentLoaded', function() {
    // Actualizar la hora local para las carreras
    updateLocalTimes();
});

function updateLocalTimes() {
    document.querySelectorAll('[data-race-time]').forEach(element => {
        const utcTime = element.getAttribute('data-race-time');
        const localTime = new Date(utcTime).toLocaleString();
        element.textContent = localTime;
    });
}

// Notificaciones
function showNotification(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.querySelector('.container').prepend(alertDiv);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}