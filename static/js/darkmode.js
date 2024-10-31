// darkmode.js
document.addEventListener('DOMContentLoaded', function() {
    const toggleButton = document.getElementById('dark-mode-toggle');
    const containers = document.querySelectorAll('.container, .box, div, section'); // Selecione os contêineres desejados
    const mainElement = document.querySelector('main'); // Selecione o elemento main

    // Verifica o estado do modo escuro no localStorage
    if (localStorage.getItem('dark-mode') === 'enabled') {
        document.body.classList.add('dark-mode');
        containers.forEach(container => container.classList.add('darkmode')); // Adiciona a classe darkmode
        mainElement.classList.add('darkmode'); // Adiciona a classe darkmode ao main
        toggleButton.innerHTML = '<i class="fas fa-sun"></i>'; // Ícone para o modo claro
    }

    toggleButton.addEventListener('click', function() {
        document.body.classList.toggle('dark-mode');

        if (document.body.classList.contains('dark-mode')) {
            localStorage.setItem('dark-mode', 'enabled');
            containers.forEach(container => container.classList.add('darkmode')); // Adiciona a classe darkmode
            mainElement.classList.add('darkmode'); // Adiciona a classe darkmode ao main
            toggleButton.innerHTML = '<i class="fas fa-sun"></i>'; // Ícone para o modo claro
        } else {
            localStorage.setItem('dark-mode', 'disabled');
            containers.forEach(container => container.classList.remove('darkmode')); // Remove a classe darkmode
            mainElement.classList.remove('darkmode'); // Remove a classe darkmode do main
            toggleButton.innerHTML = '<i class="fas fa-moon"></i>'; // Ícone para o modo escuro
        }

        // Animação ao mudar o modo
        document.body.classList.add('transition');
        setTimeout(() => {
            document.body.classList.remove('transition');
        }, 300); // Tempo da animação
    });
});
