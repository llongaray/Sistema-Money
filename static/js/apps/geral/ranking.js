function animateValue($element, start, end, duration = 1000) {
    // Remove caracteres não numéricos
    start = parseInt(start.toString().replace(/\D/g, ''));
    end = parseInt(end.toString().replace(/\D/g, ''));
    
    // Adiciona classe de atualização
    $element.addClass('updating');
    
    // Configura a animação
    $({value: start}).animate({value: end}, {
        duration: duration,
        easing: 'swing',
        step: function(now) {
            // Formata o número com pontos de milhar
            const formattedValue = Math.floor(now).toLocaleString('pt-BR');
            $element.text(formattedValue + ($element.text().includes('pontos') ? ' pontos' : ''));
        },
        complete: function() {
            // Remove a classe de atualização
            $element.removeClass('updating');
        }
    });
}

// Função para verificar e animar mudanças
function checkForUpdates() {
    $('.animate-value').each(function() {
        const $element = $(this);
        const currentValue = $element.text().replace(/\D/g, '');
        const newValue = $element.attr('data-new-value');
        
        if (newValue && currentValue !== newValue) {
            animateValue($element, currentValue, newValue);
            $element.attr('data-new-value', ''); // Limpa o valor novo
        }
    });
}

// Atualiza quando receber novos dados
function updateValues(data) {
    // Atualiza valores do ranking
    if (data.podium) {
        data.podium.forEach((item, index) => {
            $(`.box__ranking.top${index + 1} .valor`).attr('data-new-value', item.total_pontos);
        });
    }
    
    // Atualiza valores dos destaques
    if (data.destaques) {
        $('.destaque-card:nth-child(1) .animate-value').attr('data-new-value', data.destaques.melhor_equipe.pontos);
        $('.destaque-card:nth-child(2) .animate-value').attr('data-new-value', data.destaques.melhor_jogador.pontos);
    }
    
    // Atualiza valores do header
    if (data.pontos_totais) {
        $('.pontos-totais .valor').attr('data-new-value', data.pontos_totais.valor);
    }
    
    // Inicia as animações
    checkForUpdates();
}

// Verifica atualizações a cada 5 segundos (ou conforme necessário)
setInterval(checkForUpdates, 5000);