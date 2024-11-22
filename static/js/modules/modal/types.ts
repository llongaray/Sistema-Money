// Definição dos tipos
export interface Agendamento {
    id: string;
    nome_cliente: string;
    cpf_cliente: string;
    numero_cliente: string;
    dia_agendado: string;
    tabulacao_atendente: string;
    atendente_nome: string;
    loja_nome: string;
}

export interface ClienteLoja {
    id: string;
    nome: string;
    cpf: string;
    numero: string;
    diaAgendado: string;
    diaAgendadoFormatado?: string;
    tabulacaoAtendente: string;
    atendenteAgendou: string;
    lojaAgendada: string;
}

export type TipoModal = 'listaClientes' | 'confirmacao'; 