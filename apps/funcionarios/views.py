from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User, Group
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from .forms import FuncionarioForm, UserForm, FuncionarioFullForm, CustomUserForm  # Importando os formulários
from .models import Funcionario, Empresa, Horario, Departamento, Cargo
from custom_tags_app.permissions import check_access
from datetime import datetime
from django.http import JsonResponse
import json
import logging
from datetime import date
from .forms import UserGroupForm

from django.utils.text import slugify
import os
from django.core.files.storage import default_storage
from django.conf import settings

# Configuração do logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

ESTADOS_BRASIL = [
    ('AC', 'Acre'), ('AL', 'Alagoas'), ('AP', 'Amapá'), ('AM', 'Amazonas'), ('BA', 'Bahia'),
    ('CE', 'Ceará'), ('DF', 'Distrito Federal'), ('ES', 'Espírito Santo'), ('GO', 'Goiás'),
    ('MA', 'Maranhão'), ('MT', 'Mato Grosso'), ('MS', 'Mato Grosso do Sul'), ('MG', 'Minas Gerais'),
    ('PA', 'Pará'), ('PB', 'Paraíba'), ('PR', 'Paraná'), ('PE', 'Pernambuco'), ('PI', 'Piauí'),
    ('RJ', 'Rio de Janeiro'), ('RN', 'Rio Grande do Norte'), ('RS', 'Rio Grande do Sul'),
    ('RO', 'Rondônia'), ('RR', 'Roraima'), ('SC', 'Santa Catarina'), ('SP', 'São Paulo'),
    ('SE', 'Sergipe'), ('TO', 'Tocantins')
]



# ----- Gets de funcionarios -----------
def get_funcionario(dados):
    """Processa o formulário de cadastro de funcionário, cria e salva o funcionário, e retorna uma mensagem de sucesso ou erro."""
    print("Função 'get_funcionario' aberta\n")  # Print quando a função é chamada

    # Valores padrão para campos não informados
    valores_padrao = {
        'cnpj': '01500202000122',
        'pis': '00120002334',
        'rg': '00000000000',
        'data_de_nascimento': date(2000, 1, 1),
        'cnh': '0000000000',
        'categoria_cnh': 'N/A',
        'celular': '00000000000',
        'celular_sms': False,
        'celular_ligacao': False,
        'celular_whatsapp': False,
        'nome_do_pai': 'Sem texto!',
        'nome_da_mae': 'Sem texto!',
        'genero': 'Não especificado',
        'nacionalidade': 'Sem texto!',
        'naturalidade': 'Sem texto!',
        'estado_civil': 'Solteiro',
        'matricula': '000000',
        'status': 'Ativo',
        'data_de_admissao': date(2000, 1, 1),
        'numero_da_folha': '000000',
        'ctps': '0000000000',
        'superior_direto': None,
        'identidade': None,
        'carteira_de_trabalho': None,
        'comprovante_de_escolaridade': None,
        'pdf_contrato': None,
        'certidao_de_nascimento': None,
    }

    # Atualiza os valores padrão com os dados do formulário, sobrepondo apenas o que foi informado
    dados_completos = {**valores_padrao, **dados}
    print("Dados completos após inclusão dos valores padrão:", dados_completos, "\n")  # Print após combinação com valores padrão

    # Cria uma instância do modelo Funcionario com os dados
    funcionario = Funcionario(
        nome=dados_completos.get('nome', ''),
        sobrenome=dados_completos.get('sobrenome', ''),
        cpf=dados_completos.get('cpf', ''),
        cep=dados_completos.get('cep', ''),
        endereco=dados_completos.get('endereco', ''),
        bairro=dados_completos.get('bairro', ''),
        cidade=dados_completos.get('cidade', ''),
        estado=dados_completos.get('estado', ''),
        empresa_id=dados_completos.get('empresa', None),
        horario_id=dados_completos.get('horario', None),
        cargo_id=dados_completos.get('cargo', None),
        departamento_id=dados_completos.get('departamento', None),
        foto=dados_completos.get('foto', None),
        **valores_padrao
    )

    print("Funcionário instanciado com os dados:", funcionario, "\n")  # Print para visualizar o objeto Funcionario criado

    try:
        funcionario.save()  # Salva o funcionário no banco de dados
        print("Funcionário salvo com sucesso:", funcionario, "\n")  # Print após o funcionário ser salvo
        mensagem = f'Funcionário {funcionario.nome} {funcionario.sobrenome} cadastrado com sucesso!'
    except Exception as e:
        mensagem = f'Erro ao cadastrar o funcionário. Tente novamente mais tarde. Detalhes: {e}'
        print("Erro ao salvar o funcionário:", e, "\n")  # Print para exibir qualquer erro ocorrido

    print("Mensagem final:", mensagem, "\n")  # Print da mensagem final
    return mensagem


# ------ CRIAR USUARIO -------------------
def get_usuario(form_data, funcionario):
    # Cria uma instância do modelo User com os dados
    usuario = User(
        username=form_data['username'],
        first_name=funcionario.nome,  # Nome do funcionário
        last_name=funcionario.sobrenome,  # Sobrenome do funcionário
        email=form_data['email'],
    )
    usuario.set_password(form_data['password'])  # Define a senha de forma segura

    return usuario

def create_user(form, funcionario_id):
    """Processa o formulário de cadastro de usuário e retorna uma mensagem de sucesso ou erro."""
    mensagem = 'none'

    # Print para verificar se o formulário é válido
    print(f"Formulário válido? {form.is_valid()}")

    if form.is_valid():
        formulario = {
            'username': form.cleaned_data.get('username'),
            'email': form.cleaned_data.get('email'),
            'password': form.cleaned_data.get('password'),
        }

        # Print para verificar os dados limpos do formulário
        print(f"Dados do formulário: {formulario}")

        try:
            if funcionario_id:
                # Print para verificar o ID do funcionário
                print(f"ID do funcionário: {funcionario_id}")
                
                funcionario = Funcionario.objects.get(id=funcionario_id)
                print(f"Funcionário encontrado: {funcionario}")

                usuario = get_usuario(formulario, funcionario)
                print(f"Usuário criado: {usuario}")

                usuario.save()
                print("Usuário salvo com sucesso.")

                # Atualiza o Funcionario relacionado com o ID do usuário criado
                funcionario.usuario_id = usuario.id
                funcionario.save()
                print("Funcionário atualizado com o ID do usuário.")

                mensagem = f'Usuário {usuario.username} cadastrado com sucesso!'
            else:
                mensagem = 'Nenhum funcionário selecionado.'
                print(mensagem)
            
        except Exception as e:
            mensagem = f'Erro ao cadastrar o usuário. Tente novamente mais tarde. Detalhes: {e}'
            print(mensagem)
    
    else:
        mensagem = 'Erro na validação do formulário.'
        print(mensagem)

    return mensagem




# ------- ASSOCIAR GROUPOS AO USER ------------------------

def associar_grupos(form):
    """Processa o formulário para associar grupos a um usuário e retorna uma mensagem de sucesso ou erro."""
    mensagem = 'none'

    if form.is_valid():
        # Obtém os dados do formulário
        user = form.cleaned_data['user']
        groups = form.cleaned_data['groups']
        
        # Processa os dados com a função get_associar_grupos
        mensagem_resultado = get_associar_grupos(user, groups)
        mensagem = mensagem_resultado['texto']
    
    else:
        mensagem = 'Formulário inválido. Verifique os dados e tente novamente.'

    return mensagem


def get_associar_grupos(user, groups):
    """Associa grupos ao usuário e retorna uma mensagem."""
    try:
        # Inicializa a lista para armazenar os nomes dos grupos associados
        grupos_associados = []
        
        for group in groups:
            user.groups.add(group)
            grupos_associados.append(group.name)

        return {
            'texto': f'Grupos ({", ".join(grupos_associados)}) associados com sucesso ao usuário {user.username}!',
            'tipo': 'success'
        }
    except Exception as e:
        return {
            'texto': f'Ocorreu um erro: {str(e)}',
            'tipo': 'error'
        }

# ------------------ EDITAÇÃO DE FUNCIONARIO E USER --------------------------

def render_ficha_funcionario(request, id, nome_sobrenome):
    funcionario = get_object_or_404(Funcionario, id=id)
    user = funcionario.usuario

    # Carrega os forms pré-preenchidos com os dados existentes
    form_funcionario = FuncionarioFullForm(instance=funcionario)
    form_user = CustomUserForm(instance=user)

    return render(request, 'funcionarios/ficha_funcionario.html', {
        'form_funcionario': form_funcionario,
        'form_user': form_user,
        'funcionario': funcionario,
    })

def update_funcionario(request, id):
    funcionario = get_object_or_404(Funcionario, id=id)
    
    if request.method == 'POST':
        form_funcionario = FuncionarioFullForm(request.POST, request.FILES, instance=funcionario)
        
        if form_funcionario.is_valid():
            # Cria um dicionário com os dados do formulário
            dados_atualizados = {
                'nome': form_funcionario.cleaned_data.get('nome'),
                'sobrenome': form_funcionario.cleaned_data.get('sobrenome'),
                'cpf': form_funcionario.cleaned_data.get('cpf'),
                'cnpj': form_funcionario.cleaned_data.get('cnpj'),
                'pis': form_funcionario.cleaned_data.get('pis'),
                'rg': form_funcionario.cleaned_data.get('rg'),
                'data_de_nascimento': form_funcionario.cleaned_data.get('data_de_nascimento'),
                'cnh': form_funcionario.cleaned_data.get('cnh'),
                'categoria_cnh': form_funcionario.cleaned_data.get('categoria_cnh'),
                'cep': form_funcionario.cleaned_data.get('cep'),
                'endereco': form_funcionario.cleaned_data.get('endereco'),
                'bairro': form_funcionario.cleaned_data.get('bairro'),
                'cidade': form_funcionario.cleaned_data.get('cidade'),
                'estado': form_funcionario.cleaned_data.get('estado'),
                'celular': form_funcionario.cleaned_data.get('celular'),
                'celular_sms': form_funcionario.cleaned_data.get('celular_sms'),
                'celular_ligacao': form_funcionario.cleaned_data.get('celular_ligacao'),
                'celular_whatsapp': form_funcionario.cleaned_data.get('celular_whatsapp'),
                'nome_do_pai': form_funcionario.cleaned_data.get('nome_do_pai'),
                'nome_da_mae': form_funcionario.cleaned_data.get('nome_da_mae'),
                'genero': form_funcionario.cleaned_data.get('genero'),
                'nacionalidade': form_funcionario.cleaned_data.get('nacionalidade'),
                'naturalidade': form_funcionario.cleaned_data.get('naturalidade'),
                'estado_civil': form_funcionario.cleaned_data.get('estado_civil'),
                'matricula': form_funcionario.cleaned_data.get('matricula'),
                'status': form_funcionario.cleaned_data.get('status'),
                'data_de_admissao': form_funcionario.cleaned_data.get('data_de_admissao'),
                'horario': form_funcionario.cleaned_data.get('horario'),
                'departamento': form_funcionario.cleaned_data.get('departamento'),
                'cargo': form_funcionario.cleaned_data.get('cargo'),
                'numero_da_folha': form_funcionario.cleaned_data.get('numero_da_folha'),
                'ctps': form_funcionario.cleaned_data.get('ctps'),
                'superior_direto': form_funcionario.cleaned_data.get('superior_direto'),
                'identidade': form_funcionario.cleaned_data.get('identidade'),
                'carteira_de_trabalho': form_funcionario.cleaned_data.get('carteira_de_trabalho'),
                'comprovante_de_escolaridade': form_funcionario.cleaned_data.get('comprovante_de_escolaridade'),
                'pdf_contrato': form_funcionario.cleaned_data.get('pdf_contrato'),
                'certidao_de_nascimento': form_funcionario.cleaned_data.get('certidao_de_nascimento'),
            }

            # Atualiza os campos do funcionário com os dados do dicionário
            for campo, valor in dados_atualizados.items():
                setattr(funcionario, campo, valor)
            
            try:
                funcionario.save()
                messages.success(request, f'Funcionário {funcionario.nome} {funcionario.sobrenome} atualizado com sucesso!')
                logger.info(f'Funcionário {funcionario.nome} {funcionario.sobrenome} atualizado com sucesso!')
            except Exception as e:
                error_message = f'Erro ao atualizar o funcionário: {e}'
                messages.error(request, error_message)
                logger.error(error_message)
        else:
            # Adiciona mensagens de erro específicas de cada campo
            for field in form_funcionario.errors:
                for error in form_funcionario.errors[field]:
                    error_message = f'Erro no campo {field}: {error}'
                    messages.error(request, error_message)
                    logger.warning(error_message)

    return redirect('funcionarios:all_forms')

def update_user(request, id):
    funcionario = get_object_or_404(Funcionario, id=id)
    user = funcionario.usuario

    if request.method == 'POST':
        form_user = CustomUserForm(request.POST, instance=user)
        if form_user.is_valid():
            form_user.save()
            messages.success(request, f'Usuário {user.username} atualizado com sucesso!')
        else:
            messages.error(request, 'Erro ao atualizar o usuário.')
        
        # Imprimir mensagens de feedback
        for message in messages.get_messages(request):
            print(f"{message.level_tag.upper()}: {message.message}")

    return redirect('funcionarios:all_forms')


# ----------------------------------------------------------------------------------------------------------------

# views.py no app `funcionarios`
from django.shortcuts import redirect
from django.contrib import messages
from apps.funcionarios.models import Empresa, Horario, Departamento, Cargo

from django.http import HttpResponse
from django.shortcuts import redirect
from django.contrib import messages
from .models import Empresa, Horario, Departamento, Cargo
from django.utils.dateparse import parse_date

def get_empresa(form_data):
    """Cria uma nova empresa com os parâmetros fornecidos e retorna uma mensagem de sucesso ou erro."""
    print("Função 'get_empresa' aberta\n")

    # Captura os parâmetros da URL
    nome = form_data.get('nome')
    cnpj = form_data.get('cnpj')
    endereco = form_data.get('endereco')

    # Verifica se todos os parâmetros necessários foram fornecidos
    if nome and cnpj and endereco:
        try:
            Empresa.objects.create(nome=nome, cnpj=cnpj, endereco=endereco)
            mensagem = f"Empresa '{nome}' foi adicionada com sucesso!"
            print("Mensagem de sucesso:", mensagem, "\n")
        except Exception as e:
            mensagem = f"Erro ao adicionar a empresa. Detalhes: {e}"
            print("Erro ao adicionar empresa:", e, "\n")
    else:
        mensagem = "Faltam parâmetros para criar a empresa."
        print("Mensagem de erro:", mensagem, "\n")

    return mensagem

def get_horario(form_data):
    """Cria um novo horário com os parâmetros fornecidos e retorna uma mensagem de sucesso ou erro."""
    print("Função 'get_horario' aberta\n")

    # Captura os parâmetros da URL
    nome = form_data.get('nome')
    horario_entrada = form_data.get('horario_entrada')
    horario_saida = form_data.get('horario_saida')

    # Verifica se todos os parâmetros necessários foram fornecidos
    if nome and horario_entrada and horario_saida:
        try:
            Horario.objects.create(nome=nome, horario_entrada=horario_entrada, horario_saida=horario_saida)
            mensagem = f"Horário '{nome}' foi adicionado com sucesso!"
            print("Mensagem de sucesso:", mensagem, "\n")
        except Exception as e:
            mensagem = f"Erro ao adicionar o horário. Detalhes: {e}"
            print("Erro ao adicionar horário:", e, "\n")
    else:
        mensagem = "Faltam parâmetros para criar o horário."
        print("Mensagem de erro:", mensagem, "\n")

    return mensagem

def get_departamento(form_data):
    """Cria um novo departamento com os parâmetros fornecidos e retorna uma mensagem de sucesso ou erro."""
    print("Função 'get_departamento' aberta\n")

    # Captura os parâmetros da URL
    nome = form_data.get('nome')

    # Verifica se o parâmetro necessário foi fornecido
    if nome:
        try:
            Departamento.objects.create(nome=nome)
            mensagem = f"Departamento '{nome}' foi adicionado com sucesso!"
            print("Mensagem de sucesso:", mensagem, "\n")
        except Exception as e:
            mensagem = f"Erro ao adicionar o departamento. Detalhes: {e}"
            print("Erro ao adicionar departamento:", e, "\n")
    else:
        mensagem = "Faltam parâmetros para criar o departamento."
        print("Mensagem de erro:", mensagem, "\n")

    return mensagem

def get_cargo(form_data):
    nome = form_data.get('nome')
    nivel = form_data.get('nivel')
    print(f'recebido {nome} e {nivel}!\n')
    if not nome or not nivel:
        return 'Faltam parâmetros para criar o cargo.'

    Cargo.objects.create(nome=nome, nivel=nivel)
    return 'Cargo criado com sucesso.'


def delete_funcionario(funcionario_id):
    try:
        funcionario = Funcionario.objects.get(id=funcionario_id)
        funcionario.delete()
        return {'texto': 'Funcionário excluído com sucesso!', 'classe': 'success'}
    except Funcionario.DoesNotExist:
        return {'texto': 'Funcionário não encontrado.', 'classe': 'error'}
    except Exception as e:
        return {'texto': f'Erro ao excluir funcionário: {str(e)}', 'classe': 'error'}

def get_all_forms_and_objects():
    """
    Função para centralizar a obtenção de formulários e objetos utilizados em 'render_all_forms'.
    Retorna um dicionário com todos os formulários e objetos adicionais.
    """
    # Definição dos formulários
    form_funcionario = FuncionarioForm()
    form_usuario = UserForm()
    form_grupo = UserGroupForm()

    # Obter informações adicionais para o formulário de cadastro de funcionários
    empresas = Empresa.objects.all()
    cargos = Cargo.objects.all()
    horarios = Horario.objects.all()
    departamentos = Departamento.objects.all()

    # Lista todos os funcionários
    funcionarios_list = Funcionario.objects.all()

    # Criar o campo fullname para cada funcionário
    for funcionario in funcionarios_list:
        funcionario.fullname = f'{funcionario.nome}-{funcionario.sobrenome}' if funcionario.sobrenome else funcionario.nome
        funcionario.fullname_slug = slugify(funcionario.fullname)

    funcionarios = Funcionario.objects.all().values('id', 'nome', 'sobrenome')
    print("Funcionários disponíveis:", list(funcionarios), "\n")

    # Retorna um dicionário com todos os dados
    return {
        'form_funcionario': form_funcionario,
        'form_usuario': form_usuario,
        'form_grupo': form_grupo,
        'empresas': empresas,
        'cargos': cargos,
        'horarios': horarios,
        'departamentos': departamentos,
        'funcionarios_list': funcionarios_list,
        'funcionarios': funcionarios
    }


# ---------- RENDER ALL FORMS -----------------------
def render_all_forms(request):
    mensagem = {'texto': 'none', 'classe': ''}

    # Definição dos formulários
    context_data = get_all_forms_and_objects()

    print("Método HTTP:", request.method, "\n")  # Verificar qual método HTTP está sendo utilizado

    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        print("POST recebido com os dados:", request.POST, "\n")  # Exibir todos os dados POST recebidos

        if form_type == 'cadastro_funcionario':
            print("Formulário de Funcionário enviado\n")
            funcionario_data = {
                'nome': request.POST.get('nome'),
                'sobrenome': request.POST.get('sobrenome'),
                'cpf': request.POST.get('cpf'),
                'empresa': request.POST.get('empresa'),
                'horario': request.POST.get('horario'),
                'cargo': request.POST.get('cargo'),
                'departamento': request.POST.get('departamento'),
            }
            resultado = get_funcionario(funcionario_data)
            if resultado == 'success':
                mensagem = {'texto': 'Funcionário cadastrado com sucesso!', 'classe': 'success'}
            else:
                mensagem = {'texto': 'Erro ao cadastrar funcionário.', 'classe': 'error'}
            print("Resultado do cadastro de funcionário:", mensagem, "\n")
        
        elif form_type == 'cadastrar_usuario':
            print("Formulário de Usuário enviado\n")
            usuario_data = {
                'nome': request.POST.get('nome'),
                'sobrenome': request.POST.get('sobrenome'),
                'email': request.POST.get('email'),
                'senha': request.POST.get('senha'),
                'funcionario': request.POST.get('funcionario'),
            }
            funcionario_id = usuario_data.get('funcionario')
            funcionario_id = int(funcionario_id) if funcionario_id else None
            resultado = create_user(usuario_data, funcionario_id)
            if resultado == 'success':
                mensagem = {'texto': 'Usuário cadastrado com sucesso!', 'classe': 'success'}
            else:
                mensagem = {'texto': 'Erro ao cadastrar usuário.', 'classe': 'error'}
            print("Resultado do cadastro de usuário:", mensagem, "\n")
        
        elif form_type == 'criar_empresa':
            print("Formulário de Empresa enviado\n")
            empresa_data = {
                'nome': request.POST.get('nome'),
                'cnpj': request.POST.get('cnpj'),
                'endereco': request.POST.get('endereco'),
            }
            mensagem = get_empresa(empresa_data)
            print("Resultado do cadastro de empresa:", mensagem, "\n")
        
        elif form_type == 'criar_horario':
            print("Formulário de Horário enviado\n")
            horario_data = {
                'nome': request.POST.get('nome'),
                'horario_entrada': request.POST.get('horario_entrada'),
                'horario_saida': request.POST.get('horario_saida'),
            }
            mensagem = get_horario(horario_data)
            print("Resultado do cadastro de horário:", mensagem, "\n")
        
        elif form_type == 'criar_departamento':
            print("Formulário de Departamento enviado\n")
            departamento_data = {
                'nome': request.POST.get('nome'),
            }
            mensagem = get_departamento(departamento_data)
            print("Resultado do cadastro de departamento:", mensagem, "\n")
        
        elif form_type == 'criar_cargo':
            print("Formulário de Cargo enviado\n")
            cargo_data = {
                'nome': request.POST.get('nome'),
                'nivel': request.POST.get('nivel'),
            }
            mensagem = get_cargo(cargo_data)
            print("Resultado do cadastro de cargo:", mensagem, "\n")

        elif form_type == 'delete_funcionario':
            print("Formulário de Exclusão de Funcionário enviado\n")
            funcionario_id = request.POST.get('funcionario_id')
            resultado = delete_funcionario(funcionario_id)
            mensagem = resultado  # Recebe o resultado da função de exclusão
        # Repetir o mesmo padrão para outros tipos de formulários
        context_data = get_all_forms_and_objects()

    print(f'\nMensagem de alerta: {mensagem}\n')
    context_data.update({
        'mensagem': mensagem['texto'],
        'classe_mensagem': mensagem['classe'],
    })
    # Renderiza o template com o contexto atualizado
    return render(request, 'funcionarios/all_forms_cia.html', context_data)