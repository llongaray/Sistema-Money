from django.shortcuts import render
from django.contrib import messages
from apps.siape.models import Cliente, DebitoMargem, RegisterMoney


# Create your views here.


def get_all_forms(request):
    pass

def all_forms(request):
    pass

def get_ranking(request):
    pass

def render_ranking(request):
    context = {}
    # Se houver uma mensagem na sessão, adiciona ao contexto
    if messages.get_messages(request):
        context['mensagem'] = {
            'texto': list(messages.get_messages(request))[-1].message,
            'classe': 'error'  # ou 'success', dependendo do tipo de mensagem
        }
    return render(request, 'partials/_developing.html', context)


def render_dashboard(request):
    context = {}
    
    # Calcular totais
    total_clientes = Cliente.objects.count()  # Total de clientes registrados
    total_debitos = DebitoMargem.objects.count()  # Total de débitos/margens
    total_registros_money = RegisterMoney.objects.count()  # Total de registros de dinheiro

    # Adicionando os totais ao contexto
    context['totais'] = {
        'total_clientes': total_clientes,
        'total_debitos': total_debitos,
        'total_registros_money': total_registros_money,
    }

    # Se houver uma mensagem na sessão, adiciona ao contexto
    if messages.get_messages(request):
        context['mensagem'] = {
            'texto': list(messages.get_messages(request))[-1].message,
            'classe': 'error'  # ou 'success', dependendo do tipo de mensagem
        }

    return render(request, 'partials/_dashboard.html', context)
