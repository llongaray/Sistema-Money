from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Sum, OuterRef, Subquery
from django.db import transaction
from django.contrib.auth.decorators import login_required
from setup.utils import verificar_autenticacao
from decimal import Decimal

from .models import Cliente, MatriculaDebitos
from apps.siape.models import RegisterMoney, RegisterMeta
from apps.funcionarios.models import Funcionario

import logging
from datetime import timedelta

from custom_tags_app.permissions import check_access


# Configurando o logger para registrar atividades e erros no sistema
logger = logging.getLogger(__name__)

#-------------------------- CONSULTA E FICHA CLIENTE ----------------------------------------------------

@check_access(level=2, setor='SIAPE')
def ficha_cliente(request, cpf):
    """
    Exibe a ficha completa de um cliente com base no CPF fornecido.
    Inclui informações das matrículas e cálculos relacionados a saldos e margens.
    """
    # Obtém o cliente pelo CPF, ou retorna um erro 404 se não encontrado
    cliente = get_object_or_404(Cliente, cpf=cpf)
    logger.info(f"Cliente encontrado: {cliente.nome}")

    # Filtra as matrículas associadas ao cliente
    matriculas_db = MatriculaDebitos.objects.filter(cliente=cliente)
    logger.info(f"Total de matrículas encontradas: {matriculas_db.count()}")
    
    margens = {}  # Dicionário para armazenar margens de diferentes matrículas
    cont_margem = 0  # Contador de margens processadas
    
    matriculas = []  # Lista para armazenar as matrículas processadas
    
    for matricula in matriculas_db:
        # Tentativa de conversão dos valores de `pmt` e `prazo` para float
        try:
            pmt = float(matricula.pmt)
            prazo = float(matricula.prazo)
        except (ValueError, TypeError):
            logger.error(f"Erro ao converter pmt ou prazo para float. pmt: {matricula.pmt}, prazo: {matricula.prazo}")
            pmt = 0.0
            prazo = 0.0
        logger.debug(f"Valores convertidos - PMT: {pmt}, Prazo: {prazo}")
        
        pr_pz = pmt * prazo  # Cálculo de pr_pz
        logger.debug(f"Valor de pr_pz: {pr_pz}")
        
        # Calcular porcentagem de desconto com base no prazo
        if prazo < 10:
            porcentagem = 0
        elif 10 <= prazo <= 39:
            porcentagem = 0.1
        elif 40 <= prazo <= 59:
            porcentagem = 0.2
        elif 60 <= prazo <= 71:
            porcentagem = 0.25
        elif 72 <= prazo <= 83:
            porcentagem = 0.3
        elif 84 <= prazo <= 96:
            porcentagem = 0.35
        else:
            porcentagem = 0
        
        desconto = pr_pz * porcentagem
        saldo_devedor = round(pr_pz - desconto, 2)  # Arredonda o saldo devedor para 2 casas decimais
        logger.debug(f"Desconto: {desconto}, Saldo Devedor: {saldo_devedor}")
        
        # Adiciona os detalhes da matrícula à lista de matrículas
        matriculas.append({
            'matricula': matricula.matricula,
            'rubrica': matricula.rubrica,
            'banco': matricula.banco,
            'orgao': matricula.orgao,
            'pmt': matricula.pmt,
            'prazo': matricula.prazo,
            'tipo_contrato': matricula.tipo_contrato,
            'contrato': matricula.contrato,
            'creditos': matricula.creditos,
            'liquido': matricula.liquido,
            'exc_soma': matricula.exc_soma,
            'margem': matricula.margem,
            'base_calc': matricula.base_calc,
            'bruta_5': matricula.bruta_5,
            'utilz_5': matricula.utilz_5,
            'beneficio_bruta_5': matricula.beneficio_bruta_5,
            'beneficio_utilizado_5': matricula.beneficio_utilizado_5,
            'bruta_35': matricula.bruta_35,
            'utilz_35': matricula.utilz_35,
            'bruta_70': matricula.bruta_70,
            'utilz_70': matricula.utilz_70,
            'saldo_35': matricula.saldo_35,
            'saldo_5': matricula.saldo_5,
            'beneficio_saldo_5': matricula.beneficio_saldo_5,
            'arq_upag': matricula.arq_upag,
            'exc_qtd': matricula.exc_qtd,
            'saldo_devedor': saldo_devedor,  # Saldo devedor calculado
        })
        
        # Processa margens e verifica duplicidade
        margem_chave = (matricula.saldo_35, matricula.saldo_5, matricula.beneficio_saldo_5)
        
        if cont_margem == 0:
            margens[margem_chave] = {
                'saldo_35': matricula.saldo_35,
                'saldo_5': matricula.saldo_5,
                'beneficio_saldo_5': matricula.beneficio_saldo_5,
            }
            cont_margem += 1
        else:
            if margem_chave not in margens:
                margens[margem_chave] = {
                    'saldo_35': matricula.saldo_35,
                    'saldo_5': matricula.saldo_5,
                    'beneficio_saldo_5': matricula.beneficio_saldo_5,
                }
        logger.debug(f"Margens acumuladas: {margens}")

    # Verifica duplicatas nas margens, arredondando para 2 casas decimais
    margens_unicas = {}
    for chave, valor in margens.items():
        chave_arredondada = (
            round(valor['saldo_35'], 2),
            round(valor['saldo_5'], 2),
            round(valor['beneficio_saldo_5'], 2)
        )
        logger.debug(f"Chave arredondada: {chave_arredondada}, Valor: {valor}")
        
        if chave_arredondada not in margens_unicas:
            margens_unicas[chave_arredondada] = valor

    context = {
        'cliente': {
            'nome': cliente.nome,
            'cpf': cliente.cpf,
            'uf': cliente.uf,
            'upag': cliente.upag,
            'matricula_instituidor': cliente.matricula_instituidor,
            'situacao_funcional': cliente.situacao_funcional,
            'rjur': cliente.rjur,
        },
        'margens': list(margens_unicas.values()),  # Lista de margens únicas
        'matriculas': matriculas,  # Lista de matrículas processadas
    }
    logger.info("Fim da função ficha_cliente")
    return render(request, 'consultas/ficha_cliente.html', context)

@require_http_methods(["POST", "GET"])
@check_access(level=1, setor='SIAPE')
def consulta_cliente(request):
    """
    Consulta um cliente pelo CPF. Se o cliente for encontrado, redireciona para a ficha do cliente.
    Caso contrário, exibe uma mensagem de erro.
    """
    mensagem = ""

    if request.method == "POST":
        cpf_cliente = request.POST.get('cpf_cliente', None)
        if cpf_cliente:
            cpf_cliente_limpo = cpf_cliente.replace('.', '').replace('-', '')
            try:
                cliente = Cliente.objects.get(cpf=cpf_cliente_limpo)
                return redirect('consulta:ficha_cliente_cpf', cpf=cpf_cliente_limpo)
            except Cliente.DoesNotExist:
                mensagem = "Cliente não encontrado!"
                logger.warning(f"Cliente com CPF {cpf_cliente_limpo} não encontrado.")
    
    return render(request, 'siape/consulta_cliente.html', {'mensagem': mensagem})

#---------------------------------------------------- RANKING SISTEMA -----------------------------------------------------------------

from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum, OuterRef, Subquery
from setup.utils import verificar_autenticacao
from decimal import Decimal

from .models import Cliente, MatriculaDebitos
from apps.siape.models import RegisterMoney, RegisterMeta
from apps.funcionarios.models import Funcionario

import logging

from custom_tags_app.permissions import check_access

import logging
from decimal import Decimal
from django.db.models import Sum, Subquery, OuterRef
from django.utils import timezone
from django.http import JsonResponse
from django.shortcuts import render

# Função para formatar valores monetários para o padrão '1.000,00'
def format_currency(value):
    """Formata o valor para o padrão '1.000,00'."""
    if value is None:
        value = Decimal('0.00')
    value = Decimal(value)
    formatted_value = f'{value:,.2f}'.replace('.', 'X').replace(',', '.').replace('X', ',')
    print(f"Valor formatado: {formatted_value}")
    return formatted_value

# Função para calcular valores gerais dentro do intervalo de datas
def calc_geral(valores_range, meta_geral):
    """Calcula o valor total geral e o percentual em relação à meta geral."""    
    soma_valores = sum(Decimal(venda.valor_est) for venda in valores_range)
    valor_total_meta_geral = Decimal(meta_geral.valor)
    
    percentual_height_geral = int((soma_valores / valor_total_meta_geral) * 100) if valor_total_meta_geral else 0
    valor_total_geral = format_currency(soma_valores)
    
    print(f"Soma dos valores gerais: {soma_valores}")
    print(f"Percentual em relação à meta geral: {percentual_height_geral}%")
    
    return valor_total_geral, percentual_height_geral

# Função para calcular valores específicos do departamento 'siape' dentro do intervalo de datas
def calc_siape(valores_range, meta_equipe):
    """Calcula o valor total e percentual específico para o departamento 'siape'."""
    funcionarios_ids = valores_range.values_list('funcionario_id', flat=True)
    funcionarios_range = Funcionario.objects.filter(id__in=funcionarios_ids, departamento='1')
    
    valores_siape = [
        Decimal(venda.valor_est) for venda in valores_range
        if venda.funcionario_id in funcionarios_range.values_list('id', flat=True)
    ]
    
    soma_valores = sum(valores_siape)
    valor_total_meta_equipe = Decimal(meta_equipe.valor)
    
    percentual_height_equipe = int((soma_valores / valor_total_meta_equipe) * 100) if valor_total_meta_equipe else 0
    valor_total_siape = format_currency(soma_valores)
    
    print(f"Soma dos valores SIAPE: {soma_valores}")
    print(f"Percentual em relação à meta da equipe: {percentual_height_equipe}%")
    
    return valor_total_siape, percentual_height_equipe

# Configurando o logger para registrar atividades e erros no sistema
logger = logging.getLogger(__name__)

# Função para obter as informações de ranking
def get_ranking_infos():
    today = timezone.now()
    first_day_of_month = today.replace(day=1)
    last_day_of_month = (today.replace(day=1, month=today.month + 1) - timezone.timedelta(days=1))

    valores_range = RegisterMoney.objects.filter(data__range=[first_day_of_month, last_day_of_month])
    
    vendas_no_mes = valores_range.values('funcionario_id').annotate(valor_total=Sum('valor_est')).order_by('-valor_total')
    top_funcionarios_ids = vendas_no_mes.values_list('funcionario_id', flat=True)[:5]
    
    print(f"IDs dos top funcionários!")

    top_vendedores = Funcionario.objects.filter(id__in=top_funcionarios_ids).annotate(
        valor_total=Subquery(
            RegisterMoney.objects.filter(
                funcionario_id=OuterRef('id'),
                data__range=[first_day_of_month, last_day_of_month]
            ).values('funcionario_id').annotate(
                total=Sum('valor_est')
            ).values('total')[:1]
        )
    ).order_by('-valor_total')[:5]

    # Montagem do ranking
    ranking = {
        f'top_{i+1}': {
            'foto': vendedor.foto.url if vendedor.foto else '/static/img/geral/default_image.png',
            'nome_completo': f'{vendedor.nome} {vendedor.sobrenome}',
            'valor_total': format_currency(vendedor.valor_total or 0)
        } for i, vendedor in enumerate(top_vendedores)
    }

    # Preenchendo posições vazias no ranking com valores padrão
    for i in range(1, 6):
        ranking.setdefault(f'top_{i}', {
            'foto': '/static/img/geral/default_image.png',
            'nome_completo': f'Nome {i}',
            'valor_total': format_currency(0.0)
        })

    print(f"Ranking final!")

    # Filtrando metas
    metas_gerais = RegisterMeta.objects.filter(descricao='Geral', status=True)
    metas_bônus = RegisterMeta.objects.filter(descricao='Bônus', status=True)
    metas_equipe = RegisterMeta.objects.filter(descricao='Equipe', status=True)
    
    meta_geral = max(metas_bônus, default=max(metas_gerais, default=RegisterMeta(valor=Decimal('0.00'))), key=lambda x: x.valor)
    meta_equipe = max(metas_equipe, default=RegisterMeta(valor=Decimal('0.00')), key=lambda x: x.valor)

    print(f"Meta geral: {meta_geral}")
    print(f"Meta equipe: {meta_equipe}")

    # Cálculo dos valores gerais e específicos
    valor_total_geral, percentual_height_geral = calc_geral(valores_range, meta_geral)
    valor_total_siape, percentual_height_equipe = calc_siape(valores_range, meta_equipe)

    # Contexto final para renderização
    context = {
        **ranking,
        'metaGeral': {
            'titulo': meta_geral.titulo,
            'valor': format_currency(meta_geral.valor),
            'percentual_height': percentual_height_geral,
            'valor_total': valor_total_geral
        },
        'metaEquipe': {
            'titulo': meta_equipe.titulo,
            'valor': format_currency(meta_equipe.valor),
            'percentual_height': percentual_height_equipe,
            'valor_total': valor_total_siape
        }
    }
    
    print(f"Contexto final!\n\n")

    return context

@verificar_autenticacao
def ranking(request):
    context = get_ranking_infos()
    return render(request, 'siape/ranking.html', context)

@verificar_autenticacao
@check_access(level=2, setor='SIAPE')
def update_ranking(request):
    ranking_data = get_ranking_infos()
    ranking_data['metaGeral']['percentual_height'] = int(ranking_data['metaGeral']['percentual_height'])
    
    print(f"Dados de ranking para atualização...!\n\n")

    return JsonResponse(ranking_data)
