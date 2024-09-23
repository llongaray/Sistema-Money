from django import template
from django.urls import reverse

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
