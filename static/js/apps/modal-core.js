console.log('MODAL-CORE EM EXECUÇÃO!!');


// USO UNIVERSAL: Salva o estado do modal ativo na sessão
function saveActiveModalState(modalId) {
    if (modalId) {
        sessionStorage.setItem('activeModal', modalId.replace('#', ''));
        console.log(`Estado do modal salvo: ${modalId}`);
    } else {
        sessionStorage.removeItem('activeModal');
        console.log('Estado do modal removido');
    }
}

// USO UNIVERSAL: Restaura o estado do último modal ativo
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

// USO UNIVERSAL: Abre um modal e gerencia o estado
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

// USO UNIVERSAL: Abre um sub-modal
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

// USO UNIVERSAL: Fecha todos os modais ativos
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

// USO UNIVERSAL: Fecha um modal específico
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

// USO UNIVERSAL: Abre modal com opções
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

// USO UNIVERSAL: Abre sub-modal com dados específicos
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

// USO UNIVERSAL: Preenche dados em sub-modais
function preencherDadosSubModal(subModal, tipoModal, id) {
    console.log("Iniciando preenchimento do sub-modal para ID:", id);
    console.log("Tipo do ID:", typeof id);
    console.log("Todos Agendamentos disponíveis:", todosAgendamentos);

    let agendamentosEdicao = null;

    if (tipoModal === 'listaClientes') {
        // Garantir que estamos trabalhando com strings
        const idString = String(id).trim();
        
        // Verificar se todosAgendamentos existe e tem dados
        if (!todosAgendamentos || !Array.isArray(todosAgendamentos)) {
            console.error("todosAgendamentos não está definido ou não é um array");
            return;
        }

        // Procurar o agendamento com log detalhado
        const dados = todosAgendamentos.find(agendamento => {
            console.log(`Comparando: ${String(agendamento.id)} (${typeof agendamento.id}) com ${idString} (${typeof idString})`);
            return String(agendamento.id) === idString;
        });

        if (!dados) {
            console.error(`ID ${idString} não encontrado em todosAgendamentos`);
            console.log("IDs disponíveis:", todosAgendamentos.map(a => a.id).join(', '));
            return;
        }

        console.log("Dados encontrados:", dados);

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
                '#diaAgendado': dados.dia_agendado,
                '#tabulacaoAtendente': dados.tabulacao_atendente,
                '#atendenteAgendou': dados.atendente_nome,
                '#lojaAgendada': dados.loja_nome,
                '#agendamentoId': dados.id
            };

            // Preencher campos
            Object.entries(campos).forEach(([selector, valor]) => {
                const elemento = subModal.querySelector(selector);
                if (elemento) {
                    elemento.value = valor || '';
                    console.log(`Campo ${selector} preenchido com: ${valor}`);
                } else {
                    console.warn(`Elemento não encontrado: ${selector}`);
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
            console.error('Erro ao preencher dados:', error);
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

// USO UNIVERSAL: Converte dados para formato cliente loja
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

// USO UNIVERSAL: Preenche select de vendedores
function preencherSelectVendedores(selectElement) {
    Object.values(vendedoresListaClientes).forEach(vendedor => {
        const option = document.createElement('option');
        option.value = vendedor.id;
        option.textContent = vendedor.nome;
        selectElement.appendChild(option);
    });
}

// USO UNIVERSAL: Event Listeners após carregamento do DOM
document.addEventListener('DOMContentLoaded', function() {
    const mensagensContainer = document.getElementById('mensagens');
    const temMensagemSucesso = mensagensContainer && 
                              mensagensContainer.querySelector('.success');

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
            
            const tipoMeta = document.querySelector('#tipo_meta');
            const setorField = document.querySelector('#setor');
            const lojaField = document.querySelector('#loja');
            
            if (tipoMeta && tipoMeta.value === 'INDIVIDUAL') {
                if (setorField) setorField.required = true;
                if (lojaField) lojaField.required = true;
            } else {
                if (setorField) setorField.required = false;
                if (lojaField) lojaField.required = false;
            }
            
            this.submit();
        });
    }

    // Adiciona listener para o tipo de meta
    const tipoMetaSelect = document.querySelector('#tipo_meta');
    const setorContainer = document.querySelector('#setor_container');
    const lojaContainer = document.querySelector('#loja_container');
    
    if (tipoMetaSelect) {
        tipoMetaSelect.addEventListener('change', function() {
            if (setorContainer && lojaContainer) {
                const isIndividual = this.value === 'INDIVIDUAL';
                setorContainer.style.display = isIndividual ? 'block' : 'none';
                lojaContainer.style.display = isIndividual ? 'block' : 'none';
            }
        });
        
        // Dispara o evento change para configurar o estado inicial
        tipoMetaSelect.dispatchEvent(new Event('change'));
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

// USO UNIVERSAL: Fecha um sub-modal específico
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

// USO UNIVERSAL: Gerencia cliques em modais
function handleModalClick(event) {
    if (event.target.classList.contains('modal-sec')) {
        closeSubModal(event.target.id);
        event.stopPropagation();
    }
}

// USO UNIVERSAL: Gerencia submissão de formulários em sub-modais
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
        'importar_csv_money',
        'importar_situacao',
        'cliente_rua',
        'registro_equipe',
        'adicionar_membro',
        'registrar_pontos'
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


// USO UNIVERSAL: Exibe mensagens temporárias
function mostrarMensagem(texto, tipo) {
    const mensagem = $(`<div class="alert alert-${tipo}">${texto}</div>`);
    $('#mensagens').append(mensagem);
    setTimeout(() => mensagem.fadeOut('slow', function() { $(this).remove(); }), 3000);
}

// USO UNIVERSAL: Fecha um sub-modal
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

// USO UNIVERSAL: Event Listeners jQuery
$(document).ready(function() {
    // Função para filtrar a tabela de todos os agendamentos
    function filtrarTabelaTodosAgendamentos() {
        var nome = $("#modalTodosAgendamentos #filtroNome").val().toLowerCase();
        var cpf = $("#modalTodosAgendamentos #filtroCPF").val().toLowerCase();
        var dia = $("#modalTodosAgendamentos #filtroData").val();
        var atendente = $("#modalTodosAgendamentos #filtroAtendente").val().toLowerCase();
        var loja = $("#modalTodosAgendamentos #filtroLoja").val().toLowerCase();

        $("#tabelaTodosAgendamentos tbody tr").each(function() {
            var row = $(this);
            var nomeCliente = row.find("button").text().toLowerCase();
            var cpfCliente = row.find("td:nth-child(2)").text().toLowerCase();
            var diaAgendado = row.find("td[data-date]").attr("data-date");
            var atendenteTexto = row.find("td:nth-child(5)").text().toLowerCase();
            var lojaTexto = row.find("td:nth-child(6)").text().toLowerCase();

            var matchNome = nomeCliente.includes(nome);
            var matchCPF = cpfCliente.includes(cpf);
            var matchDia = !dia || diaAgendado === dia;
            var matchAtendente = atendenteTexto.includes(atendente);
            var matchLoja = lojaTexto.includes(loja);

            if (matchNome && matchCPF && matchDia && matchAtendente && matchLoja) {
                row.show();
            } else {
                row.hide();
            }
        });

        var temResultados = $("#tabelaTodosAgendamentos tbody tr:visible").length > 0;
        if (!temResultados) {
            if (!$("#tabelaTodosAgendamentos tbody tr.sem-resultados").length) {
                $("#tabelaTodosAgendamentos tbody").append(
                    '<tr class="sem-resultados"><td colspan="8" class="text-center">Nenhum agendamento encontrado</td></tr>'
                );
            }
            $("#tabelaTodosAgendamentos tbody tr.sem-resultados").show();
        } else {
            $("#tabelaTodosAgendamentos tbody tr.sem-resultados").remove();
        }
    }

    // Função para filtrar a tabela de agendamentos
    function filtrarTabelaAgendamentos() {
        var nome = $("#filtroNome").val().toLowerCase();
        var dia = $("#filtroDia").val();
        var atendente = $("#filtroAtendente").val().toLowerCase();
        var loja = $("#filtroLoja").val().toLowerCase();
        var status = $("#filtroStatus").val().toLowerCase();

        $("#tabelaAgendamentos tr.linha-agendamento").each(function() {
            var row = $(this);
            var nomeCliente = row.find("button").text().toLowerCase();
            var diaAgendado = row.find("td[data-dia]").text().trim();
            var atendenteTexto = row.find("td:nth-child(4)").text().toLowerCase();
            var lojaTexto = row.find("td:nth-child(5)").text().toLowerCase();
            var statusTexto = row.find("td:nth-child(6)").text().toLowerCase();

            var matchNome = nomeCliente.includes(nome);
            var matchDia = !dia || (diaAgendado && diaAgendado.includes(dia));
            var matchAtendente = atendenteTexto.includes(atendente);
            var matchLoja = lojaTexto.includes(loja);
            var matchStatus = statusTexto.includes(status);

            if (matchNome && matchDia && matchAtendente && matchLoja && matchStatus) {
                row.show();
            } else {
                row.hide();
            }
        });

        var temResultados = $("#tabelaAgendamentos tr.linha-agendamento:visible").length > 0;
        $("#nenhumResultado").toggle(!temResultados);
    }

    // Função para filtrar a tabela TAC
    function filtrarTabelaTAC() {
        var nome = $("#filtroNomeTAC").val().toLowerCase();
        var cpf = $("#filtroCPFTAC").val().toLowerCase();
        var loja = $("#filtroLojaTAC").val().toLowerCase();
        var status = $("#filtroStatusTAC").val().toLowerCase();
        var periodo = $("#filtroPeriodoTAC").val();
        var dataEspecifica = $("#filtroDataEspecificaTAC").val(); // Nova variável

        // Formata a data atual no formato YYYY-MM-DD
        function formatarData(data) {
            return data.toISOString().split('T')[0];
        }

        // Calcula as datas de início e fim com base no período selecionado
        var hoje = new Date();
        var dataInicio = '';
        var dataFim = '';

        // Se uma data específica foi selecionada, ela tem prioridade sobre o período
        if (dataEspecifica) {
            dataInicio = dataEspecifica;
            dataFim = dataEspecifica;
            // Limpa o select de período para evitar confusão
            $("#filtroPeriodoTAC").val('');
        }
        // Caso contrário, usa o período selecionado
        else if (periodo === 'HOJE') {
            dataInicio = formatarData(hoje);
            dataFim = dataInicio;
        } 
        else if (periodo === 'SEMANA') {
            var inicioSemana = new Date(hoje);
            inicioSemana.setDate(hoje.getDate() - hoje.getDay());
            var fimSemana = new Date(inicioSemana);
            fimSemana.setDate(inicioSemana.getDate() + 6);
            
            dataInicio = formatarData(inicioSemana);
            dataFim = formatarData(fimSemana);
        } 
        else if (periodo === 'MES') {
            var inicioMes = new Date(hoje.getFullYear(), hoje.getMonth(), 1);
            var fimMes = new Date(hoje.getFullYear(), hoje.getMonth() + 1, 0);
            
            dataInicio = formatarData(inicioMes);
            dataFim = formatarData(fimMes);
        }

        $("#modalAgendamentosTAC .tac-row").each(function() {
            var row = $(this);
            var nomeCliente = row.find(".td-nome").text().toLowerCase();
            var cpfCliente = row.find(".td-cpf").text().toLowerCase();
            var lojaTexto = row.find(".td-loja").text().toLowerCase();
            var statusSelect = row.find(".status-select option:selected").text().toLowerCase();
            var dataAgendamento = row.find(".td-data").text(); // Já está no formato YYYY-MM-DD

            var matchNome = nomeCliente.includes(nome);
            var matchCPF = cpfCliente.includes(cpf);
            var matchLoja = lojaTexto.includes(loja);
            var matchStatus = status === "" || statusSelect === status.toLowerCase();
            
            // Verifica o período ou data específica
            var matchData = true;
            if (dataInicio && dataFim) {
                matchData = dataAgendamento >= dataInicio && dataAgendamento <= dataFim;
            }

            if (matchNome && matchCPF && matchLoja && matchStatus && matchData) {
                row.show();
            } else {
                row.hide();
            }
        });

        // Atualiza a mensagem de "nenhum resultado encontrado"
        var temResultados = $("#modalAgendamentosTAC .tac-row:visible").length > 0;
        if (!temResultados) {
            if (!$("#modalAgendamentosTAC .sem-resultados").length) {
                $("#modalAgendamentosTAC tbody").append(
                    '<tr class="sem-resultados"><td colspan="6" class="text-center">Nenhum agendamento encontrado</td></tr>'
                );
            }
            $("#modalAgendamentosTAC .sem-resultados").show();
        } else {
            $("#modalAgendamentosTAC .sem-resultados").remove();
        }
    }

    // Event listeners para todos os agendamentos
    $("#modalTodosAgendamentos #filtroNome, #modalTodosAgendamentos #filtroCPF, #modalTodosAgendamentos #filtroAtendente, #modalTodosAgendamentos #filtroLoja").on("keyup change", filtrarTabelaTodosAgendamentos);
    $("#modalTodosAgendamentos #filtroData").on("change", filtrarTabelaTodosAgendamentos);

    // Event listeners para agendamentos
    $("#filtroNome, #filtroAtendente, #filtroLoja, #filtroStatus").on("keyup change", filtrarTabelaAgendamentos);
    $("#filtroDia").on("change", filtrarTabelaAgendamentos);

    // Event listeners para TAC (atualizado para incluir o filtro de loja)
    $("#filtroNomeTAC, #filtroCPFTAC, #filtroLojaTAC, #filtroStatusTAC, #filtroPeriodoTAC, #filtroDataEspecificaTAC")
        .on("keyup change", filtrarTabelaTAC);

    // Quando selecionar uma data específica, limpa o período
    $("#filtroDataEspecificaTAC").on("change", function() {
        if ($(this).val()) {
            $("#filtroPeriodoTAC").val('');
        }
        filtrarTabelaTAC();
    });

    // Quando selecionar um período, limpa a data específica
    $("#filtroPeriodoTAC").on("change", function() {
        if ($(this).val()) {
            $("#filtroDataEspecificaTAC").val('');
        }
        filtrarTabelaTAC();
    });

    // Limpar filtros ao fechar modais
    $("#modalTodosAgendamentos").on("hidden.bs.modal", function() {
        $("#modalTodosAgendamentos #filtroNome, #modalTodosAgendamentos #filtroCPF, #modalTodosAgendamentos #filtroData, #modalTodosAgendamentos #filtroAtendente, #modalTodosAgendamentos #filtroLoja").val("");
        filtrarTabelaTodosAgendamentos();
    });

    $("#modalConfiAgendamentoTabela").on("hidden.bs.modal", function() {
        $("#filtroNome, #filtroDia, #filtroAtendente, #filtroLoja, #filtroStatus").val("");
        filtrarTabelaAgendamentos();
    });

    // Função para filtrar a tabela de agendamentos atrasados
    function filtrarTabelaAtrasados() {
        try {
            var nome = $("#filtroNomeAtrasados").val().toLowerCase();
            var cpf = $("#filtroCPFAtrasados").val().toLowerCase();
            var atendente = $("#filtroAtendenteAtrasados").val().toLowerCase();
            var loja = $("#filtroLojaAtrasados").val().toLowerCase();

            console.log('Iniciando filtragem com os valores:', {
                nome: nome,
                cpf: cpf, 
                atendente: atendente,
                loja: loja
            });

            $("#tabelaAgendamentosAtrasados tr.linha-agendamento-atrasado").each(function() {
                var row = $(this);
                var nomeCliente = row.find("button").text().toLowerCase();
                var cpfCliente = row.find("td:nth-child(2)").text().toLowerCase();
                var atendenteTexto = row.find("td:nth-child(5)").text().toLowerCase();
                var lojaTexto = row.find("td:nth-child(6)").text().toLowerCase();

                var matchNome = nomeCliente.includes(nome);
                var matchCPF = cpfCliente.includes(cpf);
                var matchAtendente = atendenteTexto.includes(atendente);
                var matchLoja = lojaTexto.includes(loja);

                if (matchNome && matchCPF && matchAtendente && matchLoja) {
                    row.show();
                } else {
                    row.hide();
                }
            });

            var temResultados = $("#tabelaAgendamentosAtrasados tr.linha-agendamento-atrasado:visible").length > 0;
            $("#nenhumResultadoAtrasados").toggle(!temResultados);

            console.log('Filtragem concluída com sucesso. Registros visíveis:', 
                $("#tabelaAgendamentosAtrasados tr.linha-agendamento-atrasado:visible").length);

        } catch (error) {
            console.error('Erro ao filtrar tabela de atrasados:', error);
        }
    }

    // Event listeners para agendamentos atrasados
    $("#filtroNomeAtrasados, #filtroCPFAtrasados, #filtroAtendenteAtrasados, #filtroLojaAtrasados").on("keyup change", filtrarTabelaAtrasados);

    // Limpar filtros ao fechar modal de atrasados
    $("#modalAgendamentosAtrasados").on("hidden.bs.modal", function() {
        $("#filtroNomeAtrasados, #filtroCPFAtrasados, #filtroAtendenteAtrasados, #filtroLojaAtrasados").val("");
        filtrarTabelaAtrasados();
    });

    // Função para filtrar a tabela de clientes
    function filtrarTabelaClientes() {
        var nome = $("#filtroNomeClientes").val().toLowerCase();
        var cpf = $("#filtroCPFClientes").val().toLowerCase();
        var atendente = $("#filtroAtendenteClientes").val().toLowerCase();
        var loja = $("#filtroLojaClientes").val().toLowerCase();

        $("#tabelaClientesLoja tr.linha-cliente-loja").each(function() {
            var row = $(this);
            var nomeCliente = row.find("button").text().toLowerCase();
            var cpfCliente = row.find("td:nth-child(2)").text().toLowerCase();
            var atendenteTexto = row.find("td:nth-child(5)").text().toLowerCase();
            var lojaTexto = row.find("td:nth-child(6)").text().toLowerCase();

            var matchNome = nomeCliente.includes(nome);
            var matchCPF = cpfCliente.includes(cpf);
            var matchAtendente = atendenteTexto.includes(atendente);
            var matchLoja = lojaTexto.includes(loja);

            if (matchNome && matchCPF && matchAtendente && matchLoja) {
                row.show();
            } else {
                row.hide();
            }
        });

        var temResultados = $("#tabelaClientesLoja tr.linha-cliente-loja:visible").length > 0;
        $("#nenhumResultadoClientes").toggle(!temResultados);
    }

    // Event listeners para filtros de clientes
    $("#filtroNomeClientes, #filtroCPFClientes, #filtroAtendenteClientes, #filtroLojaClientes").on("keyup change", filtrarTabelaClientes);

    // Limpar filtros ao fechar modal
    $("#modalListaClientes").on("hidden.bs.modal", function() {
        $("#filtroNomeClientes, #filtroCPFClientes, #filtroAtendenteClientes, #filtroLojaClientes").val("");
        filtrarTabelaClientes();
    });

    // Adicione um listener para limpar os filtros de data ao fechar o modal
    $("#modalAgendamentosTAC").on("hidden.bs.modal", function() {
        $("#filtroNomeTAC, #filtroCPFTAC, #filtroLojaTAC, #filtroStatusTAC, #filtroPeriodoTAC, #filtroDataEspecificaTAC").val("");
        filtrarTabelaTAC();
    });
});