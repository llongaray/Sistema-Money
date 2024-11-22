import { Agendamento, ClienteLoja, TipoModal } from './types';

/**
 * Gerenciador de modais do sistema
 * @class ModalManager
 */
export class ModalManager {
    private todosAgendamentos: Agendamento[];
    private vendedoresListaClientes: Record<string, { id: string; nome: string }>;

    /**
     * Inicializa o gerenciador de modais
     * @param {Agendamento[]} agendamentos - Lista de agendamentos
     * @param {Record<string, any>} vendedores - Lista de vendedores
     */
    constructor(agendamentos: Agendamento[], vendedores: Record<string, any>) {
        this.todosAgendamentos = agendamentos;
        this.vendedoresListaClientes = vendedores;
        this.initializeEventListeners();
    }

    /**
     * Preenche dados em um sub-modal
     * @param {HTMLElement} subModal - Elemento do sub-modal
     * @param {TipoModal} tipoModal - Tipo do modal
     * @param {string} id - ID do agendamento
     */
    private preencherDadosSubModal(
        subModal: HTMLElement,
        tipoModal: TipoModal,
        id: string
    ): void {
        console.log('Iniciando preenchimento do sub-modal para ID:', id);

        if (tipoModal === 'listaClientes') {
            this.preencherModalListaClientes(subModal, id);
        } else if (tipoModal === 'confirmacao') {
            this.preencherModalConfirmacao(subModal, id);
        }
    }

    /**
     * Preenche modal de lista de clientes
     * @private
     */
    private preencherModalListaClientes(subModal: HTMLElement, id: string): void {
        const dados = this.todosAgendamentos.find(
            (agendamento) => String(agendamento.id) === id
        );

        if (!dados) {
            console.error(`ID ${id} não encontrado`);
            return;
        }

        try {
            const campos: Record<string, string> = {
                '#nomeCliente': dados.nome_cliente,
                '#cpfCliente': dados.cpf_cliente,
                '#numeroCliente': dados.numero_cliente,
                '#diaAgendado': dados.dia_agendado,
                '#tabulacaoAtendente': dados.tabulacao_atendente,
                '#atendenteAgendou': dados.atendente_nome,
                '#lojaAgendada': dados.loja_nome,
                '#agendamentoId': dados.id,
            };

            this.preencherCampos(subModal, campos);
        } catch (error) {
            console.error('Erro ao preencher campos:', error);
        }
    }

    /**
     * Converte dados para formato cliente loja
     * @private
     */
    private converterParaFormatoClienteLoja(agendamento: Agendamento): ClienteLoja {
        return {
            id: agendamento.id,
            nome: agendamento.nome_cliente,
            cpf: agendamento.cpf_cliente,
            numero: agendamento.numero_cliente,
            diaAgendado: agendamento.dia_agendado,
            tabulacaoAtendente: agendamento.tabulacao_atendente,
            atendenteAgendou: agendamento.atendente_nome,
            lojaAgendada: agendamento.loja_nome,
        };
    }

    /**
     * Inicializa os event listeners
     * @private
     */
    private initializeEventListeners(): void {
        document.addEventListener('DOMContentLoaded', () => {
            this.setupModalListeners();
            this.setupFormListeners();
            this.setupKeyboardListeners();
            this.handleUrlParams();
        });
    }

    /**
     * Fecha um sub-modal específico
     * @param {string} modalId - ID do modal a ser fechado
     */
    public closeSubModal(modalId: string): void {
        const cleanedModalId = modalId.replace('#', '');
        const modal = document.getElementById(cleanedModalId);

        if (modal?.classList.contains('modal-sec')) {
            modal.classList.remove('active');
            console.log(`Sub-modal ${cleanedModalId} fechado com sucesso`);
        } else {
            console.error(`Sub-modal ${cleanedModalId} não encontrado`);
        }
    }
} 