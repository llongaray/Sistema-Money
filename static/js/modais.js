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
        
        if (cleanedModalId === 'modalListaClientes') {
            console.log('Chamando preencherTabelaClientes');
            preencherTabelaClientes();
        }
        else if (cleanedModalId === 'modalTodosAgendamentos') {
            console.log('Chamando preencherTabelaTodosAgendamentos');
            preencherTabelaTodosAgendamentos();
        }
        else if (cleanedModalId === 'modalAgendamentosAtrasados') {
            console.log('Chamando preencherTabelaAtrasados');
            preencherTabelaAtrasados();
        }
        
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

function abrirModalOptions(modalId) {
    console.log(`Tentando abrir modal via options: ${modalId}`);
    
    document.querySelectorAll('.modal.active, .modal-sec.active').forEach(modal => {
        if (modal.id !== modalId.replace('#', '')) {
            modal.classList.remove('active');
            console.log(`Fechando modal: ${modal.id}`);
        }
    });

    openModal(modalId);
}

function abrirSubModal(modalId, tipoModal, id) {
    console.log(`Abrindo sub-modal com ID: ${modalId}, tipo: ${tipoModal}, ID do agendamento: ${id}`);

    openSubModal(modalId);
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

    // Declaramos agendamentosEdicao como objeto vazio
    let agendamentosEdicao = null;

    if (tipoModal === 'listaClientes') {
        const dados = todosAgendamentos.find(c => c.id === id);

        if (!id || id === 'undefined' || !dados) {
            console.error(`ID inválido ou cliente com ID ${id} não encontrado em todosAgendamentos`);
            return;
        }

        console.log("Dados do cliente:", dados);

        try {
            const agendamentoId = subModal.querySelector('#agendamentoId');
            if (agendamentoId) {
                agendamentoId.value = dados.id;
                console.log(`Agendamento ID preenchido com: ${dados.id}`);
            }

            const campos = {
                '#nomeCliente': dados.nome_cliente,
                '#cpfCliente': dados.cpf_cliente,
                '#numeroCliente': dados.numero_cliente,
                '#diaAgendado': dados.dia_agendado, // Ajustado para usar a propriedade correta
                '#tabulacaoAtendente': dados.tabulacao_atendente,
                '#atendenteAgendou': dados.atendente_nome,
                '#lojaAgendada': dados.loja_nome
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
                vendedorSelect.innerHTML = '<option value="">Selecione um vendedor</option>';
                preencherSelectVendedores(vendedorSelect);
                
                if (dados.vendedorLoja) {
                    vendedorSelect.value = dados.vendedorLoja;
                    console.log(`Vendedor selecionado: ${dados.vendedorLoja}`);
                }
            } else {
                console.warn('Select de vendedores não encontrado');
            }

            const tabulacaoVendedor = subModal.querySelector('#tabulacaoVendedor');
            const observacaoVendedor = subModal.querySelector('#observacaoVendedor');
            const observacaoContainer = subModal.querySelector('#observacaoVendedorContainer');
            const fechouNegocioContainer = subModal.querySelector('#fechouNegocioContainer');

            if (tabulacaoVendedor && dados.tabulacaoVendedor) {
                tabulacaoVendedor.value = dados.tabulacaoVendedor;
                console.log(`Tabulação do vendedor: ${dados.tabulacaoVendedor}`);

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
        // Verifica se todosAgendamentos está carregado
        if (!todosAgendamentos || todosAgendamentos.length === 0) {
            console.error("todosAgendamentos ainda não foi carregado.");
            return;
        }
    
        // Convertendo o ID para string para garantir a comparação correta
        const idExistente = todosAgendamentos.find(agendamento => agendamento.id === String(id));
    
        if (idExistente) {
            console.log('Dados do agendamento encontrados:', idExistente);
            agendamentosEdicao = idExistente;
    
            subModal.querySelector('#idAgendamentoConfirmacao').value = id;
            subModal.querySelector('#nomeClienteConfirmacao').value = agendamentosEdicao.nome_cliente;
            subModal.querySelector('#diaAgendadoConfirmacao').value = agendamentosEdicao.dia_agendado;
            subModal.querySelector('#numeroClienteConfirmacao').value = agendamentosEdicao.numero_cliente;
            subModal.querySelector('#lojaAgendadaConfirmacao').value = agendamentosEdicao.loja_nome;
            subModal.querySelector('#tabulacaoAtendente').value = agendamentosEdicao.tabulacao_atendente;
    
            console.log('ID do agendamento definido:', id);
        } else {
            console.error(`ID inválido ou agendamento com ID ${id} não encontrado`);
            return;
        }
    }
    
}


function preencherTabelaClientes() {
    console.log('Iniciando preenchimento da tabela de clientes');
    
    const $tabela = $('#modalListaClientes #tabelaClientesLoja tbody');
    
    if (!$tabela.length) {
        console.error('Tabela não encontrada!');
        return;
    }
    
    $tabela.empty();
    console.log('Tabela limpa');

    clientesLoja.forEach(cliente => {
        const nomeElement = `<button type="button" class="btn-link abrir-sub-modal" 
            onclick="abrirSubModal('#modalEdicaoCliente', 'listaClientes', '${cliente.id}')">
            ${cliente.nome_cliente}
        </button>`;

        const row = `
            <tr>
                <td>${nomeElement}</td>
                <td>${cliente.cpf_cliente}</td>
                <td>${cliente.numero_cliente}</td>
                <td>${cliente.dia_agendado}</td>
                <td>${cliente.atendente_nome}</td>
                <td>${cliente.loja_nome}</td>
                <td>${cliente.status || 'N/A'}</td>
            </tr>
        `;
        
        $tabela.append(row);
    });
    
    console.log('Preenchimento da tabela concluído');
}

let sortDirection = 'desc';

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

    const agendamentosPorCPF = {};
    todosAgendamentos.forEach(agendamento => {
        if (!agendamentosPorCPF[agendamento.cpf_cliente]) {
            agendamentosPorCPF[agendamento.cpf_cliente] = [];
        }
        agendamentosPorCPF[agendamento.cpf_cliente].push(agendamento);
    });

    Object.values(agendamentosPorCPF).forEach(agendamentos => {
        agendamentos.sort((a, b) => new Date(b.dia_agendado) - new Date(a.dia_agendado));
        
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

document.addEventListener('DOMContentLoaded', function() {
    const mensagensContainer = document.getElementById('mensagens');
    const temMensagemSucesso = mensagensContainer && 
                              mensagensContainer.querySelector('.success');
    
    // Remover esta parte que restaura o modal antigo
    // if (temMensagemSucesso) {
    //     saveActiveModalState(null);
    //     console.log('Estado do modal removido - mensagem de sucesso');
    // } else {
    //     restoreActiveModalState();
    // }

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

    document.querySelectorAll('.modal-sec form').forEach(form => {
        form.addEventListener('submit', handleSubModalFormSubmit);
    });

    document.querySelectorAll('.modal-sec .btn-close').forEach(button => {
        button.addEventListener('click', function() {
            const modalId = this.closest('.modal-sec').id;
            closeSubModal(modalId);
        });
    });

    document.querySelectorAll('.modal-sec').forEach(modalSec => {
        modalSec.addEventListener('click', function(event) {
            if (event.target === this) {
                closeSubModal(this.id);
            }
        });
    });

    document.addEventListener('click', function(event) {
        // Verifica se o clique foi fora de um modal-sec
        if (event.target.classList.contains('modal-sec')) {
            // Não faz nada se o clique foi dentro do modal-sec
            return;
        }

        // Se o clique foi fora de um modal, fecha o modal
        if (event.target.classList.contains('modal-sec')) {
            fecharModal(event.target.id);
        }
    });

    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            document.querySelectorAll('.modal.active, .modal-sec.active').forEach(modal => {
                fecharModal(modal.id);
            });
        }
    });

    const urlParams = new URLSearchParams(window.location.search);
    const keepModalId = urlParams.get('keepModal');
    const lastActiveModal = sessionStorage.getItem('lastActiveModal');

    if (keepModalId) {
        console.log(`Restaurando modal específico: ${keepModalId}`);
        openModal(keepModalId);
        window.history.replaceState({}, document.title, window.location.pathname);
    } else if (lastActiveModal) {
        console.log(`Restaurando último modal ativo: ${lastActiveModal}`);
        openModal(lastActiveModal);
        sessionStorage.removeItem('lastActiveModal');
    }

    // Verifica se deve abrir o modal padrão após reload
    const defaultModal = sessionStorage.getItem('defaultModal');
    if (defaultModal) {
        console.log(`Abrindo modal padrão após reload: ${defaultModal}`);
        openModal(defaultModal);
        sessionStorage.removeItem('defaultModal');
    }

    // Adiciona listener específico para o form de meta
    const formMeta = document.querySelector('form[name="form_type"][value="adicionar_meta"]');
    if (formMeta) {
        formMeta.addEventListener('submit', function(event) {
            event.preventDefault();
            const metaModal = document.getElementById('modalAdicionarMeta');
            if (metaModal) {
                metaModal.classList.remove('active');
                console.log('Modal de meta fechado antes do submit');
            }
            handleSubModalFormSubmit(event);
        });
    }

    // Adiciona listener específico para formulários em modais
    document.querySelectorAll('.modal form, .modal-sec form').forEach(form => {
        form.addEventListener('submit', function(event) {
            event.preventDefault();
            
            // Fecha todos os modais antes do submit
            document.querySelectorAll('.modal.active, .modal-sec.active').forEach(modal => {
                modal.classList.remove('active');
                console.log(`Fechando modal: ${modal.id}`);
            });
            
            handleSubModalFormSubmit(event);
        });
    });
});

document.querySelectorAll('.modal').forEach(modal => {
    modal.addEventListener('click', handleModalClick);
});

document.getElementById('modalConfirmacaoAgendamento')
    .querySelector('#tabulacaoAtendente')
    .addEventListener('change', handleTabulacaoChange);

$(document).ready(function() {
    $('[data-target="#modalListaClientes"]').on('click', function() {
        console.log('Botão de lista de clientes clicado');
        openModal('modalListaClientes');
        return false;
    });

    $("#filtroCPF").on("keyup", function() {
        const value = $(this).val().toLowerCase();
        $("#tabelaTodosAgendamentos tbody tr").filter(function() {
            $(this).toggle($(this).children("td:eq(1)").text().toLowerCase().indexOf(value) > -1);
        });
    });

    $('.sortable[data-sort="data"]').on('click', function() {
        sortDirection = sortDirection === 'desc' ? 'asc' : 'desc';
        const icon = $(this).find('i');
        icon.removeClass('fa-sort-down fa-sort-up')
            .addClass(sortDirection === 'desc' ? 'fa-sort-down' : 'fa-sort-up');
        preencherTabelaTodosAgendamentos();
    });

    $('.sortable').css('cursor', 'pointer');

    $('.text-uppercase').on('input', function() {
        this.value = this.value.toUpperCase();
    });

    // Função para aplicar todos os filtros
    function aplicarFiltros() {
        const filtroNome = $("#filtroNome").val().toLowerCase();
        const filtroCPF = $("#filtroCPF").val().toLowerCase();
        const filtroData = $("#filtroData").val();
        const filtroAtendente = $("#filtroAtendente").val().toLowerCase();
        const filtroLoja = $("#filtroLoja").val().toLowerCase();

        $("#tabelaTodosAgendamentos tbody tr").each(function() {
            const $row = $(this);
            const nome = $row.find("td:eq(0)").text().toLowerCase();
            const cpf = $row.find("td:eq(1)").text().toLowerCase();
            const data = $row.find("td:eq(3)").attr("data-date");
            const atendente = $row.find("td:eq(4)").text().toLowerCase();
            const loja = $row.find("td:eq(5)").text().toLowerCase();

            const matchNome = !filtroNome || nome.includes(filtroNome);
            const matchCPF = !filtroCPF || cpf.includes(filtroCPF);
            const matchData = !filtroData || data.includes(filtroData);
            const matchAtendente = !filtroAtendente || atendente.includes(filtroAtendente);
            const matchLoja = !filtroLoja || loja.includes(filtroLoja);

            const shouldShow = matchNome && matchCPF && matchData && 
                             matchAtendente && matchLoja;
            
            $row.toggle(shouldShow);
        });
    }

    // Adicionar eventos para todos os campos de filtro
    $("#filtroNome, #filtroCPF, #filtroData, #filtroAtendente, #filtroLoja")
        .on("keyup change", aplicarFiltros);

    // Evento para limpar todos os filtros
    $("#limparFiltros").on("click", function() {
        $("#filtroNome, #filtroCPF, #filtroData, #filtroAtendente, #filtroLoja")
            .val('');
        $("#tabelaTodosAgendamentos tbody tr").show();
    });

    // Adicionar debounce para melhor performance
    let timeoutId;
    $(".form-control").on("keyup change", function() {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(aplicarFiltros, 300);
    });

    // Função para aplicar filtros na tabela de clientes loja
    function aplicarFiltrosClientesLoja() {
        const filtroNome = $("#filtroNomeClientes").val().toLowerCase();
        const filtroCPF = $("#filtroCPFClientes").val().toLowerCase();
        const filtroAtendente = $("#filtroAtendenteClientes").val().toLowerCase();
        const filtroLoja = $("#filtroLojaClientes").val().toLowerCase();

        $("#tabelaClientesLoja tbody tr").each(function() {
            const $row = $(this);
            const nome = $row.find("td:eq(0)").text().toLowerCase();
            const cpf = $row.find("td:eq(1)").text().toLowerCase();
            const atendente = $row.find("td:eq(4)").text().toLowerCase();
            const loja = $row.find("td:eq(5)").text().toLowerCase();

            const matchNome = !filtroNome || nome.includes(filtroNome);
            const matchCPF = !filtroCPF || cpf.includes(filtroCPF);
            const matchAtendente = !filtroAtendente || atendente.includes(filtroAtendente);
            const matchLoja = !filtroLoja || loja.includes(filtroLoja);

            const shouldShow = matchNome && matchCPF && matchAtendente && matchLoja;
            
            $row.toggle(shouldShow);
        });
    }

    // Eventos para os filtros da tabela de clientes loja
    let timeoutIdClientesLoja;
    $("#filtroNomeClientes, #filtroCPFClientes, #filtroAtendenteClientes, #filtroLojaClientes")
        .on("keyup change", function() {
            clearTimeout(timeoutIdClientesLoja);
            timeoutIdClientesLoja = setTimeout(aplicarFiltrosClientesLoja, 300);
        });

    // Função para aplicar filtros na tabela de agendamentos atrasados
    function aplicarFiltrosAtrasados() {
        const filtroNome = $("#filtroNomeAtrasados").val().toLowerCase();
        const filtroCPF = $("#filtroCPFAtrasados").val().toLowerCase();
        const filtroAtendente = $("#filtroAtendenteAtrasados").val().toLowerCase();
        const filtroLoja = $("#filtroLojaAtrasados").val().toLowerCase();

        $("#modalAgendamentosAtrasados .wp-style-table tbody tr").each(function() {
            const $row = $(this);
            
            // Ignora a linha de "nenhum cliente encontrado"
            if ($row.find('td[colspan]').length) return;

            // Garantir que os índices correspondam à ordem das colunas na tabela
            const nome = $row.find("td:eq(0)").text().toLowerCase();
            const cpf = $row.find("td:eq(1)").text().toLowerCase();
            const atendente = $row.find("td:eq(4)").text().toLowerCase();
            const loja = $row.find("td:eq(5)").text().toLowerCase();

            const matchNome = !filtroNome || nome.includes(filtroNome);
            const matchCPF = !filtroCPF || cpf.includes(filtroCPF);
            const matchAtendente = !filtroAtendente || atendente.includes(filtroAtendente);
            const matchLoja = !filtroLoja || loja.includes(filtroLoja);

            const shouldShow = matchNome && matchCPF && matchAtendente && matchLoja;
            
            $row.toggle(shouldShow);
        });
    }

    // Eventos para os filtros da tabela de agendamentos atrasados
    let timeoutIdAtrasados;
    $("#filtroNomeAtrasados, #filtroCPFAtrasados, #filtroAtendenteAtrasados, #filtroLojaAtrasados")
        .on("keyup change", function() {
            clearTimeout(timeoutIdAtrasados);
            timeoutIdAtrasados = setTimeout(aplicarFiltrosAtrasados, 300);
        });
});

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

function handleModalClick(event) {
    if (event.target.classList.contains('modal-sec')) {
        closeSubModal(event.target.id);
        event.stopPropagation();
    }
}

function handleSubModalFormSubmit(event) {
    event.preventDefault();
    const form = event.target;
    const formType = form.querySelector('input[name="form_type"]').value;

    console.log(`Processando submit do formulário tipo: ${formType}`);

    // Adicionando os novos tipos de formulário permitidos
    const tiposPermitidos = [
        'criar_campanha', 
        'consulta_cliente', 
        'importar_csv', 
        'adicionar_registro', 
        'adicionar_meta', 
        'alterar_status_meta', 
        'excluir_registro', 
        'agendamento', 
        'status_tac', 
        'lista_clientes', 
        'confirmacao_agendamento',
        'delete_funcionario', 
        'criar_horario', 
        'excluir_cargo', 
        'criar_cargo', 
        'criar_departamento', 
        'delete_loja', 
        'criar_loja', 
        'criar_empresa', 
        'associar_grupos', 
        'cadastrar_usuario', 
        'cadastro_funcionario',
        'importar_csv_money'
    ];

    // Se o tipo de formulário estiver na lista permitida, permite o submit normal
    if (tiposPermitidos.includes(formType)) {
        console.log(`Submetendo formulário de ${formType} normalmente.`);
        form.submit(); // Permite o submit padrão
        return; // Sai da função
    }

    // Fecha todos os modais antes do submit
    document.querySelectorAll('.modal.active, .modal-sec.active').forEach(modal => {
        modal.classList.remove('active');
        console.log(`Fechando modal: ${modal.id}`);
    });

    // Limpa todos os estados salvos
    sessionStorage.removeItem('activeModal');
    sessionStorage.removeItem('lastActiveModal');
    sessionStorage.removeItem('defaultModal');

    // Define a URL correta com base no tipo de formulário
    let url;
    if (formType === 'update_funcionario' || formType === 'update_user') {
        url = form.action; // A URL já está definida no action do formulário
    } else {
        console.error('Tipo de formulário não reconhecido:', formType);
        return; // Sai da função se o tipo não for reconhecido
    }

    $.ajax({
        url: url,
        method: form.method,
        data: new FormData(form),
        processData: false,
        contentType: false,
        success: function(response) {
            console.log('Formulário enviado com sucesso');
            // Lógica de sucesso
        },
        error: function(xhr, status, error) {
            console.error('Erro ao enviar formulário:', error);
            mostrarMensagem('Erro ao processar formulário', 'error');
        }
    });
}

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
                statusCell.text(novoStatus);
                
                mostrarMensagem('Status atualizado com sucesso!', 'success');
                
                if (novoStatus === 'PAGO') {
                    row.addClass('tac-pago');
                } else {
                    row.removeClass('tac-pago');
                }
            } else {
                mostrarMensagem('Erro ao atualizar status: ' + response.error, 'error');
                $(selectElement).val(statusCell.text());
            }
        },
        error: function() {
            mostrarMensagem('Erro ao comunicar com o servidor', 'error');
            $(selectElement).val(statusCell.text());
        }
    });
}

function mostrarMensagem(texto, tipo) {
    const mensagem = $(`<div class="alert alert-${tipo}">${texto}</div>`);
    $('#mensagens').append(mensagem);
    setTimeout(() => mensagem.fadeOut('slow', function() { $(this).remove(); }), 3000);
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

function preencherTabelaAtrasados() {
    console.log('Iniciando preenchimento da tabela de agendamentos atrasados');
    
    // Corrigir o seletor da tabela para incluir o ID correto
    const $tabela = $('#modalAgendamentosAtrasados .wp-style-table tbody');
    
    if (!$tabela.length) {
        console.error('Tabela de atrasados não encontrada!');
        return;
    }
    
    $tabela.empty();
    console.log('Tabela de atrasados limpa');

    if (!agendamentosAtrasados || agendamentosAtrasados.length === 0) {
        $tabela.append(`
            <tr>
                <td colspan="6" class="text-center">Nenhum cliente atrasado encontrado</td>
            </tr>
        `);
        return;
    }

    agendamentosAtrasados.forEach(agendamento => {
        // Garantir que os campos correspondam exatamente aos do dicionário
        const row = `
            <tr>
                <td>${agendamento.nome_cliente || ''}</td>
                <td>${agendamento.cpf_cliente || ''}</td>
                <td>${agendamento.numero_cliente || ''}</td>
                <td data-date="${agendamento.dia_agendado || ''}">${agendamento.dia_agendado || ''}</td>
                <td>${agendamento.atendente_nome || ''}</td>
                <td>${agendamento.loja_nome || ''}</td>
            </tr>
        `;
        
        $tabela.append(row);
    });
    
    console.log('Preenchimento da tabela de atrasados concluído');
}

// Função para aplicar filtros na tabela de atrasados
function aplicarFiltrosAtrasados() {
    const filtroNome = $("#filtroNomeAtrasados").val().toLowerCase();
    const filtroCPF = $("#filtroCPFAtrasados").val().toLowerCase();
    const filtroAtendente = $("#filtroAtendenteAtrasados").val().toLowerCase();
    const filtroLoja = $("#filtroLojaAtrasados").val().toLowerCase();

    $("#modalAgendamentosAtrasados .wp-style-table tbody tr").each(function() {
        const $row = $(this);
        
        // Ignora a linha de "nenhum cliente encontrado"
        if ($row.find('td[colspan]').length) return;

        // Garantir que os índices correspondam à ordem das colunas na tabela
        const nome = $row.find("td:eq(0)").text().toLowerCase();
        const cpf = $row.find("td:eq(1)").text().toLowerCase();
        const atendente = $row.find("td:eq(4)").text().toLowerCase();
        const loja = $row.find("td:eq(5)").text().toLowerCase();

        const matchNome = !filtroNome || nome.includes(filtroNome);
        const matchCPF = !filtroCPF || cpf.includes(filtroCPF);
        const matchAtendente = !filtroAtendente || atendente.includes(filtroAtendente);
        const matchLoja = !filtroLoja || loja.includes(filtroLoja);

        const shouldShow = matchNome && matchCPF && matchAtendente && matchLoja;
        
        $row.toggle(shouldShow);
    });
}

