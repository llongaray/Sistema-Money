from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Agendamento
from apps.funcionarios.models import Funcionario
from .forms import AgendamentoForm, ConfirmacaoForm, ReliseClienteForm
from django.utils import timezone

@login_required
def agendamento(request):
    try:
        # Verifica se o usuário logado tem um Funcionario associado
        funcionario_logado = Funcionario.objects.get(usuario_id=request.user.id)
    except Funcionario.DoesNotExist:
        funcionario_logado = None

    # Lista de funcionários excluindo o funcionário logado, se existir
    funcionarios = Funcionario.objects.all()
    if funcionario_logado:
        funcionarios = funcionarios.exclude(id=funcionario_logado.id)

    if request.method == 'POST':
        form = AgendamentoForm(request.POST)
        if form.is_valid():
            nome_cliente = form.cleaned_data['nome_cliente']
            cpf_cliente = form.cleaned_data['cpf_cliente']
            numero_celular = form.cleaned_data['numero_celular']
            data = form.cleaned_data['data']
            loja_agendada = form.cleaned_data['loja_agendada']
            
            # Obtém o ID do funcionário selecionado ou usa o ID do funcionário logado
            funcionario_id = request.POST.get('funcionario') or funcionario_logado.id
            funcionario = Funcionario.objects.get(id=funcionario_id)

            Agendamento.objects.create(
                nome_cliente=nome_cliente,
                cpf_cliente=cpf_cliente,
                numero_celular=numero_celular,
                data=data,
                loja_agendada=loja_agendada,
                funcionario=funcionario
            )
            return redirect('inss:agendamento')
    else:
        form = AgendamentoForm()

    return render(request, 'inss/agendamento.html', {
        'form': form,
        'funcionario_logado': funcionario_logado,
        'funcionarios': funcionarios
    })

@login_required
def confirmacao_agem(request):
    if request.method == 'POST':
        form = ConfirmacaoForm(request.POST)
        if form.is_valid():
            agendamento_id = form.cleaned_data['agendamento_id']
            confirmacao_agem = form.cleaned_data['confirmacao_agem']
            data_confim = timezone.now().date()
            comparecimento = form.cleaned_data['comparecimento']
            negocio_fechado = form.cleaned_data['negocio_fechado']
            agendamento = get_object_or_404(Agendamento, id=agendamento_id)
            
            agendamento.confirmacao_agem = confirmacao_agem
            agendamento.data_confim = data_confim
            agendamento.comparecimento = comparecimento
            agendamento.negocio_fechado = negocio_fechado
            agendamento.save()
            
            return redirect('inss:confirmacao_agem')
    else:
        form = ConfirmacaoForm()

    return render(request, 'inss/confirmacao_agem.html', {
        'form': form
    })

@login_required
def relise_clientes(request):
    if request.method == 'POST':
        form = ReliseClienteForm(request.POST)
        if form.is_valid():
            agendamento_id = form.cleaned_data['agendamento_id']
            nome_cliente = form.cleaned_data['nome_cliente']
            cpf_cliente = form.cleaned_data['cpf_cliente']
            numero_celular = form.cleaned_data['numero_celular']
            loja_agendada = form.cleaned_data['loja_agendada']
            funcionario_atendimento = Funcionario.objects.get(usuario_id=request.user.id)
            
            agendamento = get_object_or_404(Agendamento, id=agendamento_id)
            agendamento.nome_cliente = nome_cliente
            agendamento.cpf_cliente = cpf_cliente
            agendamento.numero_celular = numero_celular
            agendamento.loja_agendada = loja_agendada
            agendamento.funcionario_atendimento = funcionario_atendimento
            agendamento.save()
            
            return redirect('inss:relise_clientes')
    else:
        form = ReliseClienteForm()

    return render(request, 'inss/relise_clientes.html', {
        'form': form
    })

@login_required
def loja_poa(request):
    agendamentos = Agendamento.objects.filter(loja_agendada='Porto Alegre')
    return render(request, 'inss/loja_poa.html', {
        'agendamentos': agendamentos
    })

@login_required
def loja_sle(request):
    agendamentos = Agendamento.objects.filter(loja_agendada='São Leopoldo')
    return render(request, 'inss/loja_sle.html', {
        'agendamentos': agendamentos
    })

@login_required
def loja_sm(request):
    agendamentos = Agendamento.objects.filter(loja_agendada='Santa Maria')
    return render(request, 'inss/loja_sm.html', {
        'agendamentos': agendamentos
    })

@login_required
def save_cliente(request):
    if request.method == 'POST':
        nome_cliente = request.POST['nome_cliente']
        cpf_cliente = request.POST['cpf_cliente']
        numero_celular = request.POST['numero_celular']
        loja_agendada = request.POST['loja_agendada']
        agendamento_id = request.POST['agendamento_id']
        comparecimento = request.POST.get('comparecimento') == 'on'
        negocio_fechado = request.POST.get('negocio_fechado') == 'on'

        funcionario_agendamento = Funcionario.objects.get(usuario_id=request.user.id)
        agendamento = get_object_or_404(Agendamento, id=agendamento_id)
        
        agendamento.nome_cliente = nome_cliente
        agendamento.cpf_cliente = cpf_cliente
        agendamento.numero_celular = numero_celular
        agendamento.loja_agendada = loja_agendada
        agendamento.funcionario = funcionario_agendamento
        agendamento.funcionario_atendimento = funcionario_agendamento
        agendamento.comparecimento = comparecimento
        agendamento.negocio_fechado = negocio_fechado
        agendamento.save()

        return redirect(f'inss:loja_{agendamento.loja_agendada.lower().replace(" ", "_")}')


# ------------- Ranking INSS ----------------
