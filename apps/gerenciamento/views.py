# views.py no app `gerenciamento`
from custom_tags_app.permissions import check_access
from django.shortcuts import render
from apps.funcionarios.models import Funcionario, Empresa, Horario, Departamento, Cargo
from django.contrib.auth.decorators import login_required

@login_required
def gen_funcionarios(request):
    funcionarios = Funcionario.objects.all()
    empresas = Empresa.objects.all()
    horarios = Horario.objects.all()
    departamentos = Departamento.objects.all()
    cargos = Cargo.objects.all()

    context = {
        'funcionarios': funcionarios,
        'empresas': empresas,
        'horarios': horarios,
        'departamentos': departamentos,
        'cargos': cargos,
    }
    
    return render(request, 'gerenciamento/gen_funcionarios.html', context)

@login_required
def gen_inss(request):
    # Renderiza o template gen_inss.html
    return render(request, 'gerenciamento/gen_inss.html')