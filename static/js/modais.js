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
        closeAllModals();
        const modal = document.getElementById(activeModalId);
        if (modal) {
            modal.classList.add('active');
            console.log(`Modal restaurado: ${activeModalId}`);
        }
    }
}

// Funções de Controle de Modal
function openModal(modalId) {
    const cleanedModalId = modalId.replace('#', '');
    console.log(`Tentando abrir o modal com ID: ${cleanedModalId}`);

    const modal = document.getElementById(cleanedModalId);
    if (modal) {
        modal.classList.add('active');
        saveActiveModalState(cleanedModalId);
        
        if (cleanedModalId === 'modalListaClientes') {
            console.log('Chamando preencherTabelaClientes');
            preencherTabelaClientes();
        }
        else if (cleanedModalId === 'modalTodosAgendamentos') {
            console.log('Chamando preencherTabelaTodosAgendamentos');
            preencherTabelaTodosAgendamentos();
        }
        
        console.log(`Modal com ID: ${cleanedModalId} aberto com sucesso`);
    } else {
        console.error(`Modal com ID: ${cleanedModalId} não encontrado`);
    }
}

function closeAllModals() {
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
        saveActiveModalState(null);
        console.log(`Modal com ID: ${cleanedModalId} fechado com sucesso`);
    } else {
        console.error(`Modal com ID: ${cleanedModalId} não encontrado`);
    }
}

function abrirModalOptions(modalId) {
    console.log('Tetando abri');
    closeAllModals();
    openModal(modalId);
}

// Funções de Sub-Modal
function abrirSubModal(modalId, tipoModal, id) {
    console.log(`Abrindo sub-modal com ID: ${modalId}, tipo: ${tipoModal}, ID do agendamento: ${id}`);

    openModal(modalId);
    const subModal = document.getElementById(modalId.replace('#', ''));
    
    if (tipoModal === 'importcsv') {
        preencherDadosImportCSV(subModal, id);
    } else if (subModal) {
        preencherDadosSubModal(subModal, tipoModal, id);
    } else {
        console.error(`Sub-modal com ID: ${modalId} não encontrado`);
    }
}

function preencherDadosImportCSV(subModal, idCampanha) {
    console.log("Preenchendo dados para importação de CSV. ID da Campanha:", idCampanha);

    const campanha = campanhasEdicao[idCampanha];

    if (campanha) {
        subModal.querySelector('#nome_campanha').value = campanha.nome;  
        subModal.querySelector('#campanha_id').value = idCampanha;  
    } else {
        console.warn(`Dados para a campanha com ID ${idCampanha} não encontrados.`);
    }
}

function preencherDadosSubModal(subModal, tipoModal, id) {
    console.log("Iniciando preenchimento do sub-modal para ID:", id);

    if (tipoModal === 'listaClientes') {
        if (!id || id === 'undefined' || !clientesLojaData.find(c => c.id === id)) {
            console.error(`ID inválido ou cliente com ID ${id} não encontrado em clientesLojaData`);
            return;
        }

        const dados = clientesLojaData.find(c => c.id === id);
        console.log("Dados do cliente:", dados);

        try {
            // Preencher o ID do agendamento
            const agendamentoId = subModal.querySelector('#agendamentoId');
            if (agendamentoId) {
                agendamentoId.value = dados.id;
                console.log(`Agendamento ID preenchido com: ${dados.id}`);
            }

            // Mapear campos para preencher
            const campos = {
                '#nomeCliente': dados.nome,
                '#cpfCliente': dados.cpf,
                '#numeroCliente': dados.numero,
                '#diaAgendado': dados.diaAgendadoFormatado,
                '#tabulacaoAtendente': dados.tabulacaoAtendente,
                '#atendenteAgendou': dados.atendenteNome,
                '#lojaAgendada': dados.lojaNome
            };

            // Preencher cada campo
            Object.entries(campos).forEach(([selector, valor]) => {
                const elemento = subModal.querySelector(selector);
                if (elemento) {
                    elemento.value = valor || '';
                    console.log(`Campo ${selector} preenchido com: ${valor}`);
                } else {
                    console.warn(`Elemento ${selector} não encontrado no modal`);
                }
            });

            // Preencher select de vendedores
            const vendedorSelect = subModal.querySelector('#vendedorLoja');
            if (vendedorSelect) {
                // Limpar opções existentes
                vendedorSelect.innerHTML = '<option value="">Selecione um vendedor</option>';
                // Preencher com novos vendedores
                preencherSelectVendedores(vendedorSelect);
                
                if (dados.vendedorLoja) {
                    vendedorSelect.value = dados.vendedorLoja;
                    console.log(`Vendedor selecionado: ${dados.vendedorLoja}`);
                }
            } else {
                console.warn('Select de vendedores não encontrado');
            }

            // Configurar campos de tabulação do vendedor
            const tabulacaoVendedor = subModal.querySelector('#tabulacaoVendedor');
            const observacaoVendedor = subModal.querySelector('#observacaoVendedor');
            const observacaoContainer = subModal.querySelector('#observacaoVendedorContainer');
            const fechouNegocioContainer = subModal.querySelector('#fechouNegocioContainer');

            if (tabulacaoVendedor && dados.tabulacaoVendedor) {
                tabulacaoVendedor.value = dados.tabulacaoVendedor;
                console.log(`Tabulação do vendedor: ${dados.tabulacaoVendedor}`);

                // Mostrar campos adicionais se necessário
                if (dados.tabulacaoVendedor === 'FECHOU NEGOCIO') {
                    fechouNegocioContainer.style.display = 'block';
                    observacaoContainer.style.display = 'block';
                } else if (dados.tabulacaoVendedor) {
                    observacaoContainer.style.display = 'block';
                }

                if (observacaoVendedor && dados.observacaoVendedor) {
                    observacaoVendedor.value = dados.observacaoVendedor;
                }
            }

        } catch (error) {
            console.error('Erro ao preencher dados do sub-modal:', error);
        }
    } else if (tipoModal === 'confirmacao') {
        if (!id || id === 'undefined' || !agendamentosEdicao[id]) {
            console.error(`ID inválido ou agendamento com ID ${id} não encontrado`);
            return;
        }

        const dados = agendamentosEdicao[id];
        if (dados) {
            console.log('Dados do agendamento:', dados);
            
            subModal.querySelector('#idAgendamentoConfirmacao').value = id;
            subModal.querySelector('#nomeClienteConfirmacao').value = dados.nome;
            subModal.querySelector('#diaAgendadoConfirmacao').value = dados.diaAgendadoForm;
            subModal.querySelector('#numeroClienteConfirmacao').value = dados.numero;
            subModal.querySelector('#lojaAgendadaConfirmacao').value = dados.lojaNome;
            subModal.querySelector('#tabulacaoAtendente').value = dados.tabulacaoAtendente;
            
            console.log('ID do agendamento definido:', id);
        } else {
            console.warn(`Dados para o ID ${id} não encontrados no dicionário.`);
        }
    }
}

// Funções de Manipulação de Tabelas
function preencherTabelaClientes() {
    console.log('Iniciando preenchimento da tabela de clientes');
    
    const $tabela = $('#modalListaClientes #tabelaClientesLoja tbody');
    
    if (!$tabela.length) {
        console.error('Tabela não encontrada!');
        return;
    }
    
    $tabela.empty();
    console.log('Tabela limpa');

    clientesLojaData.forEach(cliente => {
        const nomeElement = `<button type="button" class="btn-link abrir-sub-modal" 
            onclick="abrirSubModal('#modalEdicaoCliente', 'listaClientes', '${cliente.id}')">
            ${cliente.nome}
        </button>`;

        const row = `
            <tr>
                <td>${nomeElement}</td>
                <td>${cliente.cpf}</td>
                <td>${cliente.numero}</td>
                <td>${cliente.diaAgendadoFormatado}</td>
                <td>${cliente.atendenteNome}</td>
                <td>${cliente.lojaNome}</td>
                <td>${cliente.statusDias}</td>
            </tr>
        `;
        
        $tabela.append(row);
    });
    
    console.log('Preenchimento da tabela concluído');
}
// Variável global para controlar a direção da ordenação
let sortDirection = 'desc'; // Começa com mais recente

// Função para converter o formato dos dados
function converterParaFormatoClienteLoja(agendamento) {
    return {
        id: agendamento.id,
        nome: agendamento.nome_cliente,
        cpf: agendamento.cpf_cliente,
        numero: agendamento.numero_cliente,
        diaAgendado: agendamento.dia_agendado,
        diaAgendadoFormatado: agendamento.diaAgendadoFormatado,
        tabulacaoAtendente: agendamento.tabulacao_atendente,
        atendenteAgendou: agendamento.atendente_nome,
        lojaAgendada: agendamento.loja_nome
    };
}

function preencherTabelaTodosAgendamentos() {
    console.log('Iniciando preenchimento da tabela de todos os agendamentos');
    
    const $tabela = $('#modalTodosAgendamentos #tabelaTodosAgendamentos tbody');
    
    if (!$tabela.length) {
        console.error('Tabela de todos os agendamentos não encontrada!');
        return;
    }
    
    $tabela.empty();
    console.log('Tabela limpa');

    // Agrupar por CPF
    const agendamentosPorCPF = {};
    todosAgendamentos.forEach(agendamento => {
        if (!agendamentosPorCPF[agendamento.cpf_cliente]) {
            agendamentosPorCPF[agendamento.cpf_cliente] = [];
        }
        agendamentosPorCPF[agendamento.cpf_cliente].push(agendamento);
    });

    Object.values(agendamentosPorCPF).forEach(agendamentos => {
        // Ordenar agendamentos do mesmo CPF por data (mais recente primeiro)
        agendamentos.sort((a, b) => new Date(b.dia_agendado) - new Date(a.dia_agendado));
        
        // Pegar apenas o agendamento mais recente
        const agendamentoRecente = agendamentos[0];
        const totalAgendamentos = agendamentos.length;

        const nomeElement = `<button type="button" class="btn-link abrir-sub-modal" 
            onclick="abrirSubModal('#modalEdicaoCliente', 'listaClientes', '${agendamentoRecente.id}')">
            ${agendamentoRecente.nome_cliente}
        </button>`;

        const dataCompleta = new Date(agendamentoRecente.dia_agendado);
        const dataFormatada = dataCompleta.toISOString().split('T')[0];

        const row = `
            <tr>
                <td>${nomeElement}</td>
                <td>${agendamentoRecente.cpf_cliente}</td>
                <td>${agendamentoRecente.numero_cliente}</td>
                <td data-date="${agendamentoRecente.dia_agendado}">${dataFormatada}</td>
                <td>${agendamentoRecente.atendente_nome}</td>
                <td>${agendamentoRecente.loja_nome}</td>
                <td>${agendamentoRecente.status_dias}</td>
                <td>${totalAgendamentos}</td>
            </tr>
        `;
        
        $tabela.append(row);
    });

    console.log('Preenchimento da tabela de todos os agendamentos concluído');
}

// Funções de Manipulação de Formulários
function handleTabulacaoChange() {
    const modal = document.getElementById('modalConfirmacaoAgendamento');
    const tabulacaoSelect = modal.querySelector('#tabulacaoAtendente');
    const selectedValue = tabulacaoSelect.value;
    
    console.log('Select dropdown:', tabulacaoSelect); 
    console.log('Valor selecionado no dropdown:', selectedValue);
    
    const novaDataContainer = modal.querySelector('#novaDataContainer');
    const observacaoContainer = modal.querySelector('#observacaoContainer');
    
    novaDataContainer.style.display = 'none';
    observacaoContainer.style.display = 'none';
    
    if (selectedValue === 'REAGENDADO') {
        console.log('Campo REAGENDADO selecionado, mostrando campo de nova data.');
        novaDataContainer.style.display = 'block';
    } else if (selectedValue === 'DESISTIU') {
        console.log('Campo DESISTIU selecionado, mostrando campo de observao.');
        observacaoContainer.style.display = 'block';
    } else {
        console.log('Nenhum campo específico foi selecionado.');
    }
}

function handleTabulacaoVendedorChange() {
    const modal = document.getElementById('modalEdicaoCliente');
    const tabulacaoSelect = modal.querySelector('#tabulacaoVendedor');
    const selectedValue = tabulacaoSelect.value;
    
    const observacaoContainer = modal.querySelector('#observacaoVendedorContainer');
    const fechouNegocioContainer = modal.querySelector('#fechouNegocioContainer');
    
    observacaoContainer.style.display = 'none';
    fechouNegocioContainer.style.display = 'none';
    
    if (selectedValue === 'FECHOU NEGOCIO') {
        observacaoContainer.style.display = 'block';
        fechouNegocioContainer.style.display = 'block';
    } else if (selectedValue && selectedValue !== '') {
        observacaoContainer.style.display = 'block';
    }
}

function preencherSelectVendedores(selectElement) {
    Object.values(vendedoresListaClientes).forEach(vendedor => {
        const option = document.createElement('option');
        option.value = vendedor.id;
        option.textContent = vendedor.nome;
        selectElement.appendChild(option);
    });
}

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    const mensagensContainer = document.getElementById('mensagens');
    const temMensagemSucesso = mensagensContainer && 
                              mensagensContainer.querySelector('.success');
    
    if (temMensagemSucesso) {
        saveActiveModalState(null);
        console.log('Estado do modal removido - mensagem de sucesso');
    } else {
        restoreActiveModalState();
    }

    document.querySelectorAll('.btn-close').forEach(button => {
        button.addEventListener('click', function() {
            const modalId = this.closest('.modal').id;
            fecharModal(modalId);
        });
    });

    const modalEdicaoCliente = document.getElementById('modalEdicaoCliente');
    if (modalEdicaoCliente) {
        const tabulacaoVendedor = modalEdicaoCliente.querySelector('#tabulacaoVendedor');
        if (tabulacaoVendedor) {
            tabulacaoVendedor.addEventListener('change', handleTabulacaoVendedorChange);
            console.log('Listener adicionado ao select de tabulação do vendedor');
        } else {
            console.error('Select de tabulação do vendedor não encontrado');
        }
    } else {
        console.error('Modal de edição cliente não encontrado');
    }

    // Adicionar listeners para os formulários em sub-modais
    document.querySelectorAll('.modal-sec form').forEach(form => {
        form.addEventListener('submit', handleSubModalFormSubmit);
    });

    // Atualizar os listeners de botões close em sub-modais
    document.querySelectorAll('.modal-sec .btn-close').forEach(button => {
        button.addEventListener('click', function() {
            const modalId = this.closest('.modal-sec').id;
            closeSubModal(modalId);
        });
    });

    // Adiciona o evento de clique em todos os modal-sec
    document.querySelectorAll('.modal-sec').forEach(modalSec => {
        modalSec.addEventListener('click', function(event) {
            // Se o clique foi diretamente no .modal-sec (backdrop)
            if (event.target === this) {
                closeSubModal(this.id);
            }
        });
    });
});

document.querySelectorAll('.modal').forEach(modal => {
    modal.addEventListener('click', handleModalClick);
});

document.getElementById('modalConfirmacaoAgendamento')
    .querySelector('#tabulacaoAtendente')
    .addEventListener('change', handleTabulacaoChange);

window.addEventListener('beforeunload', function(event) {
    const navigationType = performance.getEntriesByType("navigation")[0]?.type;
    
    if (navigationType !== "reload") {
        sessionStorage.removeItem('activeModal');
        console.log('Estado do modal removido - navegação para outra página');
    }
});

$(document).ready(function() {
    $('[data-target="#modalListaClientes"]').on('click', function() {
        console.log('Botão de lista de clientes clicado');
        openModal('modalListaClientes');
        return false;
    });

    // Listener para o filtro de CPF
    $("#filtroCPF").on("keyup", function() {
        const value = $(this).val().toLowerCase();
        $("#tabelaTodosAgendamentos tbody tr").filter(function() {
            $(this).toggle($(this).children("td:eq(1)").text().toLowerCase().indexOf(value) > -1);
        });
    });

    // Listener para ordenação por data
    $('.sortable[data-sort="data"]').on('click', function() {
        sortDirection = sortDirection === 'desc' ? 'asc' : 'desc';
        const icon = $(this).find('i');
        icon.removeClass('fa-sort-down fa-sort-up')
            .addClass(sortDirection === 'desc' ? 'fa-sort-down' : 'fa-sort-up');
        preencherTabelaTodosAgendamentos();
    });

    // Estilo para cursor pointer na coluna ordenável
    $('.sortable').css('cursor', 'pointer');

    // Formatação para caixa alta
    $('.text-uppercase').on('input', function() {
        this.value = this.value.toUpperCase();
    });
});

// Funções de Controle de Modal
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

// Atualizar a função handleModalClick para lidar apenas com modal-sec
function handleModalClick(event) {
    // Verifica se o clique foi diretamente no backdrop do modal-sec
    if (event.target.classList.contains('modal-sec')) {
        closeSubModal(event.target.id);
        event.stopPropagation(); // Impede a propagação do evento para o modal pai
    }
}

// Adicionar função para lidar com o submit dos formulários em sub-modais
function handleSubModalFormSubmit(event) {
    event.preventDefault();
    const form = event.target;
    const subModal = form.closest('.modal-sec');
    const formType = form.querySelector('input[name="form_type"]').value;
    const parentModal = subModal.closest('.modal');  // Pega o modal pai
    
    // Enviar o formulário via AJAX
    $.ajax({
        url: form.action,
        method: form.method,
        data: new FormData(form),
        processData: false,
        contentType: false,
        success: function(response) {
            console.log('Formulário enviado com sucesso');
            
            // Fechar apenas o sub-modal após o sucesso
            if (subModal) {
                subModal.classList.remove('active');
                console.log(`Sub-modal ${subModal.id} fechado`);
            }

            // Se for formulário de lista_clientes, apenas atualizar a tabela
            if (formType === 'lista_clientes') {
                // Atualizar apenas a tabela relevante
                if (document.getElementById('modalTodosAgendamentos').classList.contains('active')) {
                    preencherTabelaTodosAgendamentos();
                } else if (document.getElementById('modalListaClientes').classList.contains('active')) {
                    preencherTabelaClientes();
                }
            } else if (formType === 'confirmacao_agendamento') {
                // Para confirmação de agendamento, manter o modal pai aberto
                if (parentModal) {
                    setTimeout(() => {
                        location.reload();
                    }, 500);
                }
            } else {
                // Para outros tipos de formulário, recarregar a página
                location.reload();
            }
        },
        error: function(xhr, status, error) {
            console.error('Erro ao enviar formulário:', error);
        }
    });
}

// Função para atualizar status TAC
function atualizarStatusTAC(selectElement, agendamentoId) {
    const novoStatus = selectElement.value;
    if (!novoStatus) return;

    const row = $(selectElement).closest('tr');
    const statusCell = row.find('.status-tac');

    $.ajax({
        url: '/inss/atualizar_status_tac/',
        method: 'POST',
        data: {
            agendamento_id: agendamentoId,
            status: novoStatus,
            csrfmiddlewaretoken: $('[name=csrfmiddlewaretoken]').val()
        },
        success: function(response) {
            if (response.success) {
                // Atualiza o status na tabela
                statusCell.text(novoStatus);
                
                // Feedback visual
                mostrarMensagem('Status atualizado com sucesso!', 'success');
                
                // Se foi marcado como PAGO, atualiza a interface
                if (novoStatus === 'PAGO') {
                    row.addClass('tac-pago');
                } else {
                    row.removeClass('tac-pago');
                }
            } else {
                mostrarMensagem('Erro ao atualizar status: ' + response.error, 'error');
                // Reverte a seleção em caso de erro
                $(selectElement).val(statusCell.text());
            }
        },
        error: function() {
            mostrarMensagem('Erro ao comunicar com o servidor', 'error');
            // Reverte a seleção em caso de erro
            $(selectElement).val(statusCell.text());
        }
    });
}
// Função auxiliar para mostrar mensagens
function mostrarMensagem(texto, tipo) {
    const mensagem = $(`<div class="alert alert-${tipo}">${texto}</div>`);
    $('#mensagens').append(mensagem);
    setTimeout(() => mensagem.fadeOut('slow', function() { $(this).remove(); }), 3000);
}

