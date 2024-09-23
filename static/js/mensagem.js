document.addEventListener('DOMContentLoaded', function() {
    const messageDiv = document.getElementById('messageDiv');
    const message = messageDiv.textContent.trim();

    // Se a mensagem for vazia ou 'none', esconder o div
    if (!message || message === 'none') {
        messageDiv.style.display = 'none';
    } else {
        // Caso contrário, exibe o div
        messageDiv.style.display = 'flex';
    }
});