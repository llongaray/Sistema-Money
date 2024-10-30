from django import template
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist
from ..permissions import get_user_info

register = template.Library()

@register.simple_tag
def get_user_permissions(user):
    """
    Retorna o nível de permissão e o setor para o usuário autenticado.
    Para 'Administrador(a)' e 'Suporte', o setor não é necessário.
    """
    if not user.is_authenticated:
        return {'level': 0, 'setor': None}

    # Define o nível de permissão
    if user.groups.filter(name='Administrador(a)').exists():
        return {'level': 4, 'setor': None}
    elif user.groups.filter(name='Suporte').exists():
        return {'level': 3, 'setor': None}
    elif user.groups.filter(name='Supervisor(a)').exists():
        if user.groups.filter(name='SIAPE').exists():
            return {'level': 2, 'setor': 'SIAPE'}
        elif user.groups.filter(name='INSS').exists():
            return {'level': 2, 'setor': 'INSS'}
        elif user.groups.filter(name='LOJAS').exists():
            return {'level': 2, 'setor': 'LOJAS'}
    elif user.groups.filter(name='Atendente').exists():
        if user.groups.filter(name='SIAPE').exists():
            return {'level': 1, 'setor': 'SIAPE'}
        elif user.groups.filter(name='INSS').exists():
            return {'level': 1, 'setor': 'INSS'}
        elif user.groups.filter(name='LOJAS').exists():
            return {'level': 1, 'setor': 'LOJAS'}

    return {'level': 0, 'setor': None}

@register.simple_tag
def get_user_cargo(user):
    print(f"\n----- Obtendo cargo para o usuário: {user.username} -----")
    funcionario, departamento_nome, cargo, nivel = get_user_info(user)
    if funcionario:
        print(f"Funcionário: {funcionario}")
        print(f"Departamento: {departamento_nome}")
        print(f"Cargo: {cargo}")
        print(f"Nível: {nivel}")
        return {'departamento': departamento_nome, 'nivel': nivel, 'cargo': str(cargo)}
    else:
        print(f"Aviso: Usuário {user.username} não tem um funcionário associado.")
        return {'departamento': None, 'nivel': None, 'cargo': None}
