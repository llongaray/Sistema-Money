// Funções de Gerenciamento de Estado do Modal
function saveActiveModalState(modalId) {
    if (modalId) {
        sessionStorage.setItem('activeModal', modalId.replace('#', ''));
        console.log(`Estado do modal salvo: ${modalId}`);
    } else {
        sessionStorage.removeItem('activeModal');
        console.log('Estado do modal removido');
    }
}

function restoreActiveModalState() {
    const activeModalId = sessionStorage.getItem('activeModal');
    if (activeModalId) {
        const modal = document.getElementById(activeModalId);
        if (modal) {
            modal.classList.add('active');
            console.log(`Modal restaurado: ${activeModalId}`);
        }
    }
}

// Funções de Manipulação de Modais
function openModal(modalId) {
    const cleanedModalId = modalId.replace('#', '');
    console.log(`Tentando abrir o modal com ID: ${cleanedModalId}`);

    document.querySelectorAll('.modal.active').forEach(modal => {
        if (modal.id !== cleanedModalId) {
            modal.classList.remove('active');
            console.log(`Fechando modal: ${modal.id}`);
        }
    });

    const modal = document.getElementById(cleanedModalId);
    if (modal) {
        modal.classList.add('active');
        saveActiveModalState(cleanedModalId);
        console.log(`Modal com ID: ${cleanedModalId} aberto com sucesso`);
    } else {
        console.error(`Modal com ID: ${cleanedModalId} não encontrado`);
    }
}

function openSubModal(modalId) {
    const cleanedModalId = modalId.replace('#', '');
    console.log(`Tentando abrir o sub-modal com ID: ${cleanedModalId}`);

    document.querySelectorAll('.modal-sec.active').forEach(modalSec => {
        if (modalSec.id !== cleanedModalId) {
            modalSec.classList.remove('active');
            console.log(`Fechando sub-modal: ${modalSec.id}`);
        }
    });

    const subModal = document.getElementById(cleanedModalId);
    if (subModal) {
        subModal.classList.add('active');
        console.log(`Sub-modal com ID: ${cleanedModalId} aberto com sucesso`);
    } else {
        console.error(`Sub-modal com ID: ${cleanedModalId} não encontrado`);
    }
}

function closeAllModals(forceClose = false) {
    if (!forceClose) {
        return;
    }
    
    document.querySelectorAll('.modal.active').forEach(modal => {
        console.log(`Fechando modal com ID: ${modal.id}`);
        modal.classList.remove('active');
    });
    saveActiveModalState(null);
}

function fecharModal(modalId) {
    const cleanedModalId = modalId.replace('#', '');
    const modal = document.getElementById(cleanedModalId);
    
    if (modal) {
        modal.classList.remove('active');
        console.log(`Modal com ID: ${cleanedModalId} fechado com sucesso`);
        saveActiveModalState(null);
    } else {
        console.error(`Modal com ID: ${cleanedModalId} não encontrado`);
    }
}

function closeSubModal(modalId) {
    const cleanedModalId = modalId.replace('#', '');
    const modal = document.getElementById(cleanedModalId);
    
    if (modal && modal.classList.contains('modal-sec')) {
        modal.classList.remove('active');
        console.log(`Sub-modal com ID: ${cleanedModalId} fechado com sucesso`);
    } else {
        console.error(`Sub-modal com ID: ${cleanedModalId} não encontrado ou não é um modal secundário`);
    }
}

function fecharSubModal(modalId) {
    const cleanedModalId = modalId.replace('#', '');
    const subModal = document.getElementById(cleanedModalId);
    
    if (subModal) {
        subModal.classList.remove('active');
        console.log(`Sub-modal com ID: ${cleanedModalId} fechado com sucesso`);
    } else {
        console.error(`Sub-modal com ID: ${cleanedModalId} não encontrado`);
    }
}

// Funções de Utilidade
function mostrarMensagem(texto, tipo) {
    const mensagem = $(`<div class="alert alert-${tipo}">${texto}</div>`);
    $('#mensagens').append(mensagem);
    setTimeout(() => mensagem.fadeOut('slow', function() { $(this).remove(); }), 3000);
}

function handleModalClick(event) {
    if (event.target.classList.contains('modal-sec')) {
        closeSubModal(event.target.id);
        event.stopPropagation();
    }
}

function preencherDadosSubModal(tipoModal, id) {
    console.log(`Preenchendo dados do sub-modal tipo: ${tipoModal}, ID: ${id}`);
    const subModal = document.querySelector('.modal-sec.active');
    
    if (!subModal) {
        console.error('Sub-modal ativo não encontrado');
        return;
    }

    switch(tipoModal) {
        // Casos INSS
        case 'listaClientes':
            if (typeof clientesLoja !== 'undefined') {
                const cliente = clientesLoja.find(cliente => cliente.id === String(id));
                if (cliente) {
                    subModal.querySelector('#idClienteLista').value = id;
                    subModal.querySelector('#nomeClienteLista').value = cliente.nome_cliente;
                    subModal.querySelector('#diaAgendadoLista').value = cliente.dia_agendado;
                    subModal.querySelector('#numeroClienteLista').value = cliente.numero_cliente;
                    subModal.querySelector('#lojaAgendadaLista').value = cliente.loja_nome;
                    console.log('Dados do cliente preenchidos com sucesso');
                }
            }
            break;

        case 'confirmacao':
            if (typeof todosAgendamentos !== 'undefined') {
                const agendamento = todosAgendamentos.find(ag => ag.id === String(id));
                if (agendamento) {
                    subModal.querySelector('#idAgendamentoConfirmacao').value = id;
                    subModal.querySelector('#nomeClienteConfirmacao').value = agendamento.nome_cliente;
                    subModal.querySelector('#diaAgendadoConfirmacao').value = agendamento.dia_agendado;
                    subModal.querySelector('#numeroClienteConfirmacao').value = agendamento.numero_cliente;
                    subModal.querySelector('#lojaAgendadaConfirmacao').value = agendamento.loja_nome;
                    subModal.querySelector('#tabulacaoAtendente').value = agendamento.tabulacao_atendente;
                    console.log('Dados do agendamento preenchidos com sucesso');
                }
            }
            break;

        // Casos SIAPE
        case 'importcsv':
            if (typeof campanhas !== 'undefined') {
                const campanha = campanhas.find(camp => camp.id === String(id));
                if (campanha) {
                    subModal.querySelector('#idCampanhaImport').value = id;
                    subModal.querySelector('#nomeCampanhaImport').value = campanha.nome;
                    subModal.querySelector('#statusCampanhaImport').value = campanha.status;
                    console.log('Dados da campanha preenchidos com sucesso');
                }
            }
            break;

        default:
            console.error(`Tipo de modal não reconhecido: ${tipoModal}`);
    }
}

// Event Listeners Universais
document.addEventListener('DOMContentLoaded', function() {
    // Listeners para botões de fechar
    document.querySelectorAll('.btn-close').forEach(button => {
        button.addEventListener('click', function() {
            const modalId = this.closest('.modal').id;
            fecharModal(modalId);
        });
    });

    // Listeners para fechamento com ESC
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            document.querySelectorAll('.modal.active, .modal-sec.active').forEach(modal => {
                fecharModal(modal.id);
            });
        }
    });

    // Listeners para clique fora do modal
    document.addEventListener('click', function(event) {
        if (event.target.classList.contains('modal-sec')) {
            return;
        }

        if (event.target.classList.contains('modal-sec')) {
            fecharModal(event.target.id);
        }
    });

    // Listeners para modais
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', handleModalClick);
    });
});
