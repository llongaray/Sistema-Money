function preencherTabelaAtrasados() {
    console.log('Iniciando preenchimento da tabela de atrasados');
    
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

function filtrarTabelaTAC() {
    var nome = $("#filtroNomeTAC").val().toLowerCase();
    var cpf = $("#filtroCPFTAC").val().toLowerCase();
    var status = $("#filtroStatusTAC").val().toLowerCase();

    $("#modalAgendamentosTAC .tac-row").each(function() {
        var row = $(this);
        var nomeCliente = row.find(".td-nome").text().toLowerCase();
        var cpfCliente = row.find(".td-cpf").text().toLowerCase();
        var statusCliente = row.find(".td-status .status-badge").text().toLowerCase();

        var matchNome = nomeCliente.includes(nome);
        var matchCPF = cpfCliente.includes(cpf);
        var matchStatus = status === "" || statusCliente === status;

        if (matchNome && matchCPF && matchStatus) {
            row.show();
        } else {
            row.hide();
        }
    });
}

// Event listeners
$(document).ready(function() {
    // Event listeners para todos os agendamentos
    $("#modalTodosAgendamentos #filtroNome, #modalTodosAgendamentos #filtroCPF, #modalTodosAgendamentos #filtroAtendente, #modalTodosAgendamentos #filtroLoja").on("keyup change", filtrarTabelaTodosAgendamentos);
    $("#modalTodosAgendamentos #filtroData").on("change", filtrarTabelaTodosAgendamentos);

    // Event listeners para agendamentos
    $("#filtroNome, #filtroAtendente, #filtroLoja, #filtroStatus").on("keyup change", filtrarTabelaAgendamentos);
    $("#filtroDia").on("change", filtrarTabelaAgendamentos);

    // Event listeners para TAC
    $("#filtroNomeTAC, #filtroCPFTAC, #filtroStatusTAC").on("keyup change", filtrarTabelaTAC);

    // Limpar filtros ao fechar modais
    $("#modalTodosAgendamentos").on("hidden.bs.modal", function() {
        $("#modalTodosAgendamentos #filtroNome, #modalTodosAgendamentos #filtroCPF, #modalTodosAgendamentos #filtroData, #modalTodosAgendamentos #filtroAtendente, #modalTodosAgendamentos #filtroLoja").val("");
        filtrarTabelaTodosAgendamentos();
    });

    $("#modalConfiAgendamentoTabela").on("hidden.bs.modal", function() {
        $("#filtroNome, #filtroDia, #filtroAtendente, #filtroLoja, #filtroStatus").val("");
        filtrarTabelaAgendamentos();
    });
});
