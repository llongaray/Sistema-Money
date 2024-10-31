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
        if (!id || id === 'undefined' || !clientesLoja[id]) {
            console.error(`ID inválido ou cliente com ID ${id} não encontrado em clientesLoja`);
            return;
        }

        const dados = clientesLoja[id];
        console.log("Dados do cliente:", dados);

        try {
            const agendamentoSelect = subModal.querySelector('#agendamentoId');
            if (agendamentoSelect) {
                if (!dados.id || dados.id === 'undefined') {
                    console.error('ID do agendamento inválido');
                    return;
                }
                agendamentoSelect.value = dados.id;
                console.log(`Agendamento ID preenchido com: ${dados.id}`);
            }

            const campos = {
                '#nomeCliente': dados.nome,
                '#cpfCliente': dados.cpf,
                '#numeroCliente': dados.numero,
                '#diaAgendado': dados.diaAgendado,
                '#tabulacaoAtendente': dados.tabulacaoAtendente,
                '#atendenteAgendou': dados.atendenteAgendou,
                '#lojaAgendada': dados.lojaAgendada
            };

            Object.entries(campos).forEach(([selector, valor]) => {
                const elemento = subModal.querySelector(selector);
                if (elemento) {
                    elemento.value = valor || '';
                    console.log(`Campo ${selector} preenchido com: ${valor}`);
                } else {
                    console.warn(`Elemento ${selector} não encontrado no modal`);
                }
            });

            const vendedorSelect = subModal.querySelector('#vendedorLoja');
            if (vendedorSelect) {
                preencherSelectVendedores(vendedorSelect);
                
                if (dados.vendedorLoja && dados.vendedorLoja !== 'undefined') {
                    vendedorSelect.value = dados.vendedorLoja;
                    console.log(`Vendedor selecionado: ${dados.vendedorLoja}`);
                }
            } else {
                console.warn('Select de vendedores não encontrado');
            }

            const tabulacaoVendedor = subModal.querySelector('#tabulacaoVendedor');
            const observacaoVendedor = subModal.querySelector('#observacaoVendedor');
            const observacaoContainer = subModal.querySelector('#observacaoVendedorContainer');

            if (tabulacaoVendedor && dados.tabulacaoVendedor) {
                tabulacaoVendedor.value = dados.tabulacaoVendedor;
                console.log(`Tabulação do vendedor: ${dados.tabulacaoVendedor}`);

                if (observacaoVendedor && dados.observacaoVendedor) {
                    observacaoVendedor.value = dados.observacaoVendedor;
                    if (observacaoContainer) {
                        observacaoContainer.style.display = 'block';
                    }
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

    const clientesPorCPF = {};
    clientesLojaData.forEach(cliente => {
        if (!clientesPorCPF[cliente.cpf]) {
            clientesPorCPF[cliente.cpf] = [];
        }
        clientesPorCPF[cliente.cpf].push(cliente);
    });

    Object.values(clientesPorCPF).forEach(clientes => {
        clientes.sort((a, b) => new Date(b.diaAgendado) - new Date(a.diaAgendado));

        clientes.forEach((cliente, index) => {
            const isRecente = index === 0;
            const nomeElement = isRecente ? 
                `<a href="#" class="abrir-sub-modal" onclick="abrirSubModal('#modalEdicaoCliente', 'listaClientes', ${cliente.id})">${cliente.nome}</a>` :
                `<p class="text-muted">${cliente.nome}</p>`;

            const row = `
                <tr>
                    <td>${nomeElement}</td>
                    <td>${cliente.cpf}</td>
                    <td>${cliente.numero}</td>
                    <td>${cliente.diaAgendadoFormatado}</td>
                </tr>
            `;
            
            $tabela.append(row);
            console.log(`Linha adicionada para cliente ${cliente.nome}`);
        });
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

    // Ordenar o dicionário por data
    todosAgendamentos.sort((a, b) => {
        const dateA = new Date(a.dia_agendado);
        const dateB = new Date(b.dia_agendado);
        return sortDirection === 'desc' ? dateB - dateA : dateA - dateB;
    });

    // Converter e armazenar dados no formato correto
    todosAgendamentos.forEach(agendamento => {
        window.clientesLoja = window.clientesLoja || {};
        window.clientesLoja[agendamento.id] = converterParaFormatoClienteLoja(agendamento);
    });

    // Agrupar por CPF
    const agendamentosPorCPF = {};
    todosAgendamentos.forEach(agendamento => {
        if (!agendamentosPorCPF[agendamento.cpf_cliente]) {
            agendamentosPorCPF[agendamento.cpf_cliente] = [];
        }
        agendamentosPorCPF[agendamento.cpf_cliente].push(agendamento);
    });

    Object.values(agendamentosPorCPF).forEach(agendamentos => {
        agendamentos.forEach((agendamento, index) => {
            const isRecente = index === 0;
            const nomeElement = isRecente ? 
                `<a href="#" class="abrir-sub-modal" onclick="abrirSubModal('#modalEdicaoCliente', 'listaClientes', '${agendamento.id}')">${agendamento.nome_cliente}</a>` :
                `<p class="text-muted">${agendamento.nome_cliente}</p>`;

            const dataCompleta = new Date(agendamento.dia_agendado);
            const dataFormatada = dataCompleta.toISOString().split('T')[0];

            const row = `
                <tr>
                    <td>${nomeElement}</td>
                    <td>${agendamento.cpf_cliente}</td>
                    <td>${agendamento.numero_cliente}</td>
                    <td data-date="${agendamento.dia_agendado}">${dataFormatada}</td>
                    <td>${agendamento.atendente_nome}</td>
                    <td>${agendamento.loja_nome}</td>
                    <td>${agendamento.status_dias}</td>
                </tr>
            `;
            
            $tabela.append(row);
        });
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
    
    console.log('Select dropdown vendedor:', tabulacaoSelect); 
    console.log('Valor selecionado no dropdown vendedor:', selectedValue);
    
    const observacaoContainer = modal.querySelector('#observacaoVendedorContainer');
    observacaoContainer.style.display = 'none';
    
    if (selectedValue && selectedValue !== '') {
        console.log('Tabulação selecionada, mostrando campo de observação');
        observacaoContainer.style.display = 'block';
    } else {
        console.log('Nenhuma tabulação selecionada');
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

// Atualizar a função handleModalClick para não fechar modais principais quando clicando em sub-modais
function handleModalClick(event) {
    const modal = event.target.closest('.modal, .modal-sec');
    if (!modal) return;

    // Se o clique foi no backdrop (fora do conteúdo do modal)
    if (event.target === modal) {
        if (modal.classList.contains('modal-sec')) {
            closeSubModal(modal.id);
        } else {
            closeAllModals();
        }
    }
}

// Adicionar função para lidar com o submit dos formulários em sub-modais
function handleSubModalFormSubmit(event) {
    event.preventDefault();
    const form = event.target;
    const subModal = form.closest('.modal-sec');
    
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
                closeSubModal(subModal.id);
            }
            // Atualizar a página ou fazer outras ações necessárias
            location.reload();
        },
        error: function(xhr, status, error) {
            console.error('Erro ao enviar formulário:', error);
        }
    });
}
