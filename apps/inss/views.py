# Importações da biblioteca padrão Python
import os
import json
from datetime import datetime, date, time

# Importações padrão do Django
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.db.models import Count, F, Max, Q, Sum
from django.db.models.functions import Coalesce, TruncDate
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from datetime import timedelta

# Local imports
from custom_tags_app.permissions import check_access
from setup.utils import verificar_autenticacao

# Importações de modelos
from .models import *
from apps.funcionarios.models import *
from apps.siape.models import *

# Importações de formulários
from .forms import *

# Importações de pytz
import pytz

# Função auxiliar para obter a data/hora atual em SP
def get_current_sp_time():
    """Retorna a data/hora atual no fuso horário de São Paulo"""
    sp_timezone = pytz.timezone('America/Sao_Paulo')
    return timezone.localtime(timezone.now(), sp_timezone)

def make_aware_sp(naive_datetime):
    """Converte uma data/hora ingênua para o fuso horário de São Paulo"""
    sp_timezone = pytz.timezone('America/Sao_Paulo')
    if timezone.is_aware(naive_datetime):
        return naive_datetime.astimezone(sp_timezone)
    return timezone.make_aware(naive_datetime, sp_timezone)

def calcular_status_dias(agendamento, hoje):
    """Calcula o status baseado nos dias entre hoje e o agendamento"""
    
    # Verifica se é um dicionário ou objeto Agendamento
    if isinstance(agendamento, dict):
        tabulacao_vendedor = agendamento.get('tabulacao_vendedor')
        dia_agendado = agendamento.get('dia_agendado')
    else:
        tabulacao_vendedor = agendamento.tabulacao_vendedor
        dia_agendado = agendamento.dia_agendado

    # Verifica se já tem tabulação do vendedor
    if tabulacao_vendedor:
        return 'FINALIZADO'

    # Converte a data do agendamento para date se for string
    if isinstance(dia_agendado, str):
        dia_agendado = datetime.strptime(dia_agendado, '%Y-%m-%d %H:%M:%S').date()
    elif isinstance(dia_agendado, datetime):
        dia_agendado = dia_agendado.date()

    # Calcula a diferença de dias
    dias_diferenca = (dia_agendado - hoje).days

    # Retorna o status baseado na diferença de dias
    if dias_diferenca > 0:
        return 'FUTURO'
    elif dias_diferenca == 0:
        return 'HOJE'
    else:
        return 'ATRASADO'
    

def post_status_tac(status_data, funcionario_logado):
    """
    Processa a atualização do status do TAC e registra/remove o valor quando necessário
    """
    print("\n----- Iniciando post_status_tac -----\n")
    print(f"Dados recebidos: {status_data}")

    try:
        # Busca o agendamento
        agendamento = Agendamento.objects.get(id=status_data['agendamento_id'])
        status_anterior = agendamento.status_tac
        novo_status = status_data['status']
        
        data_atual = get_current_sp_time()
        
        # Se está mudando para PAGO
        if novo_status == 'PAGO':
            # Busca registro existente com mesmo funcionário, CPF e valor
            registro_existente = RegisterMoney.objects.filter(
                funcionario=agendamento.vendedor_loja,
                cpf_cliente=agendamento.cpf_cliente,
                valor_est=float(agendamento.tac) if agendamento.tac else None,
                status=True
            ).first()
            
            if registro_existente:
                # Atualiza o registro existente
                registro_existente.loja = agendamento.loja_agendada
                registro_existente.data = timezone.now()
                registro_existente.save()
                
                print(f"Registro de TAC atualizado para funcionário {agendamento.vendedor_loja.nome if agendamento.vendedor_loja else 'N/A'}")
                
            else:
                # Cria novo registro
                if agendamento.tac and agendamento.vendedor_loja:
                    RegisterMoney.objects.create(
                        funcionario=agendamento.vendedor_loja,
                        loja=agendamento.loja_agendada,
                        cpf_cliente=agendamento.cpf_cliente,
                        valor_est=float(agendamento.tac),
                        status=True,
                        data=timezone.now()
                    )
                    print(f"Novo registro de TAC criado para {agendamento.vendedor_loja.nome if agendamento.vendedor_loja else 'N/A'}")
                else:
                    print("Agendamento sem TAC ou vendedor definido")

            # Atualiza data de pagamento
            agendamento.data_pagamento_tac = data_atual
            
        # Atualiza o status do TAC
        agendamento.status_tac = novo_status
        if novo_status != 'PAGO':
            agendamento.data_pagamento_tac = None
        agendamento.save()

        # Registra o log de alteração de status
        LogAlteracao.objects.create(
            agendamento_id=str(agendamento.id),
            mensagem=f"Status do TAC atualizado de {status_anterior} para {novo_status}",
            status=True,
            funcionario=funcionario_logado
        )

        print("\n----- Finalizando post_status_tac -----\n")
        return {
            'texto': 'Status do TAC atualizado com sucesso!',
            'classe': 'success'
        }

    except Agendamento.DoesNotExist:
        print("Erro: Agendamento não encontrado")
        return {
            'texto': 'Erro: Agendamento não encontrado',
            'classe': 'error'
        }
    except Exception as e:
        print(f"Erro ao processar status TAC: {str(e)}")
        return {
            'texto': f'Erro ao atualizar status: {str(e)}',
            'classe': 'error'
        }

# Funções auxiliares e de processamento
def post_venda_tabulacao(form_data, funcionario):
    print("\n\n----- Iniciando post_venda_tabulacao -----\n")
    mensagem = {'texto': '', 'classe': ''}

    try:
        # Extraindo dados do formulário
        tabulacao_data = {
            'agendamento_id': form_data.get('agendamento_id'),
            'vendedor_id': form_data.get('vendedor_id'),
            'tabulacao_vendedor': form_data.get('tabulacao_vendedor'),
            'observacao_vendedor': form_data.get('observacao_vendedor'),
            'nome_cliente': form_data.get('nome_cliente'),
        }

        # Dados específicos para FECHOU NEGOCIO
        if tabulacao_data['tabulacao_vendedor'] == 'FECHOU NEGOCIO':
            tabulacao_data.update({
                'tipo_negociacao': form_data.get('tipo_negociacao'),
                'banco': form_data.get('banco'),
                'subsidio': form_data.get('subsidio'),
                'tac': form_data.get('tac'),
                'acao': form_data.get('acao'),
                'associacao': form_data.get('associacao'),
                'aumento': form_data.get('aumento')
            })

        # Validações dos campos obrigatórios para FECHOU NEGOCIO
        if tabulacao_data['tabulacao_vendedor'] == 'FECHOU NEGOCIO':
            campos_obrigatorios = [
                'tipo_negociacao', 'banco', 'subsidio', 'tac', 
                'acao', 'associacao', 'aumento'
            ]
            campos_faltantes = [campo for campo in campos_obrigatorios 
                              if not tabulacao_data.get(campo)]
            
            if campos_faltantes:
                mensagem = {
                    'texto': f'Campos obrigatórios não preenchidos: {", ".join(campos_faltantes)}',
                    'classe': 'error'
                }
                return mensagem

        # Obtém e atualiza o agendamento
        agendamento = Agendamento.objects.get(id=tabulacao_data['agendamento_id'])
        vendedor_loja = Funcionario.objects.get(id=tabulacao_data['vendedor_id'])

        # Atualiza campos básicos
        agendamento.vendedor_loja = vendedor_loja
        agendamento.tabulacao_vendedor = tabulacao_data['tabulacao_vendedor']
        agendamento.observacao_vendedor = tabulacao_data.get('observacao_vendedor')
        # Define tabulacao_atendente como CONFIRMADO
        agendamento.tabulacao_atendente = 'CONFIRMADO'

        # Atualiza campos específicos se FECHOU NEGOCIO
        if tabulacao_data['tabulacao_vendedor'] == 'FECHOU NEGOCIO':
            agendamento.tipo_negociacao = tabulacao_data['tipo_negociacao'].upper()
            agendamento.banco = tabulacao_data['banco'].upper()
            agendamento.subsidio = tabulacao_data['subsidio']
            # Converte o valor TAC para decimal
            tac_valor = tabulacao_data['tac'].replace('R$', '').replace('.', '').replace(',', '.')
            agendamento.tac = Decimal(tac_valor)
            agendamento.acao = tabulacao_data['acao']
            agendamento.associacao = tabulacao_data['associacao']
            agendamento.aumento = tabulacao_data['aumento']

        agendamento.save()

        # Criar log de alteração
        log_mensagem = (f"Tabulação de vendas atualizada. "
                       f"Vendedor: {vendedor_loja.nome}, "
                       f"Tabulação: {tabulacao_data['tabulacao_vendedor']}, "
                       f"Tabulação Atendente atualizada para: CONFIRMADO")
        
        if tabulacao_data['tabulacao_vendedor'] == 'FECHOU NEGOCIO':
            log_mensagem += (f". Negócio: {tabulacao_data['tipo_negociacao']}, "
                           f"Banco: {tabulacao_data['banco']}, "
                           f"TAC: R$ {tabulacao_data['tac']}")

        LogAlteracao.objects.create(
            agendamento_id=str(agendamento.id),
            mensagem=log_mensagem,
            status=True,
            funcionario=funcionario
        )

        mensagem['texto'] = 'Tabulação de vendas atualizada com sucesso!'
        mensagem['classe'] = 'success'

    except Exception as e:
        mensagem['texto'] = f'Erro ao atualizar a tabulação: {str(e)}'
        mensagem['classe'] = 'error'
        print(f"Erro: {str(e)}")
        LogAlteracao.objects.create(
            agendamento_id=str(tabulacao_data.get('agendamento_id', 'N/A')),
            mensagem=f"Erro ao atualizar tabulação de vendas: {str(e)}",
            status=False,
            funcionario=funcionario
        )

    return mensagem

def post_cliente_rua(request, funcionario_logado):
    """
    Processa o POST de um cliente rua, criando um novo agendamento.
    """
    print("\n----- Iniciando post_cliente_rua -----")
    
    try:
        # Coleta e valida dados básicos obrigatórios
        dados_basicos = {
            'nome_cliente': request.POST.get('nome_cliente', '').strip(),
            'cpf_cliente': request.POST.get('cpf_cliente', '').strip(),
            'numero_cliente': request.POST.get('numero_cliente', '').strip(),
            'data_comparecimento': request.POST.get('data_comparecimento')
        }
        
        # Verifica campos obrigatórios
        if not all(dados_basicos.values()):
            return {
                'texto': 'Nome, CPF, número de celular e data são campos obrigatórios.',
                'classe': 'error'
            }
        
        # Coleta dados do atendimento
        dados_atendimento = {
            'loja_id': request.POST.get('loja'),
            'vendedor_id': request.POST.get('vendedor_id'),
            'tabulacao_vendedor': request.POST.get('tabulacao_vendedor'),
            'observacao_vendedor': request.POST.get('observacao_vendedor', '')
        }
        
        # Cria o agendamento base
        agendamento = Agendamento.objects.create(
            nome_cliente=dados_basicos['nome_cliente'],
            cpf_cliente=dados_basicos['cpf_cliente'],
            numero_cliente=dados_basicos['numero_cliente'],
            dia_agendado=dados_basicos['data_comparecimento'],
            loja_agendada_id=dados_atendimento['loja_id'],
            vendedor_loja_id=dados_atendimento['vendedor_id'],
            tabulacao_vendedor=dados_atendimento['tabulacao_vendedor'],
            observacao_vendedor=dados_atendimento['observacao_vendedor'],
            cliente_rua=True
        )
        
        # Se for FECHOU NEGOCIO, processa dados adicionais
        if dados_atendimento['tabulacao_vendedor'] == 'FECHOU NEGOCIO':
            dados_negocio = {
                'tipo_negociacao': request.POST.get('tipo_negociacao', '').strip(),
                'banco': request.POST.get('banco', '').strip(),
                'subsidio': request.POST.get('subsidio'),
                'valor_tac': request.POST.get('valor_tac', '').strip(),
                'acao': request.POST.get('acao'),
                'associacao': request.POST.get('associacao'),
                'aumento': request.POST.get('aumento')
            }
            
            # Atualiza o agendamento com os dados de negócio
            agendamento.tipo_negociacao = dados_negocio['tipo_negociacao']
            agendamento.banco = dados_negocio['banco']
            agendamento.subsidio = dados_negocio['subsidio']
            
            # Processa o valor TAC se existir
            if dados_negocio['valor_tac']:
                valor_tac = dados_negocio['valor_tac'].replace('R$', '').replace('.', '').replace(',', '.').strip()
                agendamento.tac = Decimal(valor_tac)
            
            agendamento.acao = dados_negocio['acao']
            agendamento.associacao = dados_negocio['associacao']
            agendamento.aumento = dados_negocio['aumento']
            agendamento.save()
        
        # Registra o log
        LogAlteracao.objects.create(
            agendamento_id=str(agendamento.id),
            mensagem=f"Cliente Rua registrado - Tabulação: {dados_atendimento['tabulacao_vendedor']}",
            status=True,
            funcionario=funcionario_logado
        )
        
        print(f"Cliente Rua registrado com sucesso - ID: {agendamento.id}")
        return {
            'texto': 'Cliente Rua registrado com sucesso!',
            'classe': 'success'
        }
        
    except Exception as e:
        print(f"Erro ao registrar Cliente Rua: {str(e)}")
        return {
            'texto': f'Erro ao registrar Cliente Rua: {str(e)}',
            'classe': 'error'
        }
    finally:
        print("----- Finalizando post_cliente_rua -----\n")

def post_confirmacao_agem(form_data, funcionario):
    print("\n\n----- Iniciando post_confirmacao_agem -----\n")
    print(f"Dados do formulário recebidos: {form_data}")
    mensagem = {'texto': '', 'classe': ''}
    try:
        agendamento_id = form_data.get('agendamento_id')
        print(f"ID do agendamento recebido: {agendamento_id}")
        
        if not agendamento_id:
            print("ERRO: ID do agendamento não fornecido ou vazio")
            raise ValueError("ID do agendamento não fornecido")
            
        # Tenta converter para int para garantir que é um ID válido
        agendamento_id = int(agendamento_id)
        print(f"ID do agendamento convertido: {agendamento_id}")
        
        agendamento = Agendamento.objects.get(id=agendamento_id)
        print(f"Agendamento encontrado: {agendamento}")
        
        # Criar um dicionário com os dados do formulário
        dados_atualizacao = {
            'nome_cliente': form_data['nome_cliente'],
            'numero_cliente': form_data['numero_cliente'],
            'tabulacao_atendente': form_data['tabulacao_atendente']
        }
        
        # Converter e adicionar a data agendada
        if form_data['dia_agendado']:
            dia_agendado = datetime.strptime(form_data['dia_agendado'], '%Y-%m-%d').date()
            hora_atual = get_current_sp_time().time()
            dados_atualizacao['dia_agendado'] = make_aware_sp(
                datetime.combine(dia_agendado, hora_atual)
            )
        
        # Verifica o status do agendamento
        if form_data['tabulacao_atendente'] == 'CONFIRMADO':
            # Apenas atualiza a tabulação
            dados_atualizacao['tabulacao_atendente'] = 'CONFIRMADO'
        
        elif form_data['tabulacao_atendente'] == 'REAGENDADO':
            # Atualiza a tabulação e a nova data
            dados_atualizacao['tabulacao_atendente'] = 'REAGENDADO'
            if form_data.get('nova_dia_agendado'):
                nova_dia_agendado = datetime.strptime(form_data['nova_dia_agendado'], '%Y-%m-%d').date()
                hora_atual = get_current_sp_time().time()
                dados_atualizacao['dia_agendado'] = make_aware_sp(
                    datetime.combine(nova_dia_agendado, hora_atual)
                )
        
        elif form_data['tabulacao_atendente'] == 'DESISTIU':
            # Atualiza a tabulação e a observação
            dados_atualizacao['tabulacao_atendente'] = 'DESISTIU'
            dados_atualizacao['observacao_atendente'] = form_data.get('observacao', '')
        
        # Atualiza o agendamento com os novos dados
        for key, value in dados_atualizacao.items():
            setattr(agendamento, key, value)
        agendamento.save()
        
        mensagem = {
            'texto': 'Agendamento atualizado com sucesso!',
            'classe': 'success'
        }
        print("Agendamento atualizado com sucesso")
        
    except ValueError as e:
        print(f"ERRO de validação: {str(e)}")
        mensagem = {
            'texto': f'Erro de validação: {str(e)}',
            'classe': 'error'
        }
    except Agendamento.DoesNotExist:
        print("ERRO: Agendamento não encontrado")
        mensagem = {
            'texto': 'Agendamento não encontrado',
            'classe': 'error'
        }
    except Exception as e:
        print(f"ERRO inesperado: {str(e)}")
        mensagem = {
            'texto': f'Erro ao processar agendamento: {str(e)}',
            'classe': 'error'
        }
    
    print(f"Mensagem retornada: {mensagem}")
    print("\n----- Finalizando post_confirmacao_agem -----\n")
    return mensagem

def post_agendamento(request, funcionario):
    '''Processa o agendamento baseado nos dados recebidos.'''
    print("\n\n----- Iniciando post_agendamento -----\n")
    print(f'\n\n ------------------------POST Agendamento ABERTO!!------------------------\n\n')
    mensagem = {'texto': '', 'classe': ''}

    try:
        dia_agendado = request.POST.get('dia_agendado')
        print(f"Data recebida: {dia_agendado}")

        # Converter a data para datetime e adicionar a hora atual
        if isinstance(dia_agendado, str):
            dia_agendado = datetime.strptime(dia_agendado, '%Y-%m-%d').date()
        
        hora_atual = get_current_sp_time().time()
        dia_agendado_com_hora = make_aware_sp(datetime.combine(dia_agendado, hora_atual))

        agendamento_data = {
            'nome_cliente': request.POST.get('nome_cliente'),
            'cpf_cliente': request.POST.get('cpf_cliente'),
            'numero_cliente': request.POST.get('numero_cliente'),
            'dia_agendado': dia_agendado_com_hora,
            'loja_agendada_id': request.POST.get('loja_agendada'),
            'atendente_agendou_id': request.POST.get('atendente_agendou')
        }

        print(f"Dados do agendamento: {agendamento_data}")

        # Criando e salvando o novo agendamento
        agendamento = Agendamento(**agendamento_data)
        agendamento.save()

        # Criar log de alteração
        LogAlteracao.objects.create(
            agendamento_id=str(agendamento.id),
            mensagem=f"Novo agendamento criado para {agendamento_data['nome_cliente']} na data {agendamento_data['dia_agendado']}",
            status=True,
            funcionario=funcionario
        )

        mensagem['texto'] = 'Agendamento processado com sucesso!'
        mensagem['classe'] = 'success'

    except ValueError as ve:
        mensagem['texto'] = str(ve)
        mensagem['classe'] = 'error'
        # Criar log de erro
        LogAlteracao.objects.create(
            agendamento_id="N/A",
            mensagem=f"Erro ao processar agendamento: {str(ve)}",
            status=False,
            funcionario=funcionario
        )
    except Exception as e:
        mensagem['texto'] = f'Erro ao processar agendamento: {str(e)}'
        mensagem['classe'] = 'error'
        # Criar log de erro
        LogAlteracao.objects.create(
            agendamento_id="N/A",
            mensagem=f"Erro ao processar agendamento: {str(e)}",
            status=False,
            funcionario=funcionario
        )

    print(f"Mensagem final: {mensagem}")
    print("\n----- Finalizando post_agendamento -----\n")
    return mensagem

def post_tac(request, funcionario_logado):
    """Atualiza o status do agendamento e registra o valor em RegisterMoney."""
    agendamento_id = request.POST.get('agendamento_id')
    novo_status = request.POST.get('status_tac')

    print(f"Atualizando status TAC para o agendamento ID: {agendamento_id} com o novo status: {novo_status}")

    # Obtém o agendamento correspondente
    agendamento = get_object_or_404(Agendamento, id=agendamento_id)
    print(f"Agendamento encontrado: {agendamento}")

    # Atualiza o status do agendamento
    agendamento.status_tac = novo_status
    agendamento.save()
    print(f"Status TAC do agendamento ID: {agendamento_id} atualizado para: {novo_status}")

    # Adiciona um registro em RegisterMoney se o novo_status for 'PAGO'
    if novo_status == 'PAGO':
        # Usa o valor do campo 'tac' do agendamento
        valor_tac = agendamento.tac  # Supondo que tac é o valor que você quer registrar
        if valor_tac is not None:  # Verifica se o valor do tac não é None
            RegisterMoney.objects.create(
                funcionario=agendamento.vendedor_loja,  # Usa o vendedor_loja do agendamento
                cpf_cliente=agendamento.cpf_cliente,  # Passa o CPF do cliente
                valor_est=valor_tac,  # Usa o valor do tac
                status=True,  # Define o status como True
                data=timezone.now()  # Data atual
            )
            print(f"Registro em RegisterMoney criado para o funcionário: {agendamento.vendedor_loja} com valor TAC: {valor_tac}")
        else:
            print("Erro: O valor do TAC está vazio ou não é válido.")
    else:
        print("O status TAC não é 'PAGO', portanto, não será criado um registro em RegisterMoney.")

    return {
        'texto': 'Status TAC atualizado com sucesso!',
        'classe': 'success'
    }



''' ESSA PARTE É SÓ PARA O FORMS INSS, OS DICIONARIOS E DADOS NECESSARIO PARA OS FORM FUNCIONARIO '''


def get_all_agendamentos(agendamentos_base_query, funcionario_logado, nivel_cargo):
    """Obtém todos os agendamentos e seus detalhes."""
    # 1. Todos Agendamentos
    todos_agendamentos = agendamentos_base_query.all().order_by('cpf_cliente', '-dia_agendado')
    todos_agendamentos_dict = [{
        'id': a.id,
        'nome_cliente': a.nome_cliente,
        'cpf_cliente': a.cpf_cliente,
        'numero_cliente': a.numero_cliente,
        'dia_agendado': a.dia_agendado.strftime('%Y-%m-%d'),  # Formato para input date
        'atendente_agendou': a.atendente_agendou.nome.split()[0] if a.atendente_agendou else '',  # Primeiro nome do atendente
        'loja_agendada': (
                a.loja_agendada.nome.split(' - ')[-1] 
                if a.loja_agendada and a.loja_agendada.nome and ' - ' in a.loja_agendada.nome 
                else (a.loja_agendada.nome if a.loja_agendada else '')
            ),
        'tabulacao_atendente': a.tabulacao_atendente,
        'tabulacao_vendedor': a.tabulacao_vendedor,
        'observacao_vendedor': a.observacao_vendedor,
        'observacao_atendente': a.observacao_atendente,
        'tipo_negociacao': a.tipo_negociacao,
        'banco': a.banco,
        'subsidio': a.subsidio,
        'tac': a.tac,
        'acao': a.acao,
        'associacao': a.associacao,
        'aumento': a.aumento,
        'status_tac': a.status_tac,
        'data_pagamento_tac': a.data_pagamento_tac,
        'status': calcular_status_dias(a, timezone.now().date())  # Chama a funço para calcular o status
    } for a in todos_agendamentos]

    # 2. Novo dicionário específico para a tabela
    # Primeiro, agrupa por CPF e pega apenas o mais recente
    agendamentos_por_cpf = {}
    for a in todos_agendamentos:
        if a.cpf_cliente not in agendamentos_por_cpf or a.dia_agendado > agendamentos_por_cpf[a.cpf_cliente].dia_agendado:
            agendamentos_por_cpf[a.cpf_cliente] = a

    # Cria o dicionário para a tabela com apenas os agendamentos mais recentes
    todos_agend_table_dict = []
    for cpf, agendamento in agendamentos_por_cpf.items():
        # Conta total de agendamentos para este CPF
        total_agendamentos = sum(1 for a in todos_agendamentos if a.cpf_cliente == cpf)
        
        # Extrai o nome da loja após o ' - '
        loja_nome = (agendamento.loja_agendada.nome.split(' - ')[-1] 
                    if agendamento.loja_agendada and 
                       agendamento.loja_agendada.nome and 
                       ' - ' in agendamento.loja_agendada.nome 
                    else (agendamento.loja_agendada.nome if agendamento.loja_agendada else ''))

        # Pega apenas o primeiro nome do atendente
        atendente_nome = (agendamento.atendente_agendou.nome.split()[0] 
                         if agendamento.atendente_agendou else '')

        todos_agend_table_dict.append({
            'id': agendamento.id,
            'nome_cliente': agendamento.nome_cliente,
            'cpf_cliente': agendamento.cpf_cliente,
            'numero_cliente': agendamento.numero_cliente,
            'dia_agendado': agendamento.dia_agendado.strftime('%Y-%m-%d'),
            'atendente_agendou': atendente_nome,
            'loja_agendada': loja_nome,
            'status': calcular_status_dias(agendamento, timezone.now().date()),
            'total_agendamentos': total_agendamentos
        })

    # Ordena o dicionário final por data de agendamento (mais recente primeiro)
    todos_agend_table_dict.sort(key=lambda x: x['dia_agendado'], reverse=True)

    # Filtra lojas baseado no nível de acesso
    if nivel_cargo in ['ESTAGIO', 'PADRÃO', 'GERENTE']:
        lojas = Loja.objects.filter(id=funcionario_logado.loja.id)
    else:
        lojas = Loja.objects.all()

    lojas_dict = {
        loja.id: {
            'id': loja.id,
            'nome': loja.nome
        }
        for loja in lojas
    }
    print(f"Lojas disponíveis: {lojas_dict}")

    # Filtra funcionários baseado no nível de acesso
    if nivel_cargo in ['ESTAGIO', 'PADRÃO']:
        funcionarios = Funcionario.objects.filter(id=funcionario_logado.id)
    elif nivel_cargo == 'GERENTE':
        funcionarios = Funcionario.objects.filter(loja=funcionario_logado.loja)
    else:
        funcionarios = Funcionario.objects.all()

    # Cria dicionário base de funcionários
    funcionarios_dict = {
        funcionario.id: {
            'id': funcionario.id,
            'nome': funcionario.nome,
            'loja': funcionario.loja.nome if funcionario.loja else 'Sem loja'
        }
        for funcionario in funcionarios
    }

    # Usa o mesmo dicionário para vendedores e atendentes
    vendedores_lista_clientes = funcionarios_dict.copy()
    atendentes_dict = funcionarios_dict.copy()

    print(f"Vendedores disponíveis: {vendedores_lista_clientes}")
    print(f"Atendentes disponíveis: {atendentes_dict}")

    return todos_agendamentos_dict, todos_agend_table_dict, lojas_dict, vendedores_lista_clientes, atendentes_dict

def get_agendamentos_agendados(agendamentos_base_query, funcionario_logado, nivel_cargo):
    """Obtém todos os agendamentos com a tabulação 'AGENDADO'."""
    if nivel_cargo == 'TOTAL':
        agendamentos_agendados = agendamentos_base_query.filter(tabulacao_atendente='AGENDADO').order_by('dia_agendado')
    elif nivel_cargo in ['ESTAGIO', 'PADRÃO']:
        agendamentos_agendados = agendamentos_base_query.filter(tabulacao_atendente='AGENDADO', atendente_agendou=funcionario_logado).order_by('dia_agendado')
    else:
        agendamentos_agendados = agendamentos_base_query.filter(tabulacao_atendente='AGENDADO').order_by('dia_agendado')

    return [{
        'id': a.id,
        'nome_cliente': a.nome_cliente,
        'cpf_cliente': a.cpf_cliente,
        'numero_cliente': a.numero_cliente,
        'dia_agendado': a.dia_agendado.strftime('%Y-%m-%d'),  # Formato para input date
        'atendente_agendou': a.atendente_agendou.nome.split()[0] if a.atendente_agendou else '',  # Primeiro nome do atendente
        'loja_agendada': a.loja_agendada.nome.split(' - ')[-1] if a.loja_agendada and ' - ' in a.loja_agendada.nome else a.loja_agendada.nome,  # Nome da loja após ' - '
        'tabulacao_atendente': a.tabulacao_atendente,
        'tabulacao_vendedor': a.tabulacao_vendedor,
        'status': calcular_status_dias(a, timezone.now().date())  # Chama a função para calcular o status
    } for a in agendamentos_agendados]

def obter_agendamentos_reagendados(agendamentos_base_query, funcionario_logado, nivel_cargo):
    """Obtém todos os agendamentos com a tabulação 'REAGENDADO'."""
    if nivel_cargo == 'TOTAL':
        agendamentos_reagendados = agendamentos_base_query.filter(tabulacao_atendente='REAGENDADO').order_by('dia_agendado')
    elif nivel_cargo in ['ESTAGIO', 'PADRÃO']:
        agendamentos_reagendados = agendamentos_base_query.filter(tabulacao_atendente='REAGENDADO', atendente_agendou=funcionario_logado).order_by('dia_agendado')
    else:
        agendamentos_reagendados = agendamentos_base_query.filter(tabulacao_atendente='REAGENDADO').order_by('dia_agendado')

    return [{
        'id': a.id,
        'nome_cliente': a.nome_cliente,
        'cpf_cliente': a.cpf_cliente,
        'numero_cliente': a.numero_cliente,
        'dia_agendado': a.dia_agendado.strftime('%Y-%m-%d'),  # Formato para input date
        'atendente_agendou': a.atendente_agendou.nome.split()[0] if a.atendente_agendou else '',  # Primeiro nome do atendente
        'loja_agendada': a.loja_agendada.nome.split(' - ')[-1] if a.loja_agendada and ' - ' in a.loja_agendada.nome else a.loja_agendada.nome,  # Nome da loja após ' - '
        'tabulacao_atendente': a.tabulacao_atendente,
        'tabulacao_vendedor': a.tabulacao_vendedor,
        'status': calcular_status_dias(a, timezone.now().date())  # Chama a função para calcular o status
    } for a in agendamentos_reagendados]

def get_agendamentos_confirmados(agendamentos_base_query, funcionario_logado, nivel_cargo, loja_funcionario):
    """Busca os agendamentos que serão mostrados ao vendedor, ou seja, agendamentos confirmados 
    onde o cliente irá comparecer à loja no dia agendado. Estes agendamentos ainda não foram 
    atendidos pelo vendedor (tabulacao_vendedor é nulo) e são apenas os de hoje."""
    
    print("\n----- Iniciando get_agendamentos_confirmados -----")
    print(f"Funcionário logado: {funcionario_logado}")
    print(f"Nível cargo: {nivel_cargo}")
    print(f"Loja funcionário: {loja_funcionario}")

    # Obtém os agendamentos confirmados baseado no nível de acesso
    if funcionario_logado and not funcionario_logado.usuario.is_superuser and nivel_cargo in ['ESTAGIO', 'PADRÃO']:
        agendamentos_confirmados = agendamentos_base_query.filter(
            tabulacao_atendente='CONFIRMADO',
            loja_agendada=loja_funcionario,
            tabulacao_vendedor__isnull=True
        ).order_by('dia_agendado')
        print("Filtrando agendamentos para funcionário padrão/estágio")
    else:
        agendamentos_confirmados = agendamentos_base_query.filter(
            tabulacao_atendente='CONFIRMADO',
            tabulacao_vendedor__isnull=True
        ).order_by('dia_agendado')
        print("Filtrando agendamentos para admin/supervisor")

    print(f"Total de agendamentos confirmados encontrados: {agendamentos_confirmados.count()}")

    # Cria lista com todos os agendamentos confirmados
    hoje = timezone.now().date()
    todos_agendamentos = [{
        'id': a.id,
        'nome_cliente': a.nome_cliente,
        'cpf_cliente': a.cpf_cliente,
        'numero_cliente': a.numero_cliente,
        'dia_agendado': a.dia_agendado.strftime('%Y-%m-%d'),
        'atendente_agendou': a.atendente_agendou.nome.split()[0] if a.atendente_agendou else '',
        'loja_agendada': a.loja_agendada.nome.split(' - ')[-1] if a.loja_agendada and ' - ' in a.loja_agendada.nome else a.loja_agendada.nome,
        'tabulacao_atendente': a.tabulacao_atendente,
        'tabulacao_vendedor': a.tabulacao_vendedor,
        'status': calcular_status_dias(a, hoje)
    } for a in agendamentos_confirmados]

    print(f"Total de agendamentos processados: {len(todos_agendamentos)}")

    # Filtra apenas os agendamentos de hoje
    agendamentos_hoje = [agendamento for agendamento in todos_agendamentos if agendamento['status'] == 'HOJE']
    
    print(f"Total de agendamentos para hoje: {len(agendamentos_hoje)}")
    print("----- Finalizando get_agendamentos_confirmados -----\n")

    return agendamentos_hoje

def get_agendamentos_tac(todos_agendamentos_dict):
    """Função busca agendamentos que tem o campos 'tac' com algum valor, ou seja, agementos que foram feito algum negocio com o cliente"""
    return [
        {
            'cpf_cliente': a['cpf_cliente'],
            'nome_cliente': a['nome_cliente'], 
            'subsidio': a['subsidio'],
            'tac': a['tac'],
            'acao': a['acao'],
            'status': a['status_tac'],
            'agendamento_id': a['id']  # Adiciona o ID do agendamento
        }
        for a in todos_agendamentos_dict if a['tac']  # Verifica se existe valor no campo tac
    ]


def get_agendamentos_atrasados(agendamentos_base_query, funcionario_logado, nivel_cargo, loja_funcionario):
    """Busca os agendamentos que estão atrasados, ou seja, que passaram do dia_agendado
    sem receber uma tabulação do vendedor."""
    hoje = timezone.now().date()
    
    # Filtra agendamentos atrasados baseado no nível de acesso
    if funcionario_logado and not funcionario_logado.usuario.is_superuser and nivel_cargo in ['ESTAGIO', 'PADRÃO']:
        agendamentos_atrasados = agendamentos_base_query.filter(
            dia_agendado__lt=hoje,  # Dia agendado menor que hoje
            tabulacao_vendedor__isnull=True,  # Sem tabulação do vendedor
            loja_agendada=loja_funcionario
        ).order_by('dia_agendado')
    else:
        agendamentos_atrasados = agendamentos_base_query.filter(
            dia_agendado__lt=hoje,  # Dia agendado menor que hoje
            tabulacao_vendedor__isnull=True  # Sem tabulaão do vendedor
        ).order_by('dia_agendado')

    return [{
        'id': a.id,
        'nome_cliente': a.nome_cliente,
        'cpf_cliente': a.cpf_cliente,
        'numero_cliente': a.numero_cliente,
        'dia_agendado': a.dia_agendado.strftime('%Y-%m-%d'),
        'atendente_agendou': a.atendente_agendou.nome.split()[0] if a.atendente_agendou else '',
        'loja_agendada': a.loja_agendada.nome.split(' - ')[-1] if a.loja_agendada and ' - ' in a.loja_agendada.nome else a.loja_agendada.nome,
        'tabulacao_atendente': a.tabulacao_atendente,
        'tabulacao_vendedor': a.tabulacao_vendedor,
        'status': 'ATRASADO'  # Status fixo como ATRASADO
    } for a in agendamentos_atrasados]

def get_all_forms_and_objects(request):
    """Obtém todos os formulários e objetos necessários para a view"""
    print("\n\n----- Iniciando get_all_forms_and_objects -----\n")
    
    hoje = timezone.now().date()
    
    # Inicializa a query base de agendamentos
    agendamentos_base_query = Agendamento.objects.select_related('loja_agendada', 'atendente_agendou')

    # Obtém informações do funcionário logado
    try:
        funcionario_logado = Funcionario.objects.get(usuario_id=request.user.id)
        nivel_cargo = funcionario_logado.cargo.nivel if funcionario_logado.cargo else None
        loja_funcionario = funcionario_logado.loja
    except Funcionario.DoesNotExist:
        if request.user.is_superuser:
            funcionario_logado = None
            nivel_cargo = 'TOTAL'
            loja_funcionario = None
        else:
            return {
                'funcionarios': [],
                'lojas': [],
                'clientes_loja': [],
                'vendedores_lista_clientes': [],
                'agendamentos_confirmacao': [],
                'agendamentos_edicao': [],
                'agendamentos_reagendamento': [],
                'todos_agendamentos': [],
                'error_message': 'Usuário não tem um funcionário associado'
            }

    # Chama a função para obter todos os agendamentos, lojas e funcionários
    todos_agendamentos_dict, todos_agend_table_dict, lojas_dict, vendedores_lista_clientes, atendentes_dict = get_all_agendamentos(
        agendamentos_base_query, 
        funcionario_logado, 
        nivel_cargo
    )

    # Chama a função para obter agendamentos 'AGENDADO'
    agendamentos_agendados_dict = get_agendamentos_agendados(agendamentos_base_query, funcionario_logado, nivel_cargo)

    # Chama a nova função para obter agendamentos 'REAGENDADO'
    agendamentos_reagendados_dict = obter_agendamentos_reagendados(agendamentos_base_query, funcionario_logado, nivel_cargo)

    # Chama a nova função para obter agendamentos 'CONFIRMADO'
    agendamentos_confirmados_dict = get_agendamentos_confirmados(agendamentos_base_query, funcionario_logado, nivel_cargo, loja_funcionario)

    # Chama a nova função para obter agendamentos com subsídio
    agendamentos_tac = get_agendamentos_tac(todos_agendamentos_dict)
    print("\nResultado get_agendamentos_tac:", agendamentos_tac)

    # Chama a nova função para obter agendamentos atrasados
    agendamentos_atrasados_dict = get_agendamentos_atrasados(agendamentos_base_query, funcionario_logado, nivel_cargo, loja_funcionario)

    print("\n----- Finalizando get_all_forms_and_objects -----\n")
    
    return {
        'funcionarios': atendentes_dict,  # Lista de atendentes
        'lojas': lojas_dict,  # Dicionário de lojas
        'todos_agendamentos': todos_agendamentos_dict,
        'todos_agend_table': todos_agend_table_dict,
        'agendamentos_agendados': agendamentos_agendados_dict,
        'agendamentos_reagendados': agendamentos_reagendados_dict,
        'agendamentos_confirmados': agendamentos_confirmados_dict,
        'agendamentos_atrasados': agendamentos_atrasados_dict,
        'funcionario_logado': funcionario_logado,
        'nivel_cargo': nivel_cargo,
        'loja_funcionario': loja_funcionario,
        'vendedores_lista_clientes': vendedores_lista_clientes,  # Lista de vendedores
        'agendamentos_tac': agendamentos_tac,
    }

''' FIM DA ÁREA DE DADOS E DICIONARIOS DE FORM '''


@verificar_autenticacao
@check_access(departamento='INSS', nivel_minimo='ESTAGIO')
def render_all_forms(request):
    """
    Renderiza a página com todos os formulários do INSS e processa os formulários enviados.
    Requer autenticação e acesso ao departamento INSS (nível mínimo: ESTAGIO).
    """
    print("\n\n----- Iniciando render_all_forms -----\n")
    
    mensagem = {'texto': '', 'classe': ''}
    
    try:
        funcionario_logado = Funcionario.objects.get(usuario_id=request.user.id)
        print(f"\nFuncionário logado: {funcionario_logado.nome}")
    except Funcionario.DoesNotExist:
        funcionario_logado = None
        print("\n\nFuncionário não encontrado.")
    
    # Processamento de formulários POST
    if request.method == 'POST':
        print("\nRequest é POST. Processando formulário...")
        form_type = request.POST.get('form_type')
        print(f"\nTipo de formulário: {form_type}")

        if form_type == 'agendamento':
            print("\nProcessando formulário de agendamento...")

            if all([
                request.POST.get('nome_cliente'),
                request.POST.get('cpf_cliente'),
                request.POST.get('numero_cliente')
            ]):
                mensagem = post_agendamento(request, funcionario_logado)
                print("Agendamento processado.")
            else:
                mensagem = {
                    'texto': 'Erro no formulário de agendamento. Preencha todos os campos obrigatórios.',
                    'classe': 'error'
                }
                print("Erro no formulário de agendamento.")

        elif form_type == 'confirmacao_agendamento':
            print("\nProcessando formulário de confirmação de agendamento...")
            print(f"POST data recebida: {request.POST}")
            
            form_data = {
                'agendamento_id': request.POST.get('agendamento_id'),
                'nome_cliente': request.POST.get('nome_cliente'),
                'numero_cliente': request.POST.get('numero_cliente'),
                'dia_agendado': request.POST.get('dia_agendado'),
                'tabulacao_atendente': request.POST.get('tabulacao_atendente'),
                'nova_dia_agendado': request.POST.get('nova_dia_agendado'),
                'observacao': request.POST.get('observacao')
            }
            print(f"Dados extraídos do formulário: {form_data}")
            
            if not form_data['agendamento_id']:
                mensagem = {
                    'texto': 'Erro: ID do agendamento não fornecido',
                    'classe': 'danger'
                }
            else:
                mensagem = post_confirmacao_agem(form_data, funcionario_logado)

        elif form_type == 'lista_clientes':
            print("\nProcessando formulário de lista de clientes...")
            lista_clientes_data = {
                # Campos básicos
                'agendamento_id': request.POST.get('agendamento_id'),
                'nome_cliente': request.POST.get('nome_cliente'),
                'cpf_cliente': request.POST.get('cpf_cliente'),
                'numero_cliente': request.POST.get('numero_cliente'),
                'dia_agendado': request.POST.get('dia_agendado'),
                'tabulacao_atendente': request.POST.get('tabulacao_atendente'),
                'atendente_agendou': request.POST.get('atendente_agendou'),
                'loja_agendada': request.POST.get('loja_agendada'),
                
                # Campos de vendedor e tabulação
                'vendedor_id': request.POST.get('vendedor_id'),
                'tabulacao_vendedor': request.POST.get('tabulacao_vendedor'),
                'observacao_vendedor': request.POST.get('observacao_vendedor'),
                
                # Campos específicos para FECHOU NEGOCIO
                'tipo_negociacao': request.POST.get('tipo_negociacao'),
                'banco': request.POST.get('banco'),
                'subsidio': request.POST.get('subsidio'),
                'tac': request.POST.get('tac'),
                'acao': request.POST.get('acao'),
                'associacao': request.POST.get('associacao'),
                'aumento': request.POST.get('aumento')
            }
            print(f"Dados recebidos: {lista_clientes_data}")

            if lista_clientes_data['agendamento_id'] and lista_clientes_data['tabulacao_vendedor']:
                print('Entrou no if do list!')
                mensagem = post_venda_tabulacao(lista_clientes_data, funcionario_logado)
                print("Tabulação processada.")
            else:
                mensagem = {
                    'texto': 'Erro no formulário de lista de clientes. Preencha todos os campos obrigatórios.',
                    'classe': 'error'
                }
                print("Erro no formulário de lista de clientes.")

        elif form_type == 'status_tac':
            print("\nProcessando atualização de status TAC...")
            agendamento_id = request.POST.get('agendamento_id')
            status_tac = request.POST.get('status_tac')
            print(f"ID do agendamento: {agendamento_id}, Status TAC: {status_tac}")

            if not agendamento_id:
                print("Erro: ID do agendamento não fornecido")
                mensagem = {
                    'texto': 'Erro: ID do agendamento não fornecido',
                    'classe': 'error'
                }
            else:
                # Prepara os dados para post_status_tac
                status_data = {
                    'agendamento_id': agendamento_id,
                    'status': status_tac
                }
                
                # Chama post_status_tac com os dados preparados
                mensagem = post_status_tac(status_data, funcionario_logado)
                
                # Se a atualização foi bem sucedida, registra a mensagem de atualização
                if mensagem['classe'] == 'success':
                    try:
                        agendamento = Agendamento.objects.get(id=agendamento_id)
                        data_atual = get_current_sp_time()
                        
                        # Cria a mensagem de atualização
                        mensagem_update = (
                            f"Atualização de Status TAC realizada em {data_atual.strftime('%d/%m/%Y às %H:%M:%S')} (Horário de Brasília)\n"
                            f"Status anterior: {agendamento.status_tac or 'Não definido'}\n"
                            f"Novo status: {status_tac}\n"
                            f"Atualizado por: {funcionario_logado.nome if funcionario_logado else request.user.username}"
                        )
                        
                        # Atualiza a mensagem no agendamento
                        agendamento.mensagem_update_tac = mensagem_update
                        agendamento.save()
                        
                        print(f"Mensagem de atualização registrada: \n{mensagem_update}")
                    except Exception as e:
                        print(f"Erro ao registrar mensagem de atualização: {str(e)}")
                
                print(f"Mensagem retornada: {mensagem}")
            print("----- Finalizando atualização de status TAC -----\n")

        elif form_type == 'update_tac':
            print("\n----- Iniciando atualização de valor TAC -----")
            agendamento_id = request.POST.get('agendamento_id')
            valor_tac = request.POST.get('valor_tac')
            print(f"ID do agendamento recebido: {agendamento_id}")
            print(f"Valor TAC recebido: {valor_tac}")
            
            try:
                # Limpa o valor recebido (remove R$ e converte vírgula para ponto)
                valor_tac = valor_tac.replace('R$', '').replace('.', '').replace(',', '.').strip()
                valor_tac = Decimal(valor_tac)
                print(f"Valor TAC após formatação: R$ {valor_tac}")
                
                # Obtém a data e hora atual em SP
                data_atual = get_current_sp_time()
                
                # Atualiza o agendamento
                agendamento = Agendamento.objects.get(id=agendamento_id)
                valor_tac_anterior = agendamento.tac or Decimal('0.00')
                
                # Cria a mensagem de atualização
                mensagem_update = (
                    f"Atualização de TAC realizada em {data_atual.strftime('%d/%m/%Y às %H:%M:%S')} (Horário de Brasília)\n"
                    f"Valor anterior: R$ {valor_tac_anterior:.2f}\n"
                    f"Novo valor: R$ {valor_tac:.2f}\n"
                    f"Atualizado por: {funcionario_logado.nome}"
                )
                
                # Atualiza o agendamento com o novo valor e a mensagem
                agendamento.tac = valor_tac
                agendamento.mensagem_update_tac = mensagem_update
                agendamento.save()
                
                print(f"Agendamento {agendamento_id} atualizado com sucesso!")
                print(f"Mensagem de atualização: \n{mensagem_update}")
                
                # Registra o log de alteração
                LogAlteracao.objects.create(
                    agendamento_id=str(agendamento.id),
                    mensagem=mensagem_update,
                    status=True,
                    funcionario=funcionario_logado
                )
                print("Log de alteração registrado")
                
                mensagem = {
                    'texto': 'Valor TAC atualizado com sucesso!',
                    'classe': 'success'
                }
                print("Mensagem de sucesso definida")
            except (Agendamento.DoesNotExist, ValueError) as e:
                print(f"ERRO: {str(e)}")
                mensagem = {
                    'texto': f'Erro ao atualizar valor TAC: {str(e)}',
                    'classe': 'error'
                }
                print("Mensagem de erro definida")
            print("----- Finalizando atualização de valor TAC -----\n")
        elif form_type == 'cliente_rua':
            print("\nProcessando formulário de Cliente Rua...")
            mensagem = post_cliente_rua(request, funcionario_logado)

    else:
        print("\nRequest não é POST. Carregando formulários vazios...")

    print("\nTentando chamar get_all_forms_and_objects...")
    context_data = get_all_forms_and_objects(request)
    print("\nRetornou de get_all_forms_and_objects.")

    # Atualiza o contexto com mensagem e funcionário logado
    context_data.update({
        'mensagem': mensagem,
        'funcionario_logado': funcionario_logado,
    })

    # Logs para debug
    print("\nContexto dos dados obtidos:")
    if 'funcionarios' in context_data:
        print(f"\nFuncionários: {[f['nome'] for f in context_data['funcionarios'].values()]}\n")
    else:
        print("\nNenhum funcionário encontrado no contexto\n")
    
    print(f"Clientes Confirmados: {context_data.get('clientes_loja', [])}\n")

    print("\n----- Finalizando render_all_forms -----\n")
    return render(request, 'inss/all_forms.html', context_data)

''' INICIO BLOCO RACKING '''

def get_cards(periodo='mes'):
    print("\n----- Iniciando get_cards -----\n")
    
    hoje = timezone.now()
    
    # Busca a meta geral ativa
    meta_geral = RegisterMeta.objects.filter(
        tipo='GERAL',
        status=True,
        range_data_inicio__lte=hoje.date(),
        range_data_final__gte=hoje.date()
    ).first()
    
    if meta_geral:
        print(f"Meta geral encontrada: {meta_geral}")
        primeiro_dia_geral = timezone.make_aware(datetime.combine(meta_geral.range_data_inicio, time(0, 1)))  # Início às 00:01
        ultimo_dia_geral = timezone.make_aware(datetime.combine(meta_geral.range_data_final, time(23, 59, 59)))  # Fim às 23:59
    else:
        print("Nenhuma meta geral encontrada.")
        primeiro_dia_geral = timezone.make_aware(hoje.replace(day=1))
        ultimo_dia_geral = timezone.make_aware(datetime.combine((hoje.replace(day=1, month=hoje.month + 1) - timezone.timedelta(days=1)), time(23, 59, 59)))

    # Armazena todos os registros de RegisterMoney em um dicionário
    registros_dicionario = {valor.id: valor for valor in RegisterMoney.objects.all()}
    print(f"Registros de RegisterMoney encontrados: {len(registros_dicionario)}")
    
    # Filtra os registros financeiros no período da meta geral
    valores_range = [valor for valor in registros_dicionario.values() if primeiro_dia_geral <= valor.data <= ultimo_dia_geral]
    
    print(f"Valores range filtrados encontrados: {len(valores_range)}")  # Verifica quantos registros foram encontrados
    
    # Calcula faturamento total para a meta geral
    faturamento_total = 0.0  # Inicializa como float
    for valor in valores_range:
        print(f"Valor: {valor.valor_est}")  # Imprime cada valor
        faturamento_total += float(valor.valor_est) if valor.valor_est is not None else 0.0  # Soma diretamente como float, tratando None
    
    # Formata o faturamento total
    faturamento_total_formatado = f"R$ {faturamento_total:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')
    
    print(f"Faturamento total calculado: {faturamento_total_formatado}")  # Verifica o total
    
    # Busca quantidade de vendas (agendamentos com tabulacao_vendedor diferente de vazio e não 'NÃO QUIS OUVIR')
    qtd_vendas = Agendamento.objects.filter(
        dia_agendado__date__range=[primeiro_dia_geral, ultimo_dia_geral],
        tabulacao_vendedor__isnull=False,  # Verifica se o campo tabulacao_vendedor está preenchido
    ).exclude(tabulacao_vendedor='NÃO QUIS OUVIR').count()  # Exclui agendamentos com tabulacao_vendedor igual a 'NÃO QUIS OUVIR'
    
    # Busca quantidade de agendamentos confirmados
    qtd_agendamentos = Agendamento.objects.filter(
        dia_agendado__date__range=[primeiro_dia_geral, ultimo_dia_geral],
        tabulacao_atendente='CONFIRMADO'
    ).count()
    
    # Calcula o percentual em relação à meta geral, se existir
    percentual_meta = 0
    if meta_geral and meta_geral.valor:
        percentual_meta = round((faturamento_total / float(meta_geral.valor) * 100), 2)  # Converte meta_geral.valor para float
    
    # Prepara o contexto com os dados formatados
    context_data = {
        'valor_total': faturamento_total_formatado,
        'percentual': percentual_meta,
        'qtd_vendas': qtd_vendas,
        'qtd_agendamentos': qtd_agendamentos,
        'periodo': {
            'inicio': primeiro_dia_geral,  # Removido .date()
            'fim': ultimo_dia_geral.date()  # Aqui está correto
        }
    }
    
    print(f"Faturamento INSS: {context_data['valor_total']}")
    print(f"Percentual da Meta: {context_data['percentual']}%")
    print(f"Quantidade de Vendas: {context_data['qtd_vendas']}")
    print(f"Quantidade de Agendamentos: {context_data['qtd_agendamentos']}")
    print("\n----- Finalizando get_cards -----\n")
    
    return context_data

def get_podium(periodo='mes'):
    """
    Calcula o pódio das lojas baseado nos valores registrados no RegisterMoney
    usando o campo loja diretamente
    """
    print("\n----- Iniciando get_podium -----\n")
    
    hoje = timezone.now().date()
    
    # Busca metas ativas
    metas_ativas = RegisterMeta.objects.filter(
        status=True,
        range_data_inicio__lte=hoje,
        range_data_final__gte=hoje
    ).filter(
        Q(tipo='GERAL') |
        Q(tipo='EQUIPE', setor='INSS')
    )
    
    print(f"Metas ativas encontradas: {metas_ativas.count()}")
    
    # Define o período
    if not metas_ativas.exists():
        print("Nenhuma meta ativa encontrada, usando mês atual")
        primeiro_dia = hoje.replace(day=1)
        ultimo_dia = (hoje.replace(day=1, month=hoje.month + 1) - timezone.timedelta(days=1))
    else:
        meta_inss = metas_ativas.filter(tipo='EQUIPE', setor='INSS').first()
        meta_atual = meta_inss if meta_inss else metas_ativas.first()
        
        print(f"Usando meta: {meta_atual.titulo} ({meta_atual.tipo})")
        print(f"Período: {meta_atual.range_data_inicio} até {meta_atual.range_data_final}")
        
        primeiro_dia = meta_atual.range_data_inicio
        ultimo_dia = meta_atual.range_data_final
    
    # Busca registros com loja preenchida no período
    valores_range = RegisterMoney.objects.filter(
        data__date__range=[primeiro_dia, ultimo_dia],
        status=True,
        loja__isnull=False
    ).select_related('loja')  # Otimiza a consulta incluindo os dados da loja
    
    print(f"Registros encontrados no período: {valores_range.count()}")
    
    # Dicionário para armazenar valores por loja
    valores_por_loja = {}
    
    # Processa os valores
    for venda in valores_range:
        loja = venda.loja
        if not loja:
            continue
            
        loja_id = loja.id
        if loja_id not in valores_por_loja:
            nome_loja = loja.nome.split(' - ')[1] if ' - ' in loja.nome else loja.nome
            valores_por_loja[loja_id] = {
                'id': loja_id,
                'nome': nome_loja,
                'logo': loja.logo.url if loja.logo else '/static/img/default-store.png',
                'total_fechamentos': Decimal('0'),
                'meta_valor': next((m.valor for m in metas_ativas if m.loja == nome_loja), Decimal('0'))
            }
        
        valores_por_loja[loja_id]['total_fechamentos'] += Decimal(str(venda.valor_est))

    # Converte para lista e ordena
    podium = sorted(
        valores_por_loja.values(),
        key=lambda x: x['total_fechamentos'],
        reverse=True
    )[:3]  # Pega apenas os 3 primeiros

    # Adiciona posição no pódio e formata os valores
    for i, loja in enumerate(podium):
        loja['posicao'] = i + 1
        loja['total_fechamentos'] = f"R$ {loja['total_fechamentos']:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')
        if loja['meta_valor']:
            loja['meta_valor'] = f"R$ {loja['meta_valor']:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')

    print(f"Pódio calculado para o período: {primeiro_dia} até {ultimo_dia}")
    print(f"Total de lojas no pódio: {len(podium)}")
    print("\n----- Finalizando get_podium -----\n")
    
    return {
        'podium': podium,
        'periodo': {
            'inicio': primeiro_dia,
            'fim': ultimo_dia
        }
    }

def get_tabela_ranking(periodo='mes'):
    """
    Calcula o ranking dos atendentes baseado nos agendamentos confirmados e presentes em loja
    """
    print("\n----- Iniciando get_tabela_ranking -----\n")
    
    hoje = timezone.now().date()
    
    # Calcula o primeiro e o último dia da semana atual
    primeiro_dia_semana = hoje - timedelta(days=hoje.weekday())  # Domingo
    ultimo_dia_semana = primeiro_dia_semana + timedelta(days=6)  # Sábado

    print(f"Período do ranking: {primeiro_dia_semana} até {ultimo_dia_semana}")
    
    # Filtra agendamentos dentro do intervalo de datas
    agendamentos_data_range = Agendamento.objects.filter(
        dia_agendado__date__gte=primeiro_dia_semana,
        dia_agendado__date__lte=ultimo_dia_semana,
        atendente_agendou__isnull=False
    ).select_related('atendente_agendou')

    print(f"Total de agendamentos no intervalo de datas: {agendamentos_data_range.count()}")

    # Agrupa agendamentos por atendente
    ranking_por_atendente = {}
    
    for agendamento in agendamentos_data_range:
        atendente = agendamento.atendente_agendou
        if atendente not in ranking_por_atendente:
            ranking_por_atendente[atendente] = {
                'funcionario': atendente,
                'nome': atendente.nome,
                'foto': atendente.foto.url if atendente.foto else None,
                'total_confirmados': 0,  # Agendamentos com tabulacao 'CONFIRMADO'
                'total_em_loja': 0,      # Agendamentos confirmados e com tabulação do vendedor
            }
        
        # Conta agendamentos confirmados
        if agendamento.tabulacao_atendente == 'CONFIRMADO':
            ranking_por_atendente[atendente]['total_confirmados'] += 1
            
            # Conta agendamentos que foram para loja (tabulação diferente de 'NÃO QUIS OUVIR')
            if agendamento.tabulacao_vendedor and agendamento.tabulacao_vendedor != 'NÃO QUIS OUVIR':
                ranking_por_atendente[atendente]['total_em_loja'] += 1

    # Prepara dados para o ranking
    ranking_data = []
    for atendente, dados in ranking_por_atendente.items():
        ranking_data.append({
            'posicao': len(ranking_data) + 1,
            'foto': dados['foto'],
            'nome': dados['nome'],
            'total_confirmados': dados['total_confirmados'],
            'total_em_loja': dados['total_em_loja']
        })

    # Ordena o ranking pelo número total de clientes em loja (decrescente)
    # Em caso de empate, usa o total de confirmados como segundo critério
    ranking_data.sort(key=lambda x: (x['total_em_loja'], x['total_confirmados']), reverse=True)
    
    # Atualiza as posições após a ordenação
    for i, dados in enumerate(ranking_data, 1):
        dados['posicao'] = i
    
    print(f"Dados do ranking calculados para {len(ranking_data)} atendentes")
    
    # Log para debug
    for dados in ranking_data:
        print(f"Atendente: {dados['nome']}")
        print(f"Posição: {dados['posicao']}")
        print(f"Total Em Loja: {dados['total_em_loja']}")
        print(f"Total Confirmados: {dados['total_confirmados']}")
        print("---")
    
    print("\n----- Finalizando get_tabela_ranking -----\n")
    
    return {
        'ranking_data': ranking_data,
        'periodo': {
            'inicio': primeiro_dia_semana,
            'fim': ultimo_dia_semana
        },
        'total_agendamentos': agendamentos_data_range.count()
    }


def get_ranking(request):
    """
    Obtém os dados do ranking e retorna o contexto
    """
    print("\n----- Iniciando get_ranking -----\n")
    
    dados_ranking = get_tabela_ranking()
    dados_podium = get_podium()
    dados_cards = get_cards()
    # Log para debug do percentual_conf
    for dados in dados_ranking['ranking_data']:
        print(f"Percentual de confirmação para {dados['nome']}: {dados.get('percentual_conf', 0)}%")
    context_data = {
        'ranking_data': dados_ranking['ranking_data'],
        'periodo': dados_ranking['periodo'],
        'total_agendamentos': dados_ranking['total_agendamentos'],
        'podium': dados_podium['podium'],
        'cards': dados_cards
    }
    
    print("\n----- Finalizando get_ranking -----\n")
    return context_data

@verificar_autenticacao
@check_access(departamento='INSS', nivel_minimo='ESTAGIO')
def render_ranking(request):
    """
    Renderiza a página de ranking com os dados necessários.
    Requer autenticação e acesso ao departamento INSS (nível mínimo: ESTAGIO).
    """
    print("\n----- Iniciando render_ranking -----\n")
    
    # Verifica se o usuário está logado e obtém o funcionário associado
    funcionario_logado = None
    if request.user.is_authenticated:
        try:
            funcionario_logado = Funcionario.objects.get(usuario=request.user)
        except Funcionario.DoesNotExist:
            print("Usuário logado não tem funcionário associado")
    
    # Obtém os dados do ranking
    context = get_ranking(request)
    
    # Adiciona o funcionário logado ao contexto
    context['funcionario_logado'] = funcionario_logado
    
    print("\n----- Finalizando render_ranking -----\n")
    return render(request, 'inss/ranking.html', context)


''' FINAL BLOCO RANKING '''