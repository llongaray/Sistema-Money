# apps/usuarios/views.py
from custom_tags_app.permissions import check_access
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.auth.models import Group

def criar_usuario_com_grupo(nome, sobrenome, email, senha, senha2, grupo_id):
    """
    Cria um novo usuário com as informações fornecidas, adiciona o usuário ao grupo especificado e retorna o ID do usuário e uma variável de sucesso.

    Args:
        nome (str): Primeiro nome do usuário.
        sobrenome (str): Sobrenome do usuário.
        email (str): E-mail do usuário.
        senha (str): Senha do usuário.
        senha2 (str): Confirmação da senha do usuário.
        grupo_id (int): ID do grupo ao qual o usuário será adicionado.

    Returns:
        dict: Um dicionário contendo o ID do usuário e uma variável de sucesso.
    """
    success = False
    user_id = None

    if senha != senha2:
        return {'success': success, 'user_id': user_id, 'error': 'As senhas não coincidem.'}

    if User.objects.filter(username=email).exists():
        return {'success': success, 'user_id': user_id, 'error': 'Usuário já existe.'}

    try:
        user = User.objects.create_user(
            username=email,
            email=email,
            password=senha,
            first_name=nome,
            last_name=sobrenome
        )

        # Adiciona o usuário ao grupo especificado, se o grupo existir
        try:
            group = Group.objects.get(id=grupo_id)
            user.groups.add(group)
        except Group.DoesNotExist:
            return {'success': success, 'user_id': user_id, 'error': 'Grupo não encontrado.'}

        user_id = user.id
        success = True
        return {'success': success, 'user_id': user_id}

    except Exception as e:
        return {'success': success, 'user_id': user_id, 'error': str(e)}

def login_view(request):
    """
    Gerencia o login do usuário. Exibe o formulário de login e realiza a autenticação.

    Args:
        request (HttpRequest): A requisição HTTP.

    Returns:
        HttpResponse: Redireciona para a URL de destino após o login ou exibe um formulário com erro de autenticação.
    """
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('siape:ranking')  # Substitua 'home' pela URL de destino após o login
        else:
            return render(request, 'usuarios/login.html', {'form': form, 'error': 'Usuário ou senha inválidos'})
    else:
        form = AuthenticationForm()
    return render(request, 'usuarios/login.html', {'form': form})

@login_required
def logout_view(request):
    """
    Realiza o logout do usuário autenticado. Redireciona para a URL de destino após o logout.

    Args:
        request (HttpRequest): A requisição HTTP.

    Returns:
        HttpResponse: Redireciona para a URL de destino após o logout.
    """
    logout(request)
    return redirect('siape:ranking')  # Substitua 'home' pela URL de destino após o logout
