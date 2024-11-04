$(document).ready(function() {
    // Função para salvar dados do top1 no localStorage
    function saveTop1Data(nome, valor) {
        const top1Data = {
            nome: nome,
            valor: valor
        };
        localStorage.setItem('siapeTop1', JSON.stringify(top1Data));
    }

    // Função para obter dados do top1 do localStorage
    function getTop1Data() {
        const data = localStorage.getItem('siapeTop1');
        return data ? JSON.parse(data) : null;
    }

    // Função para mostrar animação de novo top1
    function showTop1Celebration() {
        // Remove celebração anterior se existir
        $('#top1Celebration').remove();
        
        const celebrationHtml = `
            <div id="top1Celebration">
                <div class="celebration-content">
                    <img src="/static/img/novo_top1.gif" class="celebration-gif" alt="Novo Top 1!">
                    <audio id="celebrationAudio" autoplay>
                        <source src="/static/files/audio_celebration.mp3" type="audio/mpeg">
                    </audio>
                </div>
            </div>
        `;

        $('body').append(celebrationHtml);
        
        // Mostra a celebração com fade e inicia o áudio
        $('#top1Celebration').fadeIn('fast', function() {
            const audio = document.getElementById('celebrationAudio');
            audio.volume = 1.0; // Volume máximo (100%)
            audio.play().catch(function(error) {
                console.log("Erro ao tocar áudio:", error);
            });

            confetti({
                particleCount: 100,
                spread: 160,
                origin: { y: 0.6 },
                disableForReducedMotion: true
            });
        });

        // Remove a celebração após 6 segundos
        setTimeout(() => {
            const audio = document.getElementById('celebrationAudio');
            if (audio) {
                audio.pause();
                audio.currentTime = 0;
            }
            $('#top1Celebration').fadeOut('slow', function() {
                $(this).remove();
            });
        }, 6000);
    }

    // Verificar se houve mudança no top1
    function checkTop1Change() {
        const storedTop1 = getTop1Data();
        const currentTop1 = podiumData.top1;

        if (!storedTop1) {
            // Primeiro acesso, apenas salva os dados
            saveTop1Data(currentTop1.nome, currentTop1.valor);
        } else if (storedTop1.nome !== currentTop1.nome) {
            // Novo top1 detectado - sempre mostra a celebração se não for "Posição Disponível"
            if (currentTop1.nome !== 'Posição Disponível') {
                showTop1Celebration();
            }
            // Atualiza o storage com o novo top1
            saveTop1Data(currentTop1.nome, currentTop1.valor);
        }
    }

    // Executar verificação inicial
    checkTop1Change();
});
