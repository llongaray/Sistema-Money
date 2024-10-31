document.addEventListener('DOMContentLoaded', function() {
    const sortIcons = document.querySelectorAll('.sort-icon');
    
    sortIcons.forEach(icon => {
        icon.addEventListener('click', function() {
            const column = this.dataset.column;
            const tbody = document.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const currentIcon = this.querySelector('i');
            
            // Alterna entre ascendente e descendente
            const isAscending = currentIcon.classList.contains('fa-sort') || 
                              currentIcon.classList.contains('fa-sort-down');
            
            // Atualiza o ícone
            currentIcon.className = isAscending ? 'fas fa-sort-up' : 'fas fa-sort-down';
            
            // Ordena as linhas
            rows.sort((a, b) => {
                let valueA, valueB;
                
                if (column === 'rank') {
                    valueA = parseInt(a.cells[0].textContent);
                    valueB = parseInt(b.cells[0].textContent);
                } else if (column === 'nome') {
                    valueA = a.cells[2].textContent;
                    valueB = b.cells[2].textContent;
                } else if (column === 'faturamento') {
                    valueA = parseFaturamento(a.cells[3].textContent);
                    valueB = parseFaturamento(b.cells[3].textContent);
                }
                
                if (isAscending) {
                    return valueA > valueB ? 1 : -1;
                } else {
                    return valueA < valueB ? 1 : -1;
                }
            });
            
            // Reinsere as linhas ordenadas
            rows.forEach(row => tbody.appendChild(row));
        });
    });
});

// Função auxiliar para converter o valor do faturamento em número
function parseFaturamento(valor) {
    return parseFloat(valor.replace('R$ ', '').replace(' Mi', '').replace(',', '.'));
}

// Adicione esta função
function createAnimatedBackground() {
    const colors = ['#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF'];
    const barContainer = $('.bar-container');
    const containerWidth = barContainer.width();
    const barWidth = 10;
    const numberOfBars = Math.floor(containerWidth / (barWidth * 2));

    for (let i = 0; i < numberOfBars; i++) {
        const bar = $('<div>').addClass('animated-bar');
        const randomColor = colors[Math.floor(Math.random() * colors.length)];
        const randomDelay = Math.random() * 2;
        const randomDuration = 2 + Math.random() * 2;
        
        bar.css({
            'left': `${i * (barWidth * 2)}px`,
            'background-color': randomColor,
            'animation-delay': `${randomDelay}s`,
            'animation-duration': `${randomDuration}s`
        });
        
        barContainer.append(bar);
    }
}

// Adicione isto ao seu DOMContentLoaded existente
document.addEventListener('DOMContentLoaded', function() {
    createAnimatedBackground();
    setupPageReload();
    
    // ... resto do seu código existente ...
});

// Recrie as barras quando a janela for redimensionada
$(window).on('resize', function() {
    $('.bar-container').empty();
    createAnimatedBackground();
});

function createAnimatedLines() {
    const colors = ['#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF'];
    const container = $('.bar-container');
    const containerWidth = $('.animated-bg').width();
    const containerHeight = $('.animated-bg').height();

    // Limpa linhas existentes
    container.empty();

    // Cria novas linhas
    for (let i = 0; i < 20; i++) {
        const line = $('<div>').addClass('animated-line');
        const randomColor = colors[Math.floor(Math.random() * colors.length)];
        const randomWidth = Math.random() * 50 + 30;
        const randomLeft = Math.random() * containerWidth;
        const randomDelay = Math.random() * 5;
        
        line.css({
            'width': `${randomWidth}px`,
            'left': `${randomLeft}px`,
            'bottom': '-100px',
            'background': `linear-gradient(90deg, transparent, ${randomColor})`,
            'color': randomColor
        });

        function animateLine() {
            line.css('bottom', '-100px').animate({
                'bottom': containerHeight + 100
            }, {
                duration: 3000,
                easing: 'linear',
                complete: function() {
                    animateLine();
                }
            });
        }

        container.append(line);
        setTimeout(() => animateLine(), randomDelay * 1000);
    }
}

$(document).ready(function() {
    createAnimatedLines();
    
    $(window).on('resize', function() {
        createAnimatedLines();
    });
});

// Dark Mode Toggle
const toggleSwitch = document.querySelector('.theme-switch input[type="checkbox"]');

function switchTheme(e) {
    if (e.target.checked) {
        document.documentElement.setAttribute('data-theme', 'dark');
        localStorage.setItem('theme', 'dark');
    } else {
        document.documentElement.setAttribute('data-theme', 'light');
        localStorage.setItem('theme', 'light');
    }    
}

toggleSwitch.addEventListener('change', switchTheme);

// Verifica preferência salva
const currentTheme = localStorage.getItem('theme');
if (currentTheme) {
    document.documentElement.setAttribute('data-theme', currentTheme);
    if (currentTheme === 'dark') {
        toggleSwitch.checked = true;
    }
}

// Adicione esta função no final do arquivo
function setupPageReload() {
    // Recarrega a página a cada 10 segundos (10000 milissegundos)
    setInterval(() => {
        console.log('Página recarregada em:', new Date().toLocaleString());
        window.location.reload();
    }, 100000000);
}
