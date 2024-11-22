from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, time, timedelta
from .models import Equipe, MembroEquipe, Pontuacao, ProvaGincana
from custom_tags_app.permissions import check_access
from setup.utils import verificar_autenticacao
from apps.funcionarios.models import *

# ===== INÍCIO DA SEÇÃO DE ALL FORMS =====

def get_all_forms():
    """
    Obtém todos os parâmetros necessários para all_forms.
    """
    equipes = Equipe.objects.all()
    funcionarios = Funcionario.objects.all()
    pontuacoes = Pontuacao.objects.select_related('funcionario', 'equipe').all()
    
    # Cálculo do período de análise
    hoje = timezone.now()
    primeiro_dia = hoje.replace(day=1)
    ultimo_dia = (primeiro_dia + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    # Contagem total de equipes e membros
    total_equipes = equipes.count()
    total_membros = MembroEquipe.objects.count()
    
    # Cálculo de pontos totais
    total_pontos = sum(pontuacao.pontos for pontuacao in pontuacoes)
    
    # Ranking de pontos
    ranking_pontos = []
    for pontuacao in pontuacoes:
        ranking_pontos.append({
            'funcionario': pontuacao.funcionario.nome,
            'equipe': pontuacao.equipe.nome,
            'pontos': pontuacao.pontos
        })
    
    context = {
        'equipes': equipes,
        'funcionarios': funcionarios,
        'periodo_analise': f"{primeiro_dia.strftime('%d/%m/%Y')} - {ultimo_dia.strftime('%d/%m/%Y')}",
        'total_equipes': total_equipes,
        'total_membros': total_membros,
        'total_pontos': total_pontos,
        'ranking_pontos': sorted(ranking_pontos, key=lambda x: x['pontos'], reverse=True)
    }
    
    return context

@verificar_autenticacao
def all_forms(request):
    """
    Renderiza a página com todos os formulários da Gincana e processa os formulários enviados.
    """
    mensagem = {'texto': '', 'classe': ''}
    
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        
        if form_type == 'registro_equipe':
            mensagem = post_equipe(request)
        
        elif form_type == 'adicionar_membro':
            try:
                equipe_id = request.POST.get('equipe')
                funcionario_id = request.POST.get('funcionario')
                
                MembroEquipe.objects.create(
                    equipe_id=equipe_id,
                    funcionario_id=funcionario_id
                )
                mensagem = {'texto': 'Membro adicionado com sucesso!', 'classe': 'success'}
                
            except Exception as e:
                mensagem = {'texto': f'Erro ao adicionar membro: {str(e)}', 'classe': 'error'}
        
        elif form_type == 'registrar_pontos':
            try:
                funcionario_id = request.POST.get('funcionario')
                pontos = int(request.POST.get('pontos'))
                motivo = request.POST.get('motivo')
                
                funcionario = Funcionario.objects.get(id=funcionario_id)
                membro = MembroEquipe.objects.get(funcionario=funcionario)
                
                Pontuacao.objects.create(
                    funcionario=funcionario,
                    equipe=membro.equipe,
                    pontos=pontos,
                    motivo=motivo
                )
                mensagem = {'texto': 'Pontos registrados com sucesso!', 'classe': 'success'}
                
            except Exception as e:
                mensagem = {'texto': f'Erro ao registrar pontos: {str(e)}', 'classe': 'error'}
    
    context = get_all_forms()
    context['mensagem'] = mensagem
    
    return render(request, 'geral/all_forms.html', context)

def post_equipe(request):
    """
    Processa o POST de registro de uma nova equipe.
    Retorna uma mensagem de sucesso ou erro.
    """
    try:
        # Obtém os dados do formulário
        nome = request.POST.get('nome_equipe')
        descricao = request.POST.get('descricao_equipe')
        lider_id = request.POST.get('lider_equipe')
        
        # Validações básicas
        if not nome:
            return {'texto': 'O nome da equipe é obrigatório.', 'classe': 'error'}
        
        if not lider_id:
            return {'texto': 'É necessário selecionar um líder para a equipe.', 'classe': 'error'}
            
        # Verifica se já existe uma equipe com este nome
        if Equipe.objects.filter(nome=nome).exists():
            return {'texto': f'Já existe uma equipe com o nome "{nome}".', 'classe': 'error'}
            
        # Verifica se o líder existe
        try:
            lider = Funcionario.objects.get(id=lider_id)
        except Funcionario.DoesNotExist:
            return {'texto': 'Líder selecionado não encontrado.', 'classe': 'error'}
            
        # Cria a nova equipe
        equipe = Equipe.objects.create(
            nome=nome,
            descricao=descricao,
            lider=lider,
            status=True  # Equipe começa ativa por padrão
        )
        
        # Cria automaticamente o primeiro membro (líder) da equipe
        MembroEquipe.objects.create(
            funcionario=lider,
            equipe=equipe,
            ativo=True
        )
        
        return {
            'texto': f'Equipe "{nome}" criada com sucesso! {lider.nome} definido como líder.',
            'classe': 'success'
        }
        
    except Exception as e:
        return {
            'texto': f'Erro ao criar equipe: {str(e)}',
            'classe': 'error'
        }

# ===== INÍCIO DA SEÇÃO DE RANKING =====

def get_cards():
    """
    Obtém os dados para os cards do ranking.
    """
    hoje = timezone.now()
    primeiro_dia = hoje.replace(day=1)
    ultimo_dia = (primeiro_dia + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    # Pontuações do período
    pontuacoes = Pontuacao.objects.filter(
        data_registro__range=[primeiro_dia, ultimo_dia]
    ).select_related('equipe')
    
    # Cálculo de pontos totais
    pontos_totais = sum(p.pontos for p in pontuacoes)
    
    # Contagem de equipes ativas
    equipes_ativas = Equipe.objects.filter(status=True).count()
    total_equipes = Equipe.objects.count()
    
    context = {
        'pontos_totais': {
            'valor': pontos_totais,
            'percentual': round((pontos_totais / 1000) * 100, 2)  # Meta exemplo de 1000 pontos
        },
        'equipes_ativas': {
            'total': equipes_ativas,
            'participacao': round((equipes_ativas / total_equipes) * 100, 2) if total_equipes > 0 else 0
        }
    }
    
    return context

def get_podium():
    """
    Obtém os dados para o pódium do ranking.
    """
    equipes = Equipe.objects.all()
    podium_data = []
    
    for equipe in equipes:
        pontos_equipe = Pontuacao.objects.filter(equipe=equipe).aggregate(
            total_pontos=models.Sum('pontos')
        )['total_pontos'] or 0
        
        podium_data.append({
            'nome': equipe.nome,
            'logo': equipe.logo.url if equipe.logo else None,
            'total_pontos': pontos_equipe
        })
    
    # Ordena por pontuação
    podium_data.sort(key=lambda x: x['total_pontos'], reverse=True)
    
    return podium_data[:5]  # Retorna top 5

def get_destaques():
    """
    Obtém os destaques da semana para o ranking.
    """
    hoje = timezone.now()
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    
    # Melhor equipe da semana
    melhor_equipe = Equipe.objects.annotate(
        pontos_semana=models.Sum('pontuacoes__pontos',  # Corrigido de pontuacao para pontuacoes
            filter=models.Q(pontuacoes__data_registro__gte=inicio_semana))
    ).order_by('-pontos_semana').first()
    
    # Melhor jogador da semana
    melhor_jogador = Funcionario.objects.annotate(
        pontos_semana=models.Sum('pontuacoes__pontos',  # Corrigido de pontuacao para pontuacoes
            filter=models.Q(pontuacoes__data_registro__gte=inicio_semana))
    ).order_by('-pontos_semana').first()
    
    # Prova mais participada
    prova_destaque = ProvaGincana.objects.annotate(
        total_participantes=models.Count('participantes')
    ).order_by('-total_participantes').first()
    
    return {
        'melhor_equipe': {
            'nome': melhor_equipe.nome if melhor_equipe else "Sem dados",
            'logo': melhor_equipe.logo.url if melhor_equipe and melhor_equipe.logo else None,
            'pontos': melhor_equipe.pontos_semana if melhor_equipe else 0
        },
        'melhor_jogador': {
            'nome': melhor_jogador.nome if melhor_jogador else "Sem dados",
            'foto': melhor_jogador.foto.url if melhor_jogador and melhor_jogador.foto else None,
            'pontos': melhor_jogador.pontos_semana if melhor_jogador else 0
        },
        'prova_destaque': {
            'nome': prova_destaque.nome if prova_destaque else "Sem dados",
            'icone': prova_destaque.icone if prova_destaque else "fa-star",
            'participantes': prova_destaque.total_participantes if prova_destaque else 0
        }
    }

@verificar_autenticacao
def render_ranking(request):
    """
    Renderiza a página de ranking da Gincana.
    """
    context = {
        'podium': get_podium(),
        'destaques': get_destaques(),
        **get_cards()
    }
    
    return render(request, 'geral/ranking_gincana.html', context)
