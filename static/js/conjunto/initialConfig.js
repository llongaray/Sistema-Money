// initialConfig.js
$(document).ready(function () {
    const container = $('.container'); // Seleciona o container que será ajustado
    const modals = $('.modal'); // Seleciona todos os modais

    // Função para ajustar a altura do container com base na altura do maior modal
    function adjustContainerHeight() {
        let maxModalHeight = 0;

        // Percorre todos os modais para encontrar a altura máxima
        modals.each(function () {
            const modalHeight = $(this).outerHeight(true); // Pega a altura do modal com margem
            if (modalHeight > maxModalHeight) {
                maxModalHeight = modalHeight;
            }
        });

        // Define a altura do container como a altura máxima encontrada
        container.css('height', maxModalHeight + 'px');

        // Adiciona um console log para verificar a altura máxima
        console.log('Altura máxima do modal:', maxModalHeight);
    }

    // Ajusta a altura do container ao carregar a página
    adjustContainerHeight();

    // Adiciona um listener para redimensionamento da janela
    $(window).on('resize', adjustContainerHeight);

    // Também ajusta a altura do container quando qualquer modal é aberto
    modals.on('shown.bs.modal', adjustContainerHeight);
});
