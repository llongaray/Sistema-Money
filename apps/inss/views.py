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
        
        # Se está mudando de PAGO para NÃO PAGO ou EM ESPERA
        if status_anterior == 'PAGO' and novo_status in ['NÃO PAGO', 'EM ESPERA']:
            # Busca e remove registro em RegisterMoney se existir
            registro_money = RegisterMoney.objects.filter(
                funcionario=agendamento.vendedor_loja,
                cpf_cliente=agendamento.cpf_cliente,
                valor_est=float(agendamento.tac),
                status=True
            ).first()
            
            if registro_money:
                registro_money.delete()
                print(f"Registro de TAC removido para CPF {agendamento.cpf_cliente}")
                
                # Registra o log de remoção
                LogAlteracao.objects.create(
                    agendamento_id=str(agendamento.id),
                    mensagem=f"Registro de TAC removido devido à mudança de status para {novo_status}",
                    status=True,
                    funcionario=funcionario_logado
                )
        
        # Se está mudando para PAGO
        elif novo_status == 'PAGO':
            # Verifica se já existe registro com mesmo CPF e valor
            registro_existente = RegisterMoney.objects.filter(
                funcionario=agendamento.vendedor_loja,
                cpf_cliente=agendamento.cpf_cliente,
                valor_est=float(agendamento.tac),
                status=True
            ).exists()
            
            # Só registra se não existir registro anterior
            if not registro_existente and agendamento.tac and agendamento.vendedor_loja:
                RegisterMoney.objects.create(
                    funcionario=agendamento.vendedor_loja,
                    cpf_cliente=agendamento.cpf_cliente,
                    valor_est=float(agendamento.tac),
                    status=True,
                    data=timezone.now()
                )
                print(f"Valor TAC R$ {agendamento.tac} registrado para {agendamento.vendedor_loja.nome}")
            else:
                print("Registro já existe ou agendamento sem TAC/vendedor definido")
        
        # Atualiza o status e data de pagamento
        agendamento.status_tac = novo_status
        if novo_status == 'PAGO':
            agendamento.data_pagamento_tac = timezone.now()
        else:
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
            hora_atual = timezone.now().time()
            dados_atualizacao['dia_agendado'] = timezone.make_aware(datetime.combine(dia_agendado, hora_atual))

        # Verifica o status do agendamento
        if form_data['tabulacao_atendente'] == 'CONFIRMADO':
            dados_atualizacao['tabulacao_atendente'] = 'CONFIRMADO'
        
        elif form_data['tabulacao_atendente'] == 'REAGENDADO':
            dados_atualizacao['tabulacao_atendente'] = 'REAGENDADO'
            if form_data.get('nova_dia_agendado'):
                nova_dia_agendado = datetime.strptime(form_data['nova_dia_agendado'], '%Y-%m-%d').date()
                dados_atualizacao['dia_agendado'] = timezone.make_aware(datetime.combine(nova_dia_agendado, hora_atual))

        elif form_data['tabulacao_atendente'] == 'DESISTIU':
            dados_atualizacao['tabulacao_atendente'] = 'DESISTIU'
            dados_atualizacao['observacao_atendente'] = form_data.get('observacao', '')

        # Atualizar o agendamento com os novos dados
        for campo, valor in dados_atualizacao.items():
            setattr(agendamento, campo, valor)

        agendamento.save()

        # Criar log de alteração
        LogAlteracao.objects.create(
            agendamento_id=str(agendamento.id),
            mensagem=f"Confirmação de agendamento atualizada. Nova tabulação: {form_data['tabulacao_atendente']}",
            status=True,
            funcionario=funcionario
        )

        mensagem['texto'] = 'Confirmação de agendamento atualizada com sucesso!'
        mensagem['classe'] = 'success'
    
    except Exception as e:
        print(f"Erro ao processar confirmação de agendamento: {e}")
        mensagem['texto'] = 'Erro ao atualizar confirmação de agendamento.'
        mensagem['classe'] = 'danger'

    return mensagem

def post_conf_loja(form_data, funcionario):
    print("\n\n----- Iniciando post_conf_loja -----\n")
    mensagem = {'texto': '', 'classe': ''}

    try:
        agendamento_id = form_data.get('agendamento_id')
        vendedor_id = form_data.get('vendedor_id')
        tabulacao_vendedor = form_data.get('tabulacao_vendedor')

        print(f"ID do agendamento: {agendamento_id}, Vendedor ID: {vendedor_id}, Tabulação Vendedor: {tabulacao_vendedor}")

        if not agendamento_id or not vendedor_id:
            print("Erro: ID do agendamento ou ID do vendedor não fornecido.")
            raise ValueError("ID do agendamento ou ID do vendedor não fornecido.")

        # Obtém o agendamento e o vendedor
        print("Buscando agendamento e vendedor...")
        agendamento = Agendamento.objects.get(id=agendamento_id)
        vendedor_loja = Funcionario.objects.get(id=vendedor_id)
        print(f"Agendamento encontrado: {agendamento}, Vendedor encontrado: {vendedor_loja.nome}")

        # Atualiza os campos necessários
        agendamento.vendedor_loja = vendedor_loja
        agendamento.tabulacao_vendedor = tabulacao_vendedor
        agendamento.data_confirmacao_loja = timezone.now()  # Atualiza a data de confirmação da loja
        print("Campos atualizados: vendedor_loja, tabulacao_vendedor e data_confirmacao_loja.")

        # Salva as alterações
        agendamento.save()
        print("Agendamento salvo com as novas informações.")

        # Criar log de alteração
        LogAlteracao.objects.create(
            agendamento_id=str(agendamento.id),
            mensagem=f"Confirmação de loja atualizada. Vendedor: {vendedor_loja.nome}, Tabulação: {tabulacao_vendedor}",
            status=True,
            funcionario=funcionario
        )
        print("Log de alteração criado com sucesso.")

        mensagem['texto'] = 'Confirmação de loja atualizada com sucesso!'
        mensagem['classe'] = 'success'

    except Exception as e:
        mensagem['texto'] = f'Erro ao atualizar confirmação de loja: {str(e)}'
        mensagem['classe'] = 'error'
        print(f"Erro: {str(e)}")
        LogAlteracao.objects.create(
            agendamento_id=str(agendamento_id) if agendamento_id else 'N/A',
            mensagem=f"Erro ao atualizar confirmação de loja: {str(e)}",
            status=False,
            funcionario=funcionario
        )
        print("Log de erro criado.")

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
        
        hora_atual = timezone.now().time()
        dia_agendado_com_hora = timezone.make_aware(datetime.combine(dia_agendado, hora_atual))

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

    # Se o novo_status for 'PAGO', atualiza a data_tac_paga
    if novo_status == 'PAGO':
        agendamento.data_tac_paga = timezone.now()  # Atualiza a data_tac_paga com a data atual

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




def criar_dicionario_agendamento(agendamento, hoje, incluir_status=True):
    dicionario = {
        'id': agendamento.id,
        'nome_cliente': agendamento.nome_cliente,
        'cpf_cliente': agendamento.cpf_cliente,
        'numero_cliente': agendamento.numero_cliente,
        'dia_agendado': agendamento.dia_agendado.strftime('%d/%m/%Y'),
        'atendente_nome': agendamento.atendente_agendou.nome if agendamento.atendente_agendou else None,
        'loja_nome': agendamento.loja_agendada.nome if agendamento.loja_agendada else None,
        'tabulacao_atendente': agendamento.tabulacao_atendente,
        'tabulacao_vendedor': agendamento.tabulacao_vendedor
    }
    if incluir_status:
        dicionario['status_dias'] = calcular_status_dias(agendamento, hoje)
    return dicionario

"""
Função get_all_agem
-------------------
Objetivo: Buscar e formatar todos os agendamentos do sistema.

Funcionalidades:
- Recebe uma lista de agendamentos e a data atual
- Agrupa os agendamentos por CPF
- Mantém apenas o agendamento mais recente de cada CPF
- Calcula o status de cada agendamento (HOJE, ATRASADO, etc)
- Adiciona contagem de quantos agendamentos cada CPF possui
- Retorna lista formatada com os agendamentos mais recentes e mensagens de log

Template: Usado na tabela de "Todos os Agendamentos" que mostra o histórico completo
"""
def get_all_agem(agendamentos_dict, hoje):
    """Busca todos os agendamentos e retorna dicionário formatado"""
    
    # Logs de mensagens
    mensagem = []
    
    # 1. Busca todos os agendamentos
    mensagem.append("\nBuscando todos os agendamentos...")
    count_agens = len(agendamentos_dict)
    mensagem.append(f"Total de agendamentos encontrados: {count_agens}")

    # 2. Calcula contagem de agendamentos por CPF
    contagem_por_cpf = {}
    for agendamento in agendamentos_dict:
        cpf = agendamento['cpf_cliente']
        contagem_por_cpf[cpf] = contagem_por_cpf.get(cpf, 0) + 1

    # 3. Criar lista com todos os agendamentos
    todos_agem_disc = [
        {
            'id': a['id'],
            'nome_cliente': a['nome_cliente'],
            'cpf_cliente': a['cpf_cliente'],
            'numero_cliente': a['numero_cliente'],
            'dia_agendado': a['dia_agendado'].strftime('%d/%m/%Y'),  # Formato brasileiro
            'dia_agendado_completo': a['dia_agendado'].strftime('%Y-%m-%d %H:%M:%S'),
            'atendente_nome': a['atendente_agendou'].nome if a['atendente_agendou'] else '',
            'loja_nome': a['loja_agendada'].nome if a['loja_agendada'] else '',
            'tabulacao_atendente': a['tabulacao_atendente'] or '',
            'tabulacao_vendedor': a['tabulacao_vendedor'] or '',
            'status_dias': calcular_status_dias(a, hoje),
            'total_agendamentos': contagem_por_cpf[cpf]  # Corrigido para usar a variável cpf
        } for a in agendamentos_dict  # Corrigido para fechar a lista corretamente
    ]

    # 4. Ordenar por data mais recente
    todos_agem_disc.sort(key=lambda x: x['dia_agendado_completo'], reverse=True)

    mensagem.append(f"Total de agendamentos processados: {len(todos_agem_disc)}")
    mensagem.append(f"Total de CPFs únicos: {len(contagem_por_cpf)}")

    return todos_agem_disc, mensagem

"""
Função get_reagem
----------------
Objetivo: Buscar e formatar os agendamentos que foram reagendados.

Funcionalidades:
- Filtra agendamentos com status 'REAGENDADO' e sem tabulação do vendedor
- Formata as datas em diferentes padrões para uso no template
- Calcula o status de cada agendamento
- Inclui informações do atendente e loja

Template: Usado na tabela de "Reagendamentos" que mostra clientes que precisaram remarcar
"""
def get_reagem(agendamentos_base_query, hoje):
    """Obtém os agendamentos reagendados"""
    print("\nBuscando agendamentos reagendados...")
    
    # Agendamentos reagendados - apenas com tabulacao_atendente='REAGENDADO'
    agendamentos_reagendados = agendamentos_base_query.filter(
        tabulacao_atendente='REAGENDADO',
        tabulacao_vendedor__isnull=True
    ).order_by('dia_agendado')  # Ordenar por data do agendamento
    
    print(f"\nTotal de agendamentos reagendados encontrados: {agendamentos_reagendados.count()}")

    # Criar dicionário com informações detalhadas
    agendamentos_reagendados_dicionario = [{
        'id': a.id,
        'nome_cliente': a.nome_cliente,
        'cpf_cliente': a.cpf_cliente,
        'numero_cliente': a.numero_cliente,
        'dia_agendado': a.dia_agendado.strftime('%d/%m/%Y'),  # Formato brasileiro
        'dia_agendado_completo': a.dia_agendado.strftime('%Y-%m-%d %H:%M:%S'),  # Formato completo
        'dia_agendado_form': a.dia_agendado.strftime('%Y-%m-%d'),  # Formato para formulário
        'atendente_nome': a.atendente_agendou.nome if a.atendente_agendou else '',
        'loja_nome': a.loja_agendada.nome if a.loja_agendada else '',
        'tabulacao_atendente': a.tabulacao_atendente or '',
        'tabulacao_vendedor': a.tabulacao_vendedor or '',
        'status_dias': calcular_status_dias(a, hoje)
    } for a in agendamentos_reagendados]

    # Log para debug
    for agendamento in agendamentos_reagendados_dicionario:
        print(f"Agendamento reagendado encontrado: {agendamento['nome_cliente']} - {agendamento['dia_agendado']}")

    return agendamentos_reagendados_dicionario

def get_cliente_loja(agendamentos_base_query, hoje, funcionario_logado=None, is_superuser=False):
    """Obtém os clientes agendados na loja baseado no nível de acesso"""
    print("\nBuscando clientes na loja...")

    # Filtra todos os clientes com agendamentos
    clientes_loja_base = agendamentos_base_query.select_related(
        'atendente_agendou', 
        'loja_agendada'
    )

    # Aplica filtros baseados no nível de acesso
    if is_superuser:
        print("Usuário é superuser - mostrando todos os agendamentos")
        pass  # Não aplica filtros
    elif funcionario_logado:
        nivel_cargo = funcionario_logado.cargo.nivel if funcionario_logado.cargo else None
        print(f"Funcionário logado: {funcionario_logado.nome}, Nível: {nivel_cargo}")

        if nivel_cargo in ['ESTAGIO', 'PADRÃO']:
            print("Nível ESTAGIO/PADRÃO - filtrando por loja e data atual")
            clientes_loja_base = clientes_loja_base.filter(
                loja_agendada=funcionario_logado.loja,
                dia_agendado__date=hoje
            )
        elif nivel_cargo == 'GERENTE':
            print("Nível GERENTE - filtrando apenas por loja")
            clientes_loja_base = clientes_loja_base.filter(
                loja_agendada=funcionario_logado.loja
            )
        elif nivel_cargo in ['COORDENADOR', 'SUPERVISOR GERAL', 'TOTAL']:
            print("Nível superior - mostrando todos os agendamentos")
            pass  # Não aplica filtros
        else:
            print("Nível não reconhecido - aplicando filtros restritivos")
            clientes_loja_base = clientes_loja_base.filter(
                loja_agendada=funcionario_logado.loja,
                dia_agendado__date=hoje
            )
    else:
        print("Sem funcionário logado - retornando lista vazia")
        return []

    # Agrupa por CPF e obtém contagens e último ID
    clientes_loja_agrupados = clientes_loja_base.values('cpf_cliente').annotate(
        total_agendamentos=Count('id'),
        ultimo_id=Max('id')
    ).order_by('cpf_cliente')

    # Obtém apenas os agendamentos mais recentes por CPF
    ids_mais_recentes = [item['ultimo_id'] for item in clientes_loja_agrupados]
    clientes_loja = clientes_loja_base.filter(
        id__in=ids_mais_recentes
    ).order_by('-dia_agendado')

    # Formata dados para o template
    clientes_loja_dicionario = [{
        'id': agendamento.id,
        'nome_cliente': agendamento.nome_cliente,
        'cpf_cliente': agendamento.cpf_cliente,
        'numero_cliente': agendamento.numero_cliente,
        'dia_agendado_completo': agendamento.dia_agendado.strftime('%Y-%m-%d %H:%M:%S'),
        'dia_agendado': agendamento.dia_agendado.strftime('%d/%m/%Y'),
        'tabulacao_atendente': agendamento.tabulacao_atendente or 'PENDENTE',
        'atendente_nome': getattr(agendamento.atendente_agendou, 'nome', ''),
        'loja_nome': getattr(agendamento.loja_agendada, 'nome', ''),
        'status_dias': calcular_status_dias(agendamento, hoje),
        'total_agendamentos': next(
            (item['total_agendamentos'] for item in clientes_loja_agrupados 
             if item['ultimo_id'] == agendamento.id),
            1
        )
    } for agendamento in clientes_loja]

    print(f"Total de clientes encontrados: {len(clientes_loja_dicionario)}")
    return clientes_loja_dicionario

def get_all_forms_and_objects(request_post):
    """Obtém todos os formulários e objetos necessários para a view"""
    print("\n\n----- Iniciando get_all_forms_and_objects -----\n")
    
    hoje = timezone.now().date()
    
    # Inicializa a query base de agendamentos
    agendamentos_base_query = Agendamento.objects.select_related('loja_agendada', 'atendente_agendou')

    # Obtém informações do funcionário logado
    try:
        funcionario_logado = Funcionario.objects.get(usuario_id=request_post.user.id)
        nivel_cargo = funcionario_logado.cargo.nivel if funcionario_logado.cargo else None
        loja_funcionario = funcionario_logado.loja
    except Funcionario.DoesNotExist:
        if request_post.user.is_superuser:
            funcionario_logado = None
            nivel_cargo = 'TOTAL'
            loja_funcionario = None
        else:
            return {
                'form_agendamento': AgendamentoForm(funcionarios=Funcionario.objects.none()),
                'form_confirmacao': ConfirmacaoAgendamentoForm(),
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

    # Obtém lista de funcionários baseada no nível de acesso
    if request_post.user.is_superuser:
        funcionarios = Funcionario.objects.all()
        lojas = Loja.objects.all()  # Mostra todas as lojas para superuser
    else:
        if nivel_cargo in ['ESTAGIO', 'PADRÃO']:
            funcionarios = [funcionario_logado]  # Apenas o próprio funcionário
            lojas = Loja.objects.filter(id=funcionario_logado.loja.id)  # Apenas a loja do funcionário
        else:
            funcionarios = Funcionario.objects.all()  # Todos os funcionários
            lojas = Loja.objects.all()  # Mostra todas as lojas

    # Cria o dicionário de vendedores
    vendedores_lista_clientes = {
        funcionario.id: {
            'id': funcionario.id,
            'nome': funcionario.nome.split()[0]  # Primeiro nome
        }
        for funcionario in funcionarios
    }
    print(f"Vendedores: {vendedores_lista_clientes}")

    # Configuração de formulários
    form_agendamento = AgendamentoForm(funcionarios=funcionarios)
    form_confirmacao = ConfirmacaoAgendamentoForm()

    # Obtém todos os agendamentos sem filtro
    todos_agendamentos = agendamentos_base_query.all().order_by('cpf_cliente', '-dia_agendado')
    hoje = datetime.now().date()  # Obtém a data atual

    todos_agendamentos_dict = [{
        'id': a.id,
        'nome_cliente': a.nome_cliente,
        'cpf_cliente': a.cpf_cliente,
        'numero_cliente': a.numero_cliente,
        'dia_agendado': a.dia_agendado.strftime('%Y-%m-%d'),  # Formato para input date
        'atendente_agendou': a.atendente_agendou.nome.split()[0] if a.atendente_agendou else '',  # Primeiro nome do atendente
        'loja_agendada': a.loja_agendada.nome.split(' - ')[-1] if a.loja_agendada and ' - ' in a.loja_agendada.nome else a.loja_agendada.nome,  # Nome da loja após ' - '
        'tabulacao_atendente': a.tabulacao_atendente,
        'tabulacao_vendedor': a.tabulacao_vendedor,
        'observacao_vendedor': a.observacao_vendedor,  # Observação do vendedor
        'observacao_atendente': a.observacao_atendente,  # Observação do atendente
        'tipo_negociacao': a.tipo_negociacao,  # Tipo de negociação
        'banco': a.banco,  # Banco
        'subsidio': a.subsidio,  # Subsdio
        'tac': a.tac,  # Valor TAC
        'acao': a.acao,  # Ação
        'associacao': a.associacao,  # Associação
        'aumento': a.aumento,  # Aumento
        'status_tac': a.status_tac,  # Status do TAC
        'data_pagamento_tac': a.data_pagamento_tac.strftime('%Y-%m-%d') if a.data_pagamento_tac else None,  # Data de pagamento do TAC
        'status': (
            'HOJE' if a.dia_agendado.date() == hoje else
            'ATRASADO' if a.dia_agendado.date() < hoje else
            'EM PROCESSO' if a.tabulacao_atendente == 'AGENDADO' else
            'FECHADO'  # Você pode ajustar essa lógica conforme necessário
        ),
        'vendedor_loja': {
            'id': a.vendedor_loja.id if a.vendedor_loja else None,  # ID do vendedor
            'nome': a.vendedor_loja.nome if a.vendedor_loja else ''  # Nome do vendedor
        }
    } for a in todos_agendamentos]  # Fechamento correto da lista

    # Agendamentos com filtro de tabulacao_atendente 'AGENDADO'
    if nivel_cargo in ['ESTAGIO', 'PADRÃO']:
        agendamentos_agendados = agendamentos_base_query.filter(
            tabulacao_atendente='AGENDADO',
            atendente_agendou=funcionario_logado,
            tabulacao_vendedor__isnull=True  # Adiciona filtro para tabulacao_vendedor ser nulo
        ).order_by('dia_agendado')
    else:
        agendamentos_agendados = agendamentos_base_query.filter(
            tabulacao_atendente='AGENDADO',
            tabulacao_vendedor__isnull=True  # Adiciona filtro para tabulacao_vendedor ser nulo
        ).order_by('dia_agendado')

    agendamentos_agendados_dict = [{
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
    } for a in agendamentos_agendados]

    # Agendamentos com filtro de tabulacao_atendente 'REAGENDADO'
    if nivel_cargo in ['ESTAGIO', 'PADRÃO']:
        agendamentos_reagendados = agendamentos_base_query.filter(
            tabulacao_atendente='REAGENDADO',
            atendente_agendou=funcionario_logado,
            tabulacao_vendedor__isnull=True  # Adiciona filtro para tabulacao_vendedor ser nulo
        ).order_by('dia_agendado')
    else:
        agendamentos_reagendados = agendamentos_base_query.filter(
            tabulacao_atendente='REAGENDADO',
            tabulacao_vendedor__isnull=True  # Adiciona filtro para tabulacao_vendedor ser nulo
        ).order_by('dia_agendado')

    agendamentos_reagendados_dict = [{
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
    } for a in agendamentos_reagendados]

    # Agendamentos com filtro de tabulacao_vendedor 'FECHOU NEGOCIO'
    if nivel_cargo not in ['COORDENADOR', 'SUPERVISOR GERAL', 'TOTAL'] and not request_post.user.is_superuser:
        agendamentos_fechou_negocio = agendamentos_base_query.filter(
            tabulacao_vendedor='FECHOU NEGOCIO',
            loja_agendada=loja_funcionario,
            tac__isnull=True  # Adicionando filtro para 'tac' ser nulo
        ).order_by('dia_agendado')
    else:
        agendamentos_fechou_negocio = agendamentos_base_query.filter(
            tabulacao_vendedor='FECHOU NEGOCIO',
            tac__isnull=True  # Adicionando filtro para 'tac' ser nulo
        ).order_by('dia_agendado')

    agendamentos_fechou_negocio_dict = [{
        'id': a.id,
        'nome_cliente': a.nome_cliente,
        'cpf_cliente': a.cpf_cliente,
        'numero_cliente': a.numero_cliente,
        'dia_agendado': a.dia_agendado.strftime('%Y-%m-%d'),
        'atendente_agendou': a.atendente_agendou.nome.split()[0] if a.atendente_agendou else '',
        'loja_agendada': a.loja_agendada.nome.split(' - ')[-1] if a.loja_agendada and ' - ' in a.loja_agendada.nome else a.loja_agendada.nome,
        'tabulacao_atendente': a.tabulacao_atendente,
        'tabulacao_vendedor': a.tabulacao_vendedor,
        'vendedor_id': a.vendedor_loja.id if a.vendedor_loja else None,  # Adicionando ID do vendedor
        'vendedor_nome': a.vendedor_loja.nome if a.vendedor_loja else '',  # Adicionando nome do vendedor
        'status': a.status_tac if a.tac else 'EM PROCESSO'  # Verifica se 'tac' está vazio
    } for a in agendamentos_fechou_negocio]

    # Agendamentos com filtro de tabulacao_atendente 'CONFIRMADO'
    if nivel_cargo not in ['COORDENADOR', 'SUPERVISOR GERAL', 'TOTAL'] and not request_post.user.is_superuser:
        agendamentos_confirmados = agendamentos_base_query.filter(
            tabulacao_atendente='CONFIRMADO',
            loja_agendada=loja_funcionario,
            tabulacao_vendedor__isnull=True  # Adiciona filtro para tabulacao_vendedor ser nulo
        ).order_by('dia_agendado')
    else:
        agendamentos_confirmados = agendamentos_base_query.filter(
            tabulacao_atendente='CONFIRMADO',
            tabulacao_vendedor__isnull=True  # Adiciona filtro para tabulacao_vendedor ser nulo
        ).order_by('dia_agendado')

    agendamentos_confirmados_dict = [{
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

    print("\n----- Total de agendamentos -----")
    print(f"Todos os agendamentos: {len(todos_agendamentos_dict)}")
    print(f"Agendamentos AGENDADO: {len(agendamentos_agendados_dict)}")
    print(f"Agendamentos REAGENDADO: {len(agendamentos_reagendados_dict)}")
    print(f"Agendamentos CONFIRMADO: {len(agendamentos_confirmados_dict)}")
    print(f"Agendamentos FECHOU NEGÓCIO: {len(agendamentos_fechou_negocio_dict)}")

    # Cria o dicionário de agendamentos com subsidio não vazio
    agendamentos_tac = [
        {
            'cpf_cliente': a.cpf_cliente,
            'nome_cliente': a.nome_cliente,
            'subsidio': a.subsidio,
            'tac': a.tac,
            'acao': a.acao,
            'status': a.status_tac if a.tac else 'EM PROCESSO',  # Verifica se 'tac' está vazio
            'agendamento_id': a.id  # Adiciona o ID do agendamento
        }
        for a in todos_agendamentos if a.subsidio
    ]

    return {
        'form_agendamento': form_agendamento,
        'form_confirmacao': form_confirmacao,
        'funcionarios': funcionarios,
        'lojas': lojas,
        'todos_agendamentos': todos_agendamentos_dict,
        'agendamentos_agendados': agendamentos_agendados_dict,
        'agendamentos_confirmados': agendamentos_confirmados_dict,
        'agendamentos_reagendados': agendamentos_reagendados_dict,
        'agendamentos_fechou_negocio': agendamentos_fechou_negocio_dict,
        'vendedores_lista_clientes': vendedores_lista_clientes,
        'agendamentos_tac': agendamentos_tac,
    }

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

            if all([request.POST.get('nome_cliente'), 
                     request.POST.get('cpf_cliente'), 
                     request.POST.get('numero_cliente')]):
                mensagem = post_agendamento(request, funcionario_logado)  # Passando request diretamente
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
            print(f"\n\nDados extraídos do formulário: {form_data}")
            
            if not form_data['agendamento_id']:
                mensagem = {
                    'texto': 'Erro: ID do agendamento não fornecido',
                    'classe': 'danger'
                }
            else:
                mensagem = post_confirmacao_agem(form_data, funcionario_logado)
                print(f"Mensagem retornada: {mensagem}")

        elif form_type == 'lista_clientes':
            print("\nProcessando formulário de lista de clientes...")
            lista_clientes_data = {
                'agendamento_id': request.POST.get('agendamento_id'),
                'nome_cliente': request.POST.get('nome_cliente'),
                'cpf_cliente': request.POST.get('cpf_cliente'),
                'numero_cliente': request.POST.get('numero_cliente'),
                'dia_agendado': request.POST.get('dia_agendado'),
                'tabulacao_atendente': request.POST.get('tabulacao_atendente'),
                'atendente_agendou': request.POST.get('atendente_agendou'),
                'loja_agendada': request.POST.get('loja_agendada'),
                'vendedor_id': request.POST.get('vendedor_id'),
                'tabulacao_vendedor': request.POST.get('tabulacao_vendedor'),
                'observacao_vendedor': request.POST.get('observacao_vendedor'),
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

        elif form_type == 'confirmacao_loja':
            print("\nProcessando formulário de confirmação de loja...")
            form_data = {
                'agendamento_id': request.POST.get('agendamento_id'),
                'vendedor_id': request.POST.get('vendedor_id'),
                'tabulacao_vendedor': request.POST.get('tabulacao_vendedor'),
            }
            mensagem = post_conf_loja(form_data, funcionario_logado)

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
                print("ID do agendamento fornecido, chamando a função post_tac...")
                mensagem = post_tac(request, funcionario_logado)
                print(f"Mensagem retornada da função post_tac: {mensagem}")
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
        print(f"\nFuncionários: {[f.nome for f in context_data['funcionarios']]}\n")
    else:
        print("\nNenhum funcionário encontrado no contexto\n")
    
    print(f"Clientes Confirmados: {context_data.get('clientes_loja', [])}\n")

    print("\n----- Finalizando render_all_forms -----\n")
    return render(request, 'inss/all_forms.html', context_data)


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
    
    # Busca quantidade de vendas (agendamentos com TAC preenchido e status_tac 'PAGO')
    qtd_vendas = Agendamento.objects.filter(
        dia_agendado__date__range=[primeiro_dia_geral, ultimo_dia_geral],
        tac__isnull=False,  # Verifica se o campo TAC está preenchido
        status_tac='PAGO'   # Verifica se o status_tac é 'PAGO'
    ).count()
    
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
    considerando as metas ativas do RegisterMeta
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
    
    # Se não encontrar metas ativas, usa o mês atual
    if not metas_ativas.exists():
        print("Nenhuma meta ativa encontrada, usando mês atual")
        primeiro_dia = hoje.replace(day=1)
        ultimo_dia = (hoje.replace(day=1, month=hoje.month + 1) - timezone.timedelta(days=1))
    else:
        # Prioriza meta EQUIPE INSS se existir
        meta_inss = metas_ativas.filter(tipo='EQUIPE', setor='INSS').first()
        meta_atual = meta_inss if meta_inss else metas_ativas.first()
        
        print(f"Usando meta: {meta_atual.titulo} ({meta_atual.tipo})")
        print(f"Período: {meta_atual.range_data_inicio} até {meta_atual.range_data_final}")
        
        primeiro_dia = meta_atual.range_data_inicio
        ultimo_dia = meta_atual.range_data_final
    
    # Busca todos os registros de valores no período
    valores_range = RegisterMoney.objects.filter(
        data__date__range=[primeiro_dia, ultimo_dia],
        status=True
    )
    
    print(f"Registros encontrados no período: {valores_range.count()}")
    
    # Obtém os IDs dos funcionários com registros
    funcionarios_ids = valores_range.values_list('funcionario_id', flat=True).distinct()
    
    # Busca funcionários do departamento INSS
    funcionarios = Funcionario.objects.filter(
        id__in=funcionarios_ids,
        departamento__grupo__name='INSS'
    ).select_related('departamento', 'loja')
    
    print(f"Funcionários INSS encontrados: {funcionarios.count()}")
    
    # Dicionário para armazenar valores por loja
    valores_por_loja = {}
    
    # Processa os valores
    for venda in valores_range:
        funcionario = next((f for f in funcionarios if f.id == venda.funcionario_id), None)
        if not funcionario or not funcionario.loja:
            continue
            
        loja_id = funcionario.loja.id
        if loja_id not in valores_por_loja:
            nome_loja = funcionario.loja.nome.split(' - ')[1] if ' - ' in funcionario.loja.nome else funcionario.loja.nome
            valores_por_loja[loja_id] = {
                'id': loja_id,
                'nome': nome_loja,
                'logo': funcionario.loja.logo.url if funcionario.loja.logo else '/static/img/default-store.png',
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
    Calcula o ranking dos atendentes baseado nos agendamentos que resultaram em atendimento em loja
    usando o período da meta ativa do INSS
    """
    print("\n----- Iniciando get_tabela_ranking -----\n")
    
    hoje = timezone.now().date()
    
    # Calcula o primeiro e o último dia da semana atual
    primeiro_dia_semana = hoje - timedelta(days=hoje.weekday())  # Domingo
    ultimo_dia_semana = primeiro_dia_semana + timedelta(days=6)  # Sábado

    print(f"Período do ranking: {primeiro_dia_semana} até {ultimo_dia_semana}")
    
    # Busca todos os agendamentos sem filtros
    agendamentos = Agendamento.objects.all().select_related('atendente_agendou')  # Otimiza a consulta
    print(f"Total de agendamentos encontrados: {agendamentos.count()}")

    # Agrupa agendamentos por atendente
    ranking_por_atendente = {}
    
    for agendamento in agendamentos:
        atendente = agendamento.atendente_agendou
        if atendente not in ranking_por_atendente:
            ranking_por_atendente[atendente] = {
                'funcionario': atendente,
                'nome': atendente.nome,
                'foto': atendente.foto.url if atendente.foto else None,
                'total_agendamentos': 0,
                'confirmados': 0,
                'fechamentos': 0,
            }
        
        ranking_por_atendente[atendente]['total_agendamentos'] += 1

    # Filtra agendamentos dentro do intervalo de datas
    agendamentos_data_range = Agendamento.objects.filter(
        dia_agendado__date__gte=primeiro_dia_semana,
        dia_agendado__date__lte=ultimo_dia_semana,
        atendente_agendou__isnull=False,    # Apenas agendamentos com atendente definido
        tabulacao_atendente__isnull=False    # Apenas agendamentos com tabulação atendente não vazia
    ).select_related('atendente_agendou')  # Otimiza a consulta

    print(f"Total de agendamentos no intervalo de datas: {agendamentos_data_range.count()}")

    # Calcula percentual de confirmação e efetividade
    ranking_data = []
    for atendente, dados in ranking_por_atendente.items():
        total_agendamentos = dados['total_agendamentos']
        print(f"Total de agendamentos para {dados['nome']}: {total_agendamentos}")

        # Passo 3: Conte os Agendamentos Confirmados pelo Atendente
        agem_confi_atend = sum(1 for agendamento in agendamentos_data_range if agendamento.atendente_agendou == atendente and agendamento.tabulacao_atendente == 'CONFIRMADO')
        print(f"Agendamentos confirmados pelo atendente {dados['nome']}: {agem_confi_atend}")

        # Passo 4: Conte os Agendamentos Confirmados e Fechados pelo Vendedor
        agem_fechado = sum(1 for agendamento in agendamentos_data_range if agendamento.atendente_agendou == atendente and agendamento.tabulacao_atendente == 'CONFIRMADO' and agendamento.tabulacao_vendedor)
        print(f"Agendamentos fechados pelo atendente {dados['nome']}: {agem_fechado}")

        # Passo 5: Calcule o Percentual de Efetividade
        percentual_efetividade = (100 * agem_fechado / agem_confi_atend) if agem_confi_atend > 0 else 0
        print(f"Percentual de efetividade para {dados['nome']}: {percentual_efetividade}%")

        ranking_data.append({
            'posicao': len(ranking_data) + 1,  # Posição no ranking
            'foto': dados['foto'],
            'nome': dados['nome'],
            'percentual_conf': round((agem_confi_atend / total_agendamentos * 100), 2) if total_agendamentos > 0 else 0,
            'percentual_conf_str': f"{agem_confi_atend}/{total_agendamentos}",  # Formato "confirmados/total"
            'percentual_efetividade': round(percentual_efetividade, 2)
        })

    # Ordena o ranking por percentual de efetividade (decrescente)
    ranking_data.sort(key=lambda x: x['percentual_efetividade'], reverse=True)
    
    print(f"Dados do ranking calculados para {len(ranking_data)} atendentes")
    
    # Log para debug dos percentuais
    for dados in ranking_data:
        print(f"Atendente: {dados['nome']}")
        print(f"Percentual de Confirmação: {dados['percentual_conf_str']} ({dados['percentual_conf']}%)")
        print(f"Percentual de Efetividade: {dados['percentual_efetividade']}%")
        print("---")
    
    print("\n----- Finalizando get_tabela_ranking -----\n")
    
    return {
        'ranking_data': ranking_data,
        'periodo': {
            'inicio': primeiro_dia_semana,
            'fim': ultimo_dia_semana
        },
        'total_agendamentos': agendamentos.count()
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

