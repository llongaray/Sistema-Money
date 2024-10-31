from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import Group
from apps.funcionarios.models import Funcionario, Departamento, Cargo
import logging

logger = logging.getLogger(__name__)

def get_user_info(user):
    try:
        funcionario = Funcionario.objects.get(usuario_id=user.id)
        departamento = funcionario.departamento
        cargo = funcionario.cargo
        if departamento:
            departamento_nome = departamento.grupo.name
        else:
            departamento_nome = None
        nivel = cargo.nivel if cargo else None
        return funcionario, departamento_nome, cargo, nivel
    except ObjectDoesNotExist:
        return None, None, None, None

def check_access(departamento, nivel_minimo):
    def decorator(view_func):
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            user = request.user
            print(f"\n----- Verificando acesso para o usuário: {user.username} -----")
            
            if user.is_superuser or user.groups.filter(name='ADMINISTRAÇÃO').exists():
                print(f"Usuário {user.username} é superuser ou pertence ao grupo ADMINISTRAÇÃO. Acesso concedido.")
                return view_func(request, *args, **kwargs)

            funcionario, departamento_nome, cargo, nivel = get_user_info(user)
            
            if not funcionario:
                print(f"Erro: Usuário {user.username} não tem um funcionário associado.")
                return HttpResponse("Usuário não tem um funcionário associado.", status=403)

            print(f"Funcionário: {funcionario}")
            print(f"Departamento: {departamento_nome}")
            print(f"Cargo: {cargo}")
            print(f"Nível: {nivel}")

            if departamento_nome != departamento and departamento != 'TODOS':
                print(f"Acesso negado. Usuário não pertence ao departamento {departamento}.")
                return HttpResponse(f"Acesso negado. Você não pertence ao departamento {departamento}.", status=403)

<<<<<<< HEAD
            niveis_hierarquia = {
                'TOTAL': 5,
                'SUPERVISOR GERAL': 4,
                'COORDENADOR': 3,
                'GERENTE': 2,
                'PADRÃO': 1,
                'ESTÁGIO': 0
            }
            
            nivel_usuario = niveis_hierarquia.get(nivel, 0)
            nivel_minimo_req = niveis_hierarquia.get(nivel_minimo, 5)
            
            if nivel_usuario < nivel_minimo_req:
                print(f"Acesso negado. Nível do usuário ({nivel}) é inferior ao requerido ({nivel_minimo}).")
=======
            niveis = ['ESTÁGIO', 'PADRÃO', 'SUPERVISÃO', 'TOTAL']
            if nivel and niveis.index(nivel) < niveis.index(nivel_minimo):
                print(f"Acesso negado. Nível do usuário é inferior ao requerido.")
>>>>>>> 8c9bdec505c96e6d36a28aa15689b2584d325ac5
                return HttpResponse(f"Acesso negado. Nível mínimo requerido: {nivel_minimo}.", status=403)

            print(f"Acesso concedido para {user.username}.")
            return view_func(request, *args, **kwargs)

        return _wrapped_view
    return decorator

def check_access_light(view_func):
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        user = request.user
        print(f"\n----- Acesso leve verificado para o usuário: {user.username} -----")
        funcionario, departamento_nome, cargo, nivel = get_user_info(user)
        if funcionario:
            print(f"Funcionário: {funcionario}")
            print(f"Departamento: {departamento_nome}")
            print(f"Cargo: {cargo}")
            print(f"Nível: {nivel}")
        else:
            print(f"Aviso: Usuário {user.username} não tem um funcionário associado.")
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view
