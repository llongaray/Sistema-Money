# Importações padrão do Django
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils import timezone
from django.db.models import Count, Sum, F, Q
from django.db.models.functions import Coalesce, TruncDate
from django.conf import settings

# Importações de modelos
from .models import *
from apps.siape.models import *
from apps.funcionarios.models import *

# Importações de formulários
from .forms import *

# Importações da biblioteca padrão Python
from datetime import datetime, date  # Adicionando a importação de date
import os
import json

# Funções de visualização e renderização
from django.db.models import F
from django.utils import timezone

def calcular_status_dias(agendamento, hoje):
    if agendamento.tabulacao_vendedor:
        return agendamento.tabulacao_vendedor
    
    # Converter 'hoje' para datetime se for uma data
    if isinstance(hoje, date):
        hoje = timezone.make_aware(datetime.combine(hoje, datetime.min.time()))
    
    # Garantir que agendamento.dia_agendado seja aware
    if timezone.is_naive(agendamento.dia_agendado):
        agendamento.dia_agendado = timezone.make_aware(agendamento.dia_agendado)
    
    dias_diferenca = (agendamento.dia_agendado.date() - hoje.date()).days
    if dias_diferenca > 0:
        return f"Faltam {dias_diferenca} dias"
    elif dias_diferenca < 0:
        if agendamento.tabulacao_vendedor is None:
            return f"Atrasado há {abs(dias_diferenca)} dias"
        else:
            return agendamento.tabulacao_vendedor
    else:
        return "Hoje"
    
# Funções auxiliares e de processamento
def post_venda_tabulacao(form_data, funcionario):
    '''Processa a tabulação de vendas para um agendamento.'''
    print("\n\n----- Iniciando post_venda_tabulacao -----\n")
    mensagem = {'texto': '', 'classe': ''}

    print("\n\nIniciando o processamento da tabulação de vendas.")
    print(f"\nDados recebidos: {form_data}")

    try:
        # Extraindo dados do formulário para um dicionário
        tabulacao_data = {
            'agendamento_id': form_data.get('agendamento_id'),
            'vendedor_id': form_data.get('vendedor_id'),
            'tabulacao_vendedor': form_data.get('tabulacao_vendedor'),
            'observacao': form_data.get('observacao'),
            'nome_cliente': form_data.get('nome_cliente'),
            'cpf_cliente': form_data.get('cpf_cliente'),
            'numero_cliente': form_data.get('numero_cliente'),
            'dia_agendado': form_data.get('dia_agendado'),
            'tabulacao_atendente': form_data.get('tabulacao_atendente')
        }
        if not tabulacao_data['agendamento_id']:
            print("Agendamento ID está vazio. O formulário não será processado.")
            mensagem = {'texto': 'Erro: O ID do agendamento não pode estar vazio.', 'classe': 'error'}
            return mensagem  # Ou outra ação apropriada

        print(f"\nDados extraídos para processamento: {tabulacao_data}")

        # Obtém o agendamento correspondente
        agendamento = Agendamento.objects.get(id=tabulacao_data['agendamento_id'])
        print(f"Agendamento encontrado: {agendamento}")

        # Verifica e atualiza a tabulacao_atendente se necessário
        if agendamento.tabulacao_atendente != 'CONFIRMADO':
            agendamento.tabulacao_atendente = 'CONFIRMADO'
            print("Tabulação do atendente atualizada para CONFIRMADO")

        # Obtém o vendedor responsável
        vendedor_loja = Funcionario.objects.get(id=tabulacao_data['vendedor_id'])
        print(f"Vendedor encontrado: {vendedor_loja}")

        # Atualiza os dados de venda no agendamento
        agendamento.vendedor_loja = vendedor_loja
        agendamento.tabulacao_vendedor = tabulacao_data['tabulacao_vendedor']

        if tabulacao_data.get('observacao'):
            agendamento.observacao_vendedor = tabulacao_data['observacao']

        print("Dados do agendamento atualizados.")

        # Salva as alterações
        agendamento.save()
        print("Agendamento salvo com sucesso.")

        # Criar log de alteração
        LogAlteracao.objects.create(
            agendamento_id=str(agendamento.id),
            mensagem=f"Tabulação de vendas atualizada. Vendedor: {vendedor_loja.nome}, Tabulação: {tabulacao_data['tabulacao_vendedor']}. Tabulação do atendente atualizada para CONFIRMADO.",
            status=True,
            funcionario=funcionario
        )

        mensagem['texto'] = 'Tabulação de vendas atualizada com sucesso!'
        mensagem['classe'] = 'success'

    except Agendamento.DoesNotExist:
        mensagem['texto'] = 'Erro: Agendamento não encontrado.'
        mensagem['classe'] = 'error'
        print("Erro: Agendamento não encontrado.")
        LogAlteracao.objects.create(
            agendamento_id="N/A",
            mensagem=f"Erro ao atualizar tabulação de vendas: Agendamento não encontrado",
            status=False,
            funcionario=funcionario
        )
    except Funcionario.DoesNotExist:
        mensagem['texto'] = 'Erro: Vendedor não encontrado.'
        mensagem['classe'] = 'error'
        print("Erro: Vendedor não encontrado.")
        LogAlteracao.objects.create(
            agendamento_id=str(agendamento.id) if 'agendamento' in locals() else "N/A",
            mensagem=f"Erro ao atualizar tabulação de vendas: Vendedor não encontrado",
            status=False,
            funcionario=funcionario
        )
    except Exception as e:
        mensagem['texto'] = f'Erro ao atualizar a tabulação: {str(e)}'
        mensagem['classe'] = 'error'
        print(f"Erro ao atualizar a tabulação: {str(e)}")
        LogAlteracao.objects.create(
            agendamento_id=str(agendamento.id) if 'agendamento' in locals() else "N/A",
            mensagem=f"Erro ao atualizar tabulação de vendas: {str(e)}",
            status=False,
            funcionario=funcionario
        )

    print(f"Mensagem final: {mensagem}\n\n")
    print("\n----- Finalizando post_venda_tabulacao -----\n")
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
            # Apenas atualiza a tabulação
            dados_atualizacao['tabulacao_atendente'] = 'CONFIRMADO'
        
        elif form_data['tabulacao_atendente'] == 'REAGENDADO':
            # Atualiza a tabulação e a nova data
            dados_atualizacao['tabulacao_atendente'] = 'REAGENDADO'
            if form_data.get('nova_dia_agendado'):
                nova_dia_agendado = datetime.strptime(form_data['nova_dia_agendado'], '%Y-%m-%d').date()
                dados_atualizacao['dia_agendado'] = timezone.make_aware(datetime.combine(nova_dia_agendado, hora_atual))

        elif form_data['tabulacao_atendente'] == 'DESISTIU':
            # Atualiza a tabulação e a observação
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

def post_agendamento(form_data, funcionario):
    '''Processa o agendamento baseado nos dados recebidos.'''
    print("\n\n----- Iniciando post_agendamento -----\n")
    print(f'\n\n ------------------------POST Agendamento ABERTO!!------------------------\n\n')
    mensagem = {'texto': '', 'classe': ''}

    try:
        dia_agendado = form_data.get('dia_agendado')
        print(f"Data recebida: {dia_agendado}")

        # Converter a data para datetime e adicionar a hora atual
        if isinstance(dia_agendado, str):
            dia_agendado = datetime.strptime(dia_agendado, '%Y-%m-%d').date()
        
        hora_atual = timezone.now().time()
        dia_agendado_com_hora = timezone.make_aware(datetime.combine(dia_agendado, hora_atual))

        agendamento_data = {
            'nome_cliente': form_data.get('nome_cliente'),
            'cpf_cliente': form_data.get('cpf_cliente'),
            'numero_cliente': form_data.get('numero_cliente'),
            'dia_agendado': dia_agendado_com_hora,
            'loja_agendada_id': form_data.get('loja_agendada'),
            'atendente_agendou_id': form_data.get('atendente_agendou')
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

def get_all_forms_and_objects(request_post):
<<<<<<< HEAD
    print("\n\n----- Iniciando get_all_forms_and_objects -----\n")
    
    hoje = timezone.now().date()
    
    try:
        # Obtém informações do funcionário logado
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
    if request_post.user.is_superuser or nivel_cargo == 'COORDENADOR':
        funcionarios = Funcionario.objects.all()
    elif nivel_cargo == 'GERENTE':
        funcionarios = Funcionario.objects.filter(loja=loja_funcionario)
    else:
        funcionarios = Funcionario.objects.filter(id=funcionario_logado.id)

    # Configuração de formulários
    form_agendamento = AgendamentoForm(funcionarios=funcionarios)
    form_confirmacao = ConfirmacaoAgendamentoForm()

    # Lista de lojas
    if request_post.user.is_superuser or nivel_cargo == 'COORDENADOR':
        lojas = Loja.objects.all()
    elif nivel_cargo == 'GERENTE':
        lojas = Loja.objects.filter(id=loja_funcionario.id)
    else:
        lojas = Loja.objects.filter(id=loja_funcionario.id) if loja_funcionario else Loja.objects.none()
    
    lojas_dicionario = [{'id': str(loja.id), 'nome': loja.nome} for loja in lojas]

    # Lista de vendedores
    vendedores_lista_clientes = [{'id': f.id, 'nome': f.nome} for f in funcionarios]

    # Agendamentos query com filtros por nível
    agendamentos_base_query = Agendamento.objects.select_related(
        'loja_agendada', 
        'atendente_agendou'
    )

    if request_post.user.is_superuser or nivel_cargo == 'COORDENADOR':
        pass
    elif nivel_cargo == 'GERENTE':
        agendamentos_base_query = agendamentos_base_query.filter(loja_agendada=loja_funcionario)
    elif funcionario_logado:
        agendamentos_base_query = agendamentos_base_query.filter(atendente_agendou=funcionario_logado)
    else:
        agendamentos_base_query = agendamentos_base_query.none()

    # Clientes na loja hoje
    clientes_loja = agendamentos_base_query.annotate(
=======
    '''
    Função principal que retorna todos os formulários e objetos necessários para a view all_forms.
    Processa permissões de usuário e retorna dados filtrados baseados no nível de acesso.
    '''
    print("\n\n----- Iniciando get_all_forms_and_objects -----\n")
    
    # ----- Verificação de Permissões e Acesso -----
    if request_post.user.is_superuser:
        print("Usuário é superuser - mostrando todos os funcionários")
        funcionarios = Funcionario.objects.all()
    else:
        print("Usuário não é superuser - verificando funcionário associado")
        try:
            funcionario = Funcionario.objects.get(usuario_id=request_post.user.id)
            funcionarios = Funcionario.objects.filter(id=funcionario.id)
            print(f"Funcionário encontrado: {funcionario.nome}")
        except Funcionario.DoesNotExist:
            print("Nenhum funcionário associado ao usuário")
            funcionarios = Funcionario.objects.none()

    # ----- Configuração Inicial de Dados -----
    lojas = Loja.objects.all().values('id', 'nome')
    lojas_dicionario = [{'id': str(loja['id']), 'nome': loja['nome']} for loja in lojas]

    # Inicialização de formulários
    form_agendamento = AgendamentoForm(funcionarios=funcionarios)
    form_confirmacao = ConfirmacaoAgendamentoForm()
    
    # ----- Lista de Vendedores -----
    if request_post.user.is_superuser:
        vendedores_lista_clientes = [{'id': f.id, 'nome': f.nome} for f in funcionarios]
    else:
        try:
            funcionario_logado = Funcionario.objects.get(usuario_id=request_post.user.id)
            vendedores_lista_clientes = [{'id': funcionario_logado.id, 'nome': funcionario_logado.nome}]
        except Funcionario.DoesNotExist:
            vendedores_lista_clientes = []

    hoje = timezone.now().date()

    # ----- Funções Auxiliares -----
    def processar_agendamentos(queryset, filtros=None, incluir_status=True):
        '''Processa uma queryset de agendamentos aplicando filtros opcionais'''
        if filtros:
            queryset = queryset.filter(**filtros)
        return [criar_dicionario_agendamento(a, hoje, incluir_status) for a in queryset]

    # ----- Processamento de Agendamentos da Loja -----
    agendamentos_loja = Agendamento.objects.annotate(
>>>>>>> 8c9bdec505c96e6d36a28aa15689b2584d325ac5
        apenas_data=TruncDate('dia_agendado')
    ).filter(
        tabulacao_atendente='CONFIRMADO',
        apenas_data=hoje
<<<<<<< HEAD
    )

    clientes_loja_dicionario = [{
        'id': a.id,
        'nome_cliente': a.nome_cliente,
        'cpf_cliente': a.cpf_cliente,
        'numero_cliente': a.numero_cliente,
        'dia_agendado_completo': a.dia_agendado.strftime('%Y-%m-%d %H:%M:%S'),
        'dia_agendado': a.dia_agendado.strftime('%Y-%m-%d'),
        'tabulacao_atendente': a.tabulacao_atendente,
        'atendente_agendou': a.atendente_agendou.nome if a.atendente_agendou else '',
        'loja_agendada': a.loja_agendada.nome if a.loja_agendada else ''
    } for a in clientes_loja]

    # Agendamentos para confirmação
    agendamentos_confirmacao = agendamentos_base_query.filter(
        Q(tabulacao_atendente='AGENDADO') |
        Q(tabulacao_atendente='REAGENDADO')
    ).order_by('dia_agendado')

    agendamentos_confirmacao_list = [{
        'id': a.id,
        'nome_cliente': a.nome_cliente,
        'cpf_cliente': a.cpf_cliente,
        'numero_cliente': a.numero_cliente,
        'dia_agendado_completo': a.dia_agendado.strftime('%Y-%m-%d %H:%M:%S'),
        'dia_agendado': a.dia_agendado.strftime('%d/%m/%Y'),
        'dia_agendado_form': a.dia_agendado.strftime('%Y-%m-%d'),
        'atendente_nome': a.atendente_agendou.nome if a.atendente_agendou else None,
        'loja_nome': a.loja_agendada.nome if a.loja_agendada else None,
        'tabulacao_atendente': a.tabulacao_atendente,
        'tabulacao_vendedor': a.tabulacao_vendedor,
        'status_dias': calcular_status_dias(a, hoje)
    } for a in agendamentos_confirmacao]

    # Agendamentos reagendados
    agendamentos_reagendados = agendamentos_base_query.filter(
        tabulacao_atendente='REAGENDADO',
        tabulacao_vendedor__isnull=True
    )

    agendamentos_reagendados_dicionario = [{
        'id': a.id,
        'nome_cliente': a.nome_cliente,
        'cpf_cliente': a.cpf_cliente,
        'numero_cliente': a.numero_cliente,
        'dia_agendado': a.dia_agendado.strftime('%Y-%m-%d %H:%M:%S'),
        'atendente_nome': a.atendente_agendou.nome if a.atendente_agendou else '',
        'loja_nome': a.loja_agendada.nome if a.loja_agendada else '',
        'tabulacao_atendente': a.tabulacao_atendente or '',
        'status_dias': calcular_status_dias(a, hoje)
    } for a in agendamentos_reagendados]

    # Todos os agendamentos
    todos_agendamentos = agendamentos_base_query.all()
    todos_agendamentos_dicionario = [{
        'id': a.id,
        'nome_cliente': a.nome_cliente,
        'cpf_cliente': a.cpf_cliente,
        'numero_cliente': a.numero_cliente,
        'dia_agendado': a.dia_agendado.strftime('%Y-%m-%d %H:%M:%S'),
        'atendente_nome': a.atendente_agendou.nome if a.atendente_agendou else '',
        'loja_nome': a.loja_agendada.nome if a.loja_agendada else '',
        'tabulacao_atendente': a.tabulacao_atendente or '',
        'tabulacao_vendedor': a.tabulacao_vendedor or '',
        'status_dias': calcular_status_dias(a, hoje)
    } for a in todos_agendamentos]

    print("\n----- Finalizando get_all_forms_and_objects -----\n")
    
=======
    ).select_related('loja_agendada', 'atendente_agendou')

    clientes_loja_dicionario = []
    for agendamento in agendamentos_loja:
        cliente_dict = {
            'id': agendamento.id,
            'nome_cliente': agendamento.nome_cliente,
            'cpf_cliente': agendamento.cpf_cliente,
            'numero_cliente': agendamento.numero_cliente,
            'dia_agendado_completo': agendamento.dia_agendado.strftime('%Y-%m-%d %H:%M:%S'),
            'dia_agendado': agendamento.dia_agendado.strftime('%Y-%m-%d'),
            'tabulacao_atendente': agendamento.tabulacao_atendente,
            'atendente_agendou': agendamento.atendente_agendou.nome if agendamento.atendente_agendou else '',
            'loja_agendada': agendamento.loja_agendada.nome if agendamento.loja_agendada else ''
        }
        clientes_loja_dicionario.append(cliente_dict)

    # ----- Processamento de Agendamentos para Confirmação -----
    agendamentos_confirmacao = Agendamento.objects.filter(
        Q(tabulacao_atendente='AGENDADO') |
        Q(tabulacao_atendente='REAGENDADO')
    ).select_related('loja_agendada', 'atendente_agendou').order_by('dia_agendado')
    
    agendamentos_confirmacao_list = []
    for agendamento in agendamentos_confirmacao:
        agendamento_dict = {
            'id': agendamento.id,
            'nome_cliente': agendamento.nome_cliente,
            'cpf_cliente': agendamento.cpf_cliente,
            'numero_cliente': agendamento.numero_cliente,
            'dia_agendado_completo': agendamento.dia_agendado.strftime('%Y-%m-%d %H:%M:%S'),
            'dia_agendado': agendamento.dia_agendado.strftime('%d/%m/%Y'),
            'dia_agendado_form': agendamento.dia_agendado.strftime('%Y-%m-%d'),
            'atendente_nome': agendamento.atendente_agendou.nome if agendamento.atendente_agendou else None,
            'loja_nome': agendamento.loja_agendada.nome if agendamento.loja_agendada else None,
            'tabulacao_atendente': agendamento.tabulacao_atendente,
            'tabulacao_vendedor': agendamento.tabulacao_vendedor,
            'status_dias': calcular_status_dias(agendamento, hoje)
        }
        agendamentos_confirmacao_list.append(agendamento_dict)

    # Lista de agendamentos para edição
    agendamentos_edicao_list = agendamentos_confirmacao_list

    # ----- Processamento de Agendamentos Reagendados -----
    agendamentos_reagendados = Agendamento.objects.filter(
        tabulacao_atendente='REAGENDADO',
        tabulacao_vendedor__isnull=True
    ).select_related('loja_agendada', 'atendente_agendou')
    agendamentos_reagendados_dicionario = processar_agendamentos(agendamentos_reagendados)

    # ----- Processamento de Todos os Agendamentos -----
    todos_agendamentos = Agendamento.objects.all().select_related('loja_agendada', 'atendente_agendou')
    todos_agendamentos_dicionario = []
    for agendamento in todos_agendamentos:
        agendamento_dict = criar_dicionario_agendamento(agendamento, hoje, incluir_status=True)
        agendamento_dict['dia_agendado'] = agendamento.dia_agendado.strftime('%Y-%m-%d %H:%M:%S')
        todos_agendamentos_dicionario.append(agendamento_dict)
    # Todos os agendamentos
    todos_agendamentos = Agendamento.objects.all().select_related('loja_agendada', 'atendente_agendou')
    todos_agendamentos_dicionario = []
    for agendamento in todos_agendamentos:
        agendamento_dict = {
            'id': agendamento.id,
            'nome_cliente': agendamento.nome_cliente,
            'cpf_cliente': agendamento.cpf_cliente,
            'numero_cliente': agendamento.numero_cliente,
            'dia_agendado': agendamento.dia_agendado.strftime('%Y-%m-%d %H:%M:%S'),
            'atendente_nome': agendamento.atendente_agendou.nome if agendamento.atendente_agendou else '',
            'loja_nome': agendamento.loja_agendada.nome if agendamento.loja_agendada else '',
            'tabulacao_atendente': agendamento.tabulacao_atendente or '',
            'tabulacao_vendedor': agendamento.tabulacao_vendedor or '',
            'status_dias': calcular_status_dias(agendamento, timezone.now())
        }
        todos_agendamentos_dicionario.append(agendamento_dict)

    print("\n----- Finalizando get_all_forms_and_objects -----\n")
    
    # ----- Retorno Final -----
>>>>>>> 8c9bdec505c96e6d36a28aa15689b2584d325ac5
    return {
        'form_agendamento': form_agendamento,
        'form_confirmacao': form_confirmacao,
        'funcionarios': funcionarios,
        'lojas': lojas_dicionario,
        'clientes_loja': clientes_loja_dicionario,
        'vendedores_lista_clientes': vendedores_lista_clientes,
        'agendamentos_confirmacao': agendamentos_confirmacao_list,
<<<<<<< HEAD
        'agendamentos_edicao': agendamentos_confirmacao_list,
        'agendamentos_reagendamento': agendamentos_reagendados_dicionario,
        'todos_agendamentos': todos_agendamentos_dicionario,
        'funcionario_logado': funcionario_logado,
        'nivel_cargo': nivel_cargo,
        'loja_funcionario': loja_funcionario
=======
        'agendamentos_edicao': agendamentos_edicao_list,
        'agendamentos_reagendamento': agendamentos_reagendados_dicionario,
        'todos_agendamentos': todos_agendamentos_dicionario,
>>>>>>> 8c9bdec505c96e6d36a28aa15689b2584d325ac5
    }

@login_required
def render_all_forms(request):
<<<<<<< HEAD
    """Renderiza a página com todos os formulários"""
=======
>>>>>>> 8c9bdec505c96e6d36a28aa15689b2584d325ac5
    print("\n\n----- Iniciando render_all_forms -----\n")
    
    mensagem = {'texto': '', 'classe': ''}

    try:
        funcionario_logado = Funcionario.objects.get(usuario_id=request.user.id)
        print(f"\nFuncionário logado: {funcionario_logado.nome}")
    except Funcionario.DoesNotExist:
        funcionario_logado = None
        print("\n\nFuncionário não encontrado.")

<<<<<<< HEAD
    # Processamento de formulários POST
=======
    print("\nVerificando se o request é POST...")
>>>>>>> 8c9bdec505c96e6d36a28aa15689b2584d325ac5
    if request.method == 'POST':
        print("\nRequest é POST. Processando formulário...")
        form_type = request.POST.get('form_type')
        print(f"\nTipo de formulário: {form_type}")

        if form_type == 'agendamento':
<<<<<<< HEAD
            print("\nProcessando formulário de agendamento...")
=======
            print("\nProcessando formul��rio de agendamento...")
            # Extraindo os dados diretamente do request.POST
>>>>>>> 8c9bdec505c96e6d36a28aa15689b2584d325ac5
            agendamento_data = {
                'nome_cliente': request.POST.get('nome_cliente'),
                'cpf_cliente': request.POST.get('cpf_cliente'),
                'numero_cliente': request.POST.get('numero_cliente'),
                'dia_agendado': request.POST.get('dia_agendado'),
<<<<<<< HEAD
                'loja_agendada': request.POST.get('loja_agendada'),
                'atendente_agendou': request.POST.get('atendente_agendou')
            }
            print(f"Dados recebidos: {agendamento_data}")

            if all([agendamento_data['nome_cliente'], 
                   agendamento_data['cpf_cliente'], 
                   agendamento_data['numero_cliente']]):
                mensagem = post_agendamento(agendamento_data, funcionario_logado)
                print("Agendamento processado.")
            else:
                mensagem = {
                    'texto': 'Erro no formulário de agendamento. Preencha todos os campos obrigatórios.',
                    'classe': 'error'
                }
=======
                'loja_agendada': request.POST.get('loja_agendada'),  # ID da loja
                'atendente_agendou': request.POST.get('atendente_agendou')  # ID do atendente
            }
            
            # Exibindo os dados recebidos
            print(f"Dados recebidos: {agendamento_data}")

            # Validando os dados (aqui você pode adicionar a lógica de validação que preferir)
            if agendamento_data['nome_cliente'] and agendamento_data['cpf_cliente'] and agendamento_data['numero_cliente']:
                mensagem = post_agendamento(agendamento_data, funcionario_logado)  # Passa os dados para o processamento
                print("Agendamento processado.")
            else:
                mensagem = {'texto': 'Erro no formulário de agendamento. Preencha todos os campos obrigatórios.', 'classe': 'error'}
>>>>>>> 8c9bdec505c96e6d36a28aa15689b2584d325ac5
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
<<<<<<< HEAD
=======
            
>>>>>>> 8c9bdec505c96e6d36a28aa15689b2584d325ac5
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
<<<<<<< HEAD
=======
            # Extraindo os dados diretamente do request.POST
>>>>>>> 8c9bdec505c96e6d36a28aa15689b2584d325ac5
            lista_clientes_data = {
                'agendamento_id': request.POST.get('agendamento_id'),
                'nome_cliente': request.POST.get('nome_cliente'),
                'cpf_cliente': request.POST.get('cpf_cliente'),
                'numero_cliente': request.POST.get('numero_cliente'),
                'dia_agendado': request.POST.get('dia_agendado'),
                'tabulacao_atendente': request.POST.get('tabulacao_atendente'),
                'tabulacao_vendedor': request.POST.get('tabulacao_vendedor'),
<<<<<<< HEAD
                'vendedor_id': request.POST.get('vendedor_id'),
                'observacao': request.POST.get('observacao')
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
=======
                'vendedor_id': request.POST.get('vendedor_id'),  # Incluindo vendedor_id
                'observacao': request.POST.get('observacao')  # Incluindo observação
            }

            # Exibindo os dados recebidos
            print(f"Dados recebidos: {lista_clientes_data}")

            # Validando os dados
            if lista_clientes_data['agendamento_id'] and lista_clientes_data['tabulacao_vendedor']:
                print('Entrou no if do list!')
                # Chama a função para processar a venda ou tabulação
                mensagem = post_venda_tabulacao(lista_clientes_data, funcionario_logado)  # Passa os dados para o processamento
                print("Tabulação processada.")
            else:
                mensagem = {'texto': 'Erro no formulário de lista de clientes. Preencha todos os campos obrigatórios.', 'classe': 'error'}
                print("Erro no formulário de lista de clientes.")

>>>>>>> 8c9bdec505c96e6d36a28aa15689b2584d325ac5
    else:
        print("\nRequest não é POST. Carregando formulários vazios...")

    print("\nTentando chamar get_all_forms_and_objects...")
    context_data = get_all_forms_and_objects(request)
    print("\nRetornou de get_all_forms_and_objects.")

<<<<<<< HEAD
    # Atualiza o contexto com mensagem e funcionário logado
=======
>>>>>>> 8c9bdec505c96e6d36a28aa15689b2584d325ac5
    context_data.update({
        'mensagem': mensagem,
        'funcionario_logado': funcionario_logado,
    })

<<<<<<< HEAD
    # Logs para debug
    print("\nContexto dos dados obtidos:")
    if 'funcionarios' in context_data:
        print(f"\nFuncionários: {[f.nome for f in context_data['funcionarios']]}\n")
    else:
        print("\nNenhum funcionário encontrado no contexto\n")
    
    print(f"Clientes Confirmados: {context_data.get('clientes_loja', [])}\n")
=======
    print("\nContexto dos dados obtidos:")
    print(f'\n{context_data}\n')

    print(f"\nFuncionrios: {[funcionario.nome for funcionario in context_data['funcionarios']]}\n")
    print(f"Clientes Confirmados: {context_data['clientes_loja']}\n")
>>>>>>> 8c9bdec505c96e6d36a28aa15689b2584d325ac5

    print("\n----- Finalizando render_all_forms -----\n")
    return render(request, 'inss/all_forms.html', context_data)

def get_cards(periodo='mes'):
<<<<<<< HEAD
    print("\n----- Iniciando get_cards -----\n")
    
    hoje = timezone.now()
    
    # Busca a meta geral ativa
    meta_geral = RegisterMeta.objects.filter(
        tipo='GERAL',
        status=True,
        range_data_inicio__lte=hoje.date(),
        range_data_final__gte=hoje.date()
    ).first()
    
    # Se encontrou meta geral ativa, usa o range de datas dela
    if meta_geral:
        primeiro_dia = meta_geral.range_data_inicio
        ultimo_dia = meta_geral.range_data_final
    else:
        # Se não encontrou meta, usa o mês atual
        primeiro_dia = hoje.replace(day=1)
        ultimo_dia = (hoje.replace(day=1, month=hoje.month + 1) - timezone.timedelta(days=1))
=======
    """
    Calcula os dados para os cards: faturamento total, quantidade de vendas e agendamentos
    """
    print("\n----- Iniciando get_cards -----\n")
    
    hoje = timezone.now()
    primeiro_dia = hoje.replace(day=1)
    ultimo_dia = (hoje.replace(day=1, month=hoje.month + 1) - timezone.timedelta(days=1))
>>>>>>> 8c9bdec505c96e6d36a28aa15689b2584d325ac5
    
    # Busca todos os registros de valores no período
    valores_range = RegisterMoney.objects.filter(
        data__range=[primeiro_dia, ultimo_dia]
    )
    
    # Obtém os IDs dos funcionários com registros
    funcionarios_ids = valores_range.values_list('funcionario_id', flat=True).distinct()
    
    # Busca todos os funcionários e separa por departamento
    funcionarios = Funcionario.objects.filter(
        id__in=funcionarios_ids
    ).select_related('departamento', 'loja')
    
    # Inicializa variáveis para cálculo
<<<<<<< HEAD
    faturamento_total = Decimal('0')
    
    # Calcula faturamento total
=======
    faturamento_inss = Decimal('0')
    faturamento_total = Decimal('0')
    
    # Calcula faturamentos
>>>>>>> 8c9bdec505c96e6d36a28aa15689b2584d325ac5
    for venda in valores_range:
        funcionario = next((f for f in funcionarios if f.id == venda.funcionario_id), None)
        if not funcionario:
            continue
            
        valor_venda = Decimal(str(venda.valor_est))
        faturamento_total += valor_venda
<<<<<<< HEAD
=======
        
        if funcionario.departamento and funcionario.departamento.grupo.name == 'INSS':
            faturamento_inss += valor_venda
    
    # Calcula o percentual do INSS em relação ao total
    percentual_inss = round((faturamento_inss / faturamento_total * 100) if faturamento_total else 0, 2)
>>>>>>> 8c9bdec505c96e6d36a28aa15689b2584d325ac5
    
    # Busca quantidade de vendas (agendamentos com FECHOU NEGOCIO)
    qtd_vendas = Agendamento.objects.filter(
        dia_agendado__date__range=[primeiro_dia, ultimo_dia],
        tabulacao_vendedor='FECHOU NEGOCIO'
    ).count()
    
    # Busca quantidade de agendamentos confirmados
    qtd_agendamentos = Agendamento.objects.filter(
        dia_agendado__date__range=[primeiro_dia, ultimo_dia],
        tabulacao_atendente='CONFIRMADO'
    ).count()
    
<<<<<<< HEAD
    # Calcula o percentual em relação à meta
    if meta_geral and meta_geral.valor:
        percentual_meta = round((faturamento_total / meta_geral.valor * 100), 2)
    else:
        percentual_meta = 0
    
    # Formata o valor monetário
    valor_formatado = f"R$ {faturamento_total:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')
    
    # Prepara o contexto com os dados formatados
    context_data = {
        'valor_total': valor_formatado,
        'percentual': percentual_meta,
        'qtd_vendas': qtd_vendas,
        'qtd_agendamentos': qtd_agendamentos,
        'periodo': {
            'inicio': primeiro_dia.date() if isinstance(primeiro_dia, datetime) else primeiro_dia,
            'fim': ultimo_dia.date() if isinstance(ultimo_dia, datetime) else ultimo_dia
=======
    # Formata o valor monetário
    valor_formatado = f"R$ {faturamento_inss:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')
    
    # Prepara o contexto com os dados formatados
    context_data = {
        'valor_total': valor_formatado,  # Já inclui o R$
        'percentual': percentual_inss,   # Número puro, o % está no template
        'qtd_vendas': qtd_vendas,        # Número inteiro
        'qtd_agendamentos': qtd_agendamentos,  # Número inteiro
        'periodo': {
            'inicio': primeiro_dia.date(),
            'fim': ultimo_dia.date()
>>>>>>> 8c9bdec505c96e6d36a28aa15689b2584d325ac5
        }
    }
    
    print(f"Faturamento INSS: {context_data['valor_total']}")
<<<<<<< HEAD
    print(f"Percentual da Meta: {context_data['percentual']}%")
=======
    print(f"Percentual INSS: {context_data['percentual']}%")
>>>>>>> 8c9bdec505c96e6d36a28aa15689b2584d325ac5
    print(f"Quantidade de Vendas: {context_data['qtd_vendas']}")
    print(f"Quantidade de Agendamentos: {context_data['qtd_agendamentos']}")
    print("\n----- Finalizando get_cards -----\n")
    
    return context_data

def get_podium(periodo='mes'):
    """
    Calcula o pódio das lojas baseado nos valores registrados no RegisterMoney
    para funcionários do departamento INSS
    """
    print("\n----- Iniciando get_podium -----\n")
    
    hoje = timezone.now()
    primeiro_dia = hoje.replace(day=1)
    ultimo_dia = (hoje.replace(day=1, month=hoje.month + 1) - timezone.timedelta(days=1))
    
    # Busca todos os registros de valores no período
    valores_range = RegisterMoney.objects.filter(
        data__range=[primeiro_dia, ultimo_dia]
    )
    
    # Obtém os IDs dos funcionários com registros
    funcionarios_ids = valores_range.values_list('funcionario_id', flat=True).distinct()
    
    # Busca funcionários do departamento INSS
    funcionarios = Funcionario.objects.filter(
        id__in=funcionarios_ids,
        departamento__grupo__name='INSS'
    ).select_related('departamento', 'loja')
    
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
                'total_fechamentos': Decimal('0')
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
        # Formata o valor para exibição (R$ XX.XXX,XX)
        loja['total_fechamentos'] = f"R$ {loja['total_fechamentos']:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')

    print(f"Pódio calculado para o período: {primeiro_dia.date()} até {ultimo_dia.date()}")
    print(f"Total de lojas no pódio: {len(podium)}")
    print("\n----- Finalizando get_podium -----\n")
    
    return {
        'podium': podium,
        'periodo': {
            'inicio': primeiro_dia.date(),
            'fim': ultimo_dia.date()
        }
    }

def get_tabela_ranking(periodo='mes'):
    """
    Calcula o ranking dos atendentes baseado nos agendamentos que resultaram em atendimento em loja
    """
    print("\n----- Iniciando get_tabela_ranking -----\n")
    
    hoje = timezone.now().date()
<<<<<<< HEAD
    # Calcula o domingo da semana atual
    primeiro_dia = hoje - timezone.timedelta(days=hoje.weekday() + 1)
    # Calcula o sábado da semana atual
    ultimo_dia = primeiro_dia + timezone.timedelta(days=6)
    
    # Filtro para a semana atual
=======
    primeiro_dia = hoje.replace(day=1)
    ultimo_dia = (primeiro_dia + timezone.timedelta(days=32)).replace(day=1) - timezone.timedelta(days=1)
    
    # Filtro para o mês atual
>>>>>>> 8c9bdec505c96e6d36a28aa15689b2584d325ac5
    filtro_data = Q(
        dia_agendado__date__gte=primeiro_dia,
        dia_agendado__date__lte=ultimo_dia
    )

<<<<<<< HEAD
    # Busca agendamentos da semana atual
=======
    # Busca agendamentos do mês atual
>>>>>>> 8c9bdec505c96e6d36a28aa15689b2584d325ac5
    agendamentos = Agendamento.objects.filter(
        filtro_data,
        atendente_agendou__isnull=False    # Apenas agendamentos com atendente definido
    ).select_related('atendente_agendou')  # Otimiza a consulta

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
<<<<<<< HEAD
                'taxa_efetividade': 0,
                'percentual_conf': 0  # Inicializa o percentual de confirmação
            }
        
        # Ignora agendamentos com tabulação "NÃO QUIS OUVIR"
        if agendamento.tabulacao_vendedor == 'NÃO QUIS OUVIR':
            continue
            
=======
                'taxa_efetividade': 0
            }
        
>>>>>>> 8c9bdec505c96e6d36a28aa15689b2584d325ac5
        ranking_por_atendente[atendente]['total_agendamentos'] += 1
        
        # Conta confirmações e fechamentos
        if agendamento.tabulacao_atendente == 'CONFIRMADO':
            ranking_por_atendente[atendente]['confirmados'] += 1
            if agendamento.tabulacao_vendedor == 'FECHOU NEGOCIO':
                ranking_por_atendente[atendente]['fechamentos'] += 1

<<<<<<< HEAD
    # Calcula taxa de efetividade e percentual de confirmação
    ranking_data = []
    for dados in ranking_por_atendente.values():
        # Calcula o percentual de confirmação
        if dados['total_agendamentos'] > 0:
            dados['percentual_conf'] = round(
                (dados['confirmados'] / dados['total_agendamentos']) * 100
            )
        
=======
    # Calcula taxa de efetividade e filtra atendentes
    ranking_data = []
    for dados in ranking_por_atendente.values():
>>>>>>> 8c9bdec505c96e6d36a28aa15689b2584d325ac5
        # Só inclui atendentes com pelo menos 1 fechamento
        if dados['fechamentos'] > 0:
            # Calcula taxa de efetividade (fechamentos / confirmados)
            if dados['confirmados'] > 0:
                dados['taxa_efetividade'] = round(
                    (dados['fechamentos'] / dados['confirmados']) * 100, 2
                )
            ranking_data.append(dados)

    # Ordena o ranking por número de fechamentos (decrescente)
    ranking_data.sort(key=lambda x: x['fechamentos'], reverse=True)
    
    print(f"Dados do ranking calculados para {len(ranking_data)} atendentes")
    print(f"Período: {primeiro_dia} até {ultimo_dia}")
<<<<<<< HEAD
    
    # Log para debug dos percentuais
    for dados in ranking_data:
        print(f"Atendente: {dados['nome']}")
        print(f"Total Agendamentos: {dados['total_agendamentos']}")
        print(f"Confirmados: {dados['confirmados']}")
        print(f"Percentual de Confirmação: {dados['percentual_conf']}%")
        print("---")
    
=======
>>>>>>> 8c9bdec505c96e6d36a28aa15689b2584d325ac5
    print("\n----- Finalizando get_tabela_ranking -----\n")
    
    return {
        'ranking_data': ranking_data,
        'periodo': {
            'inicio': primeiro_dia,
            'fim': ultimo_dia
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
<<<<<<< HEAD
    # Log para debug do percentual_conf
    for dados in dados_ranking['ranking_data']:
        print(f"Percentual de confirmação para {dados['nome']}: {dados.get('percentual_conf', 0)}%")
=======
    
>>>>>>> 8c9bdec505c96e6d36a28aa15689b2584d325ac5
    context_data = {
        'ranking_data': dados_ranking['ranking_data'],
        'periodo': dados_ranking['periodo'],
        'total_agendamentos': dados_ranking['total_agendamentos'],
        'podium': dados_podium['podium'],
        'cards': dados_cards
    }
    
    print("\n----- Finalizando get_ranking -----\n")
    return context_data

def render_ranking(request):
    """
    Renderiza a página de ranking com os dados necessários
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



