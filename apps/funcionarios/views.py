# Django imports
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User, Group
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.http import JsonResponse, HttpResponse
from django.utils.text import slugify
from django.core.files.storage import default_storage
from django.conf import settings
from django.contrib import messages
from django.utils.dateparse import parse_date

# Python standard library imports
from datetime import datetime, date
import json
import logging
import os

# Third-party imports
# (Nenhuma importação de terceiros neste momento)

# Local imports
from .forms import FuncionarioForm, UserForm, FuncionarioFullForm, CustomUserForm, UserGroupForm
from .models import Funcionario, Empresa, Horario, Departamento, Cargo, Loja
from custom_tags_app.permissions import check_access
from setup.utils import verificar_autenticacao

# Configuração do logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# ----- Gets de funcionarios -----------
from django.db import transaction
from .models import Funcionario
from datetime import date

def post_funcionario(dados):
    """Processa o formulário de cadastro de funcionário, cria e salva o funcionário, e retorna uma mensagem de sucesso ou erro."""
    print("\n----- Iniciando post_funcionario -----")
    print("Dados recebidos:", dados)

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
    }

    # Combina dados recebidos com valores padrão
    dados_completos = {**valores_padrao, **dados}
    print("Dados completos:", dados_completos)

    try:
        with transaction.atomic():
            funcionario = Funcionario(
                nome=dados_completos['nome'],
                sobrenome=dados_completos['sobrenome'],
                cpf=dados_completos['cpf'],
                cep=dados_completos.get('cep', ''),
                endereco=dados_completos.get('endereco', ''),
                bairro=dados_completos.get('bairro', ''),
                cidade=dados_completos.get('cidade', ''),
                estado=dados_completos.get('estado', ''),
                empresa_id=dados_completos.get('empresa'),
                horario_id=dados_completos.get('horario'),
                cargo_id=dados_completos.get('cargo'),
                departamento_id=dados_completos.get('departamento'),
                loja_id=dados_completos.get('loja'),
                foto=dados_completos.get('foto'),
                **{k: v for k, v in valores_padrao.items() if k not in dados_completos}
            )
            funcionario.save()
            print(f"Funcionário {funcionario.nome} {funcionario.sobrenome} salvo com sucesso.")
            mensagem = {
                'texto': f'Funcionário {funcionario.nome} {funcionario.sobrenome} cadastrado com sucesso!',
                'classe': 'success'
            }
    except Exception as e:
        print(f"Erro ao salvar o funcionário: {str(e)}")
        mensagem = {
            'texto': f'Erro ao cadastrar o funcionário. Detalhes: {str(e)}',
            'classe': 'error'
        }

    print("Mensagem final:", mensagem)
    print("----- Finalizando post_funcionario -----\n")
    return mensagem


# ------ CRIAR USUARIO -------------------
def post_usuario(form_data, funcionario):
    print("\n\n----- Iniciando post_usuario -----\n")
    print("Dados do formulário:", form_data)
    print("Funcionário associado:", funcionario)

    print("Criando instância do modelo User...")
    usuario = User(
        username=form_data['username'],
        first_name=funcionario.nome,
        last_name=funcionario.sobrenome,
        email=form_data['email'],
    )
    print("Definindo senha...")
    usuario.set_password(form_data['password'])

    print("Usuário criado:", usuario)
    print("\n----- Finalizando post_usuario -----\n")
    return usuario

def create_user(usuario_data, funcionario_id):
    """Processa o formulário de cadastro de usuário e retorna uma mensagem de sucesso ou erro."""
    print("\n\n----- Iniciando create_user -----\n")
    print("Dados do usuário:", usuario_data)
    print("ID do funcionário:", funcionario_id)

    mensagem = {'texto': 'none', 'classe': ''}

    print("Verificando se todos os campos obrigatórios estão preenchidos...")
    if not all([usuario_data.get('username'), usuario_data.get('email'), usuario_data.get('password')]):
        mensagem['texto'] = 'Todos os campos são obrigatórios.'
        mensagem['classe'] = 'error'
        print("Erro: Campos obrigatórios não preenchidos")
        return mensagem

    try:
        # Primeiro, verificamos se o funcionário existe e obtemos seus dados
        if funcionario_id:
            try:
                funcionario = Funcionario.objects.select_related('cargo', 'departamento').get(id=funcionario_id)
                print(f"Funcionário encontrado: {funcionario.nome} {funcionario.sobrenome}")
                print(f"Cargo: {funcionario.cargo.grupo.name if funcionario.cargo else 'Nenhum'}")
                print(f"Departamento: {funcionario.departamento.grupo.name if funcionario.departamento else 'Nenhum'}")
            except Funcionario.DoesNotExist:
                mensagem['texto'] = 'Funcionário não encontrado.'
                mensagem['classe'] = 'error'
                return mensagem

        # Criando o usuário
        print("Criando usuário...")
        usuario = User.objects.create_user(
            username=usuario_data['username'],
            email=usuario_data['email'],
            password=usuario_data['password']
        )
        print("Usuário criado com sucesso:", usuario)

        if funcionario_id:
            # Associando o usuário ao funcionário
            funcionario.usuario = usuario
            funcionario.save()
            print("Usuário associado ao funcionário com sucesso")

            # Adicionando usuário aos grupos correspondentes
            grupos_para_adicionar = []
            
            # Adiciona ao grupo do cargo se existir
            if funcionario.cargo and funcionario.cargo.grupo:
                grupos_para_adicionar.append(funcionario.cargo.grupo)
                print(f"Adicionando ao grupo do cargo: {funcionario.cargo.grupo.name}")
            
            # Adiciona ao grupo do departamento se existir
            if funcionario.departamento and funcionario.departamento.grupo:
                grupos_para_adicionar.append(funcionario.departamento.grupo)
                print(f"Adicionando ao grupo do departamento: {funcionario.departamento.grupo.name}")

            # Adiciona o usuário a todos os grupos necessários
            if grupos_para_adicionar:
                usuario.groups.add(*grupos_para_adicionar)
                print(f"Usuário adicionado aos grupos: {[g.name for g in grupos_para_adicionar]}")

        mensagem['texto'] = f'Usuário {usuario.username} cadastrado com sucesso e adicionado aos grupos correspondentes!'
        mensagem['classe'] = 'success'

    except ValidationError as e:
        print("Erro de validação ao criar usuário:", str(e))
        mensagem['texto'] = f'Erro ao cadastrar o usuário: {e}'
        mensagem['classe'] = 'error'
    except Exception as e:
        print("Erro ao criar usuário:", str(e))
        mensagem['texto'] = f'Erro ao cadastrar o usuário. Tente novamente mais tarde. Detalhes: {e}'
        mensagem['classe'] = 'error'

    print("Mensagem final:", mensagem)
    print("\n----- Finalizando create_user -----\n")
    return mensagem




# ------- ASSOCIAR GROUPOS AO USER ------------------------

def associar_grupos(form):
    print("\n\n----- Iniciando associar_grupos -----\n")
    mensagem = {'texto': 'none', 'classe': ''}

    print("Verificando validade do formulário...")
    if form.is_valid():
        print("Formulário válido. Processando dados...")
        user_id = form.cleaned_data['user'].id
        print(f"ID do usuário: {user_id}")

        selected_groups_ids = form.cleaned_data['groups']
        print(f"IDs dos grupos selecionados: {selected_groups_ids}")

        selected_groups = Group.objects.filter(id__in=selected_groups_ids)
        print(f"Grupos selecionados: {[group.name for group in selected_groups]}")

        try:
            user = User.objects.get(id=user_id)
            print(f"Usuário encontrado: {user.username}")
        except User.DoesNotExist:
            print("Erro: Usuário não encontrado.")
            return {'texto': 'Usuário não encontrado.', 'classe': 'error'}

        user_groups = user.groups.all()
        print(f"Grupos atuais do usuário: {[group.name for group in user_groups]}")

        print("Adicionando novos grupos ao usuário...")
        for group in selected_groups:
            if group not in user_groups:
                user.groups.add(group)
                print(f"Grupo '{group.name}' adicionado.")

        print("Removendo grupos desmarcados...")
        for group in user_groups:
            if group not in selected_groups:
                user.groups.remove(group)
                print(f"Grupo '{group.name}' removido.")

        mensagem = {
            'texto': 'Associação de grupos atualizada com sucesso.',
            'classe': 'success'
        }
    else:
        print("Erro: Formulário inválido.")
        mensagem = {
            'texto': 'Formulário inválido. Verifique os dados e tente novamente.',
            'classe': 'error'
        }
    
    print(f"Mensagem final: {mensagem}")
    print("\n----- Finalizando associar_grupos -----\n")
    return mensagem

# ------------------ EDITAÇÃO DE FUNCIONARIO E USER --------------------------

def render_ficha_funcionario(request, id, nome_sobrenome):
    print(f"\n\n----- Iniciando render_ficha_funcionario para ID: {id} -----\n")
    
    print(f"Buscando funcionário com ID: {id}")
    funcionario = get_object_or_404(Funcionario, id=id)
    print(f"Funcionário encontrado: {funcionario.nome} {funcionario.sobrenome}")
    
    user = funcionario.usuario
    form_user = None
    
    if user:
        print(f"Usuário associado: {user.username}")
        form_user = CustomUserForm(instance=user)
    else:
        print("Nenhum usuário associado ao funcionário")
    
    print("Carregando formulários...")
    form_funcionario = FuncionarioFullForm(instance=funcionario)

    context = {
        'form_funcionario': form_funcionario,
        'form_user': form_user,
        'funcionario': funcionario,
        'has_user': user is not None  # Adiciona flag para verificar se existe usuário
    }
    print("Contexto preparado para renderização.")

    print("\n----- Finalizando render_ficha_funcionario -----\n")
    return render(request, 'funcionarios/ficha_funcionario.html', context)

def update_funcionario(request, id):
    print(f"\n\n----- Iniciando update_funcionario para ID: {id} -----\n")
    
    print(f"Buscando funcionário com ID: {id}")
    funcionario = get_object_or_404(Funcionario, id=id)
    print(f"Funcionário encontrado: {funcionario.nome} {funcionario.sobrenome}")
    
    if request.method == 'POST':
        print("Método POST detectado. Processando formulário...")
        form_funcionario = FuncionarioFullForm(request.POST, request.FILES, instance=funcionario)
        
        if form_funcionario.is_valid():
            print("Formulário válido. Atualizando dados...")
            funcionario = form_funcionario.save(commit=False)
            funcionario.status = 'Ativo' if request.POST.get('status') == 'on' else 'Inativo'
            
            # Tratamento específico para a foto
            if 'foto' in request.FILES:
                funcionario.foto = request.FILES['foto']
            elif 'foto-clear' in request.POST:
                funcionario.foto = None
            
            try:
                funcionario.save()
                print("Funcionário atualizado com sucesso.")
                messages.success(request, f'Funcionário {funcionario.nome} {funcionario.sobrenome} atualizado com sucesso!')
                logger.info(f'Funcionário {funcionario.nome} {funcionario.sobrenome} atualizado com sucesso!')
            except Exception as e:
                error_message = f'Erro ao atualizar o funcionário: {e}'
                print(f"Erro: {error_message}")
                messages.error(request, error_message)
                logger.error(error_message)
        else:
            print("Formulário inválido. Erros encontrados:")
            for field in form_funcionario.errors:
                for error in form_funcionario.errors[field]:
                    error_message = f'Erro no campo {field}: {error}'
                    print(error_message)
                    messages.error(request, error_message)
                    logger.warning(error_message)
    else:
        form_funcionario = FuncionarioFullForm(instance=funcionario)

    print("\n----- Finalizando update_funcionario -----\n")
    return render(request, 'funcionarios/ficha_funcionario.html', {
        'form_funcionario': form_funcionario,
        'funcionario': funcionario,
    })

def update_user(request, id):
    print(f"\n\n----- Iniciando update_user para ID: {id} -----\n")
    
    print(f"Buscando funcionário com ID: {id}")
    funcionario = post_object_or_404(Funcionario, id=id)
    print(f"Funcionário encontrado: {funcionario.nome} {funcionario.sobrenome}")
    
    user = funcionario.usuario
    print(f"Usuário associado: {user.username}")

    if request.method == 'POST':
        print("Método POST detectado. Processando formulário...")
        form_user = CustomUserForm(request.POST, instance=user)
        if form_user.is_valid():
            print("Formulário válido. Atualizando usuário...")
            form_user.save()
            print("Usuário atualizado com sucesso.")
            messages.success(request, f'Usuário {user.username} atualizado com sucesso!')
        else:
            print("Erro: Formulário inválido.")
            messages.error(request, 'Erro ao atualizar o usuário.')
        
        print("Mensagens de feedback:")
        for message in messages.post_messages(request):
            print(f"{message.level_tag.upper()}: {message.message}")

    print("\n----- Finalizando update_user -----\n")
    return redirect('funcionarios:all_forms')


# ----------------------------------------------------------------------------------------------------------------
def post_empresa(form_data):
    """Cria uma nova empresa com os parâmetros fornecidos e retorna uma mensagem de sucesso ou erro."""
    print("\n\n----- Iniciando post_empresa -----\n")
    print("Dados recebidos:", form_data)

    nome = form_data.get('nome')
    cnpj = form_data.get('cnpj')
    endereco = form_data.get('endereco')
    print(f"Nome: {nome}, CNPJ: {cnpj}, Endereço: {endereco}")

    if nome and cnpj and endereco:
        try:
            print("Criando nova empresa...")
            empresa = Empresa.objects.create(nome=nome, cnpj=cnpj, endereco=endereco)
            print(f"Empresa criada com ID: {empresa.id}")
            mensagem = {
                'texto': f"Empresa '{nome}' foi adicionada com sucesso!",
                'classe': 'success'
            }
            print("Mensagem de sucesso:", mensagem['texto'])
        except Exception as e:
            mensagem = {
                'texto': f"Erro ao adicionar a empresa. Detalhes: {e}",
                'classe': 'error'
            }
            print("Erro ao adicionar empresa:", str(e))
    else:
        mensagem = {
            'texto': "Faltam parâmetros para criar a empresa.",
            'classe': 'error'
        }
        print("Mensagem de erro:", mensagem['texto'])

    print("\n----- Finalizando post_empresa -----\n")
    return mensagem

def post_horario(form_data):
    """Cria um novo horário com os parâmetros fornecidos e retorna uma mensagem de sucesso ou erro."""
    print("\n\n----- Iniciando post_horario -----\n")
    print("Dados recebidos:", form_data)

    nome = form_data.get('nome')
    horario_entrada = form_data.get('horario_entrada')
    horario_saida = form_data.get('horario_saida')
    print(f"Nome: {nome}, Entrada: {horario_entrada}, Saída: {horario_saida}")

    if nome and horario_entrada and horario_saida:
        try:
            print("Criando novo horário...")
            horario = Horario.objects.create(nome=nome, horario_entrada=horario_entrada, horario_saida=horario_saida)
            print(f"Horário criado com ID: {horario.id}")
            mensagem = {
                'texto': f"Horário '{nome}' foi adicionado com sucesso!",
                'classe': 'success'
            }
            print("Mensagem de sucesso:", mensagem['texto'])
        except Exception as e:
            mensagem = {
                'texto': f"Erro ao adicionar o horário. Detalhes: {e}",
                'classe': 'error'
            }
            print("Erro ao adicionar horário:", str(e))
    else:
        mensagem = {
            'texto': "Faltam parâmetros para criar o horário.",
            'classe': 'error'
        }
        print("Mensagem de erro:", mensagem['texto'])

    print("\n----- Finalizando post_horario -----\n")
    return mensagem

def delete_loja(loja_id):
    """Exclui uma loja com base no ID fornecido."""
    print("\n\n----- Iniciando delete_loja -----\n")
    print(f"Tentando excluir loja com ID: {loja_id}")
    
    try:
        loja = Loja.objects.get(id=loja_id)
        print(f"Loja encontrada: {loja.nome}")
        
        # Se houver uma logo, excluir o arquivo
        if loja.logo:
            loja.logo.delete()
        
        loja.delete()
        mensagem = {
            'texto': f'Loja "{loja.nome}" excluída com sucesso!',
            'classe': 'success'
        }
        print("Loja excluída com sucesso")
    except Loja.DoesNotExist:
        mensagem = {
            'texto': 'Loja não encontrada.',
            'classe': 'error'
        }
        print("Erro: Loja não encontrada")
    except Exception as e:
        mensagem = {
            'texto': f'Erro ao excluir loja: {str(e)}',
            'classe': 'error'
        }
        print(f"Erro ao excluir loja: {str(e)}")

    print("\n----- Finalizando delete_loja -----\n")
    return mensagem

def post_departamento(form_data):
    """Cria um novo departamento com os parâmetros fornecidos e retorna uma mensagem de sucesso ou erro."""
    print("\n\n----- Iniciando post_departamento -----\n")
    print("Dados recebidos:", form_data)

    nome = form_data.get('nome')
    print(f"Nome do departamento recebido: {nome}")

    if nome:
        try:
            print("Criando novo grupo...")
            grupo = Group.objects.create(name=nome)
            print(f"Grupo criado com ID: {grupo.id}")
            
            print("Criando novo departamento...")
            departamento = Departamento.objects.create(grupo=grupo)
            print(f"Departamento criado com ID: {departamento.id}")
            
            mensagem = {
                'texto': f"Departamento '{nome}' foi adicionado com sucesso! ID do Grupo: {grupo.id}, ID do Departamento: {departamento.id}",
                'classe': 'success'
            }
            print("Mensagem de sucesso:", mensagem['texto'])
        except Exception as e:
            mensagem = {
                'texto': f"Erro ao adicionar o departamento. Detalhes: {e}",
                'classe': 'error'
            }
            print("Erro ao adicionar departamento:", str(e))
    else:
        mensagem = {
            'texto': "Faltam parâmetros para criar o departamento.",
            'classe': 'error'
        }
        print("Mensagem de erro:", mensagem['texto'])

    print("\n----- Finalizando post_departamento -----\n")
    return mensagem

def post_loja(form_data):
    """Cria uma nova loja com os parâmetros fornecidos e retorna uma mensagem de sucesso ou erro."""
    print("\n\n----- Iniciando post_loja -----\n")
    print("Dados recebidos:", form_data)

    nome = form_data.get('nome')
    empresa_id = form_data.get('empresa')
    logo = form_data.get('logo')
    print(f"Nome da loja: {nome}, ID da empresa: {empresa_id}")

    if nome and empresa_id:
        try:
            print(f"Buscando empresa com ID: {empresa_id}")
            empresa = Empresa.objects.get(id=empresa_id)
            print(f"Empresa encontrada: {empresa.nome}")
            
            print("Criando nova loja...")
            loja = Loja(
                nome=nome, 
                empresa=empresa,
                logo=logo if logo else None
            )
            loja.save()
            print(f"Loja criada com ID: {loja.id}")
            
            mensagem = {
                'texto': f"Loja '{loja.nome}' foi adicionada com sucesso para a empresa '{empresa.nome}'!",
                'classe': 'success'
            }
            print("Mensagem de sucesso:", mensagem['texto'])
        except Empresa.DoesNotExist:
            mensagem = {
                'texto': "Erro: A empresa selecionada não existe.",
                'classe': 'error'
            }
            print("Erro: Empresa não encontrada")
        except Exception as e:
            mensagem = {
                'texto': f"Erro ao adicionar a loja. Detalhes: {e}",
                'classe': 'error'
            }
            print("Erro ao adicionar loja:", str(e))
    else:
        mensagem = {
            'texto': "Faltam parâmetros para criar a loja. Nome e empresa são obrigatórios.",
            'classe': 'error'
        }
        print("Mensagem de erro:", mensagem['texto'])

    print("\n----- Finalizando post_loja -----\n")
    return mensagem

from django.db import IntegrityError

def post_cargo(cargo_data):
    print("\n----- Iniciando post_cargo -----\n")
    
    nome = cargo_data.get('nome')
    nivel = cargo_data.get('nivel')
    
    print(f"Dados recebidos: {cargo_data}")
    print(f"Nome do cargo recebido: {nome}")
    print(f"Nível do cargo: {nivel}")
    
    if not nome or not nivel:
        mensagem = {'texto': 'Faltam parâmetros para criar o cargo.', 'classe': 'error'}
        print(f"Mensagem de erro: {mensagem['texto']}")
        print("\n----- Finalizando post_cargo -----\n")
        return mensagem
    
    try:
        # Verificar se já existe um grupo com este nome
        grupo_nome = f"{nome} - {nivel}"
        grupo, created = Group.objects.get_or_create(name=grupo_nome)
        
        if created:
            print(f"Novo grupo criado: {grupo_nome}")
        else:
            print(f"Grupo existente encontrado: {grupo_nome}")

        # Criar o cargo
        cargo, created = Cargo.objects.get_or_create(
            nome=nome,
            nivel=nivel,
            defaults={'grupo': grupo}
        )

        if created:
            print(f"Novo cargo criado: {cargo}")
            mensagem = {
                'texto': f"Cargo '{nome}' (Nível: {nivel}) foi adicionado com sucesso! ID do Cargo: {cargo.id}",
                'classe': 'success'
            }
        else:
            print(f"Cargo já existente: {cargo}")
            mensagem = {
                'texto': f"O cargo '{nome}' (Nível: {nivel}) já existe.",
                'classe': 'info'
            }

    except IntegrityError as e:
        mensagem = {
            'texto': f"Erro de integridade ao adicionar o cargo: {e}",
            'classe': 'error'
        }
        print(f"Erro de integridade: {e}")
    except Exception as e:
        mensagem = {
            'texto': f"Erro ao adicionar o cargo. Detalhes: {e}",
            'classe': 'error'
        }
        print(f"Erro ao adicionar cargo: {e}")

    print("\n----- Finalizando post_cargo -----\n")
    return mensagem


def delete_funcionario(funcionario_id):
    print("\n\n----- Iniciando delete_funcionario -----\n")
    print(f"Tentando excluir funcionário com ID: {funcionario_id}")
    
    try:
        funcionario = Funcionario.objects.get(id=funcionario_id)
        print(f"Funcionário encontrado: {funcionario.nome} {funcionario.sobrenome}")
        funcionario.delete()
        mensagem = {'texto': 'Funcionário excluído com sucesso!', 'classe': 'success'}
        print("Funcionário excluído com sucesso")
    except Funcionario.DoesNotExist:
        mensagem = {'texto': 'Funcionário não encontrado.', 'classe': 'error'}
        print("Erro: Funcionário não encontrado")
    except Exception as e:
        mensagem = {'texto': f'Erro ao excluir funcionário: {str(e)}', 'classe': 'error'}
        print(f"Erro ao excluir funcionário: {str(e)}")

    print("\n----- Finalizando delete_funcionario -----\n")
    return mensagem

def get_all_forms_and_objects(request):
    """
    Função para centralizar a obtenção de formulários e objetos utilizados em 'render_all_forms'.
    Retorna um dicionário com todos os formulários e objetos adicionais.
    """
    print("\n\n----- Iniciando get_all_forms_and_objects -----\n")

    '''
    Formulários
    '''
    print("Definindo formulários...")
    # Criação dos formulários necessários
    form_funcionario = FuncionarioForm()
    form_usuario = UserForm()
    form_grupo = UserGroupForm()

    '''
    Consultas ao banco de dados
    '''
    # Obtendo empresas
    print("Obtendo empresas...")
    empresas = Empresa.objects.all()
    print(f"Número de empresas encontradas: {empresas.count()}")

    # Obtendo horários
    print("Obtendo horários...")
    horarios = Horario.objects.all()
    print(f"Número de horários encontrados: {horarios.count()}")

    # Obtendo lojas
    print("Obtendo lojas...")
    lojas = Loja.objects.all()
    print(f"Número de lojas encontradas: {lojas.count()}")

    # Obtendo usuários e grupos
    print("Obtendo usuários e grupos...")
    usuarios = User.objects.prefetch_related('groups').all()
    all_groups = Group.objects.all()
    print(f"Número de usuários encontrados: {usuarios.count()}")
    print(f"Número de grupos encontrados: {all_groups.count()}")

    '''
    Processamento de dados
    '''
    # Criando lista de cargos
    print("Criando lista de cargos...")
    cargo_list = [
        {
            'nome': cargo.grupo.name,
            'id_grupo': cargo.grupo.id,
            'id_cargo': cargo.id,
            'nivel': cargo.nivel
        } for cargo in Cargo.objects.select_related('grupo').all()
    ]
    print(f"Número de cargos encontrados: {len(cargo_list)}")

    # Criando lista de departamentos
    print("Criando lista de departamentos...")
    departamento_list = [
        {
            'nome': departamento.grupo.name,
            'id_grupo': departamento.grupo.id,
            'id_departamento': departamento.id
        } for departamento in Departamento.objects.select_related('grupo').all()
    ]
    print(f"Número de departamentos encontrados: {len(departamento_list)}")

    # Obtendo lista de funcionários
    print("Obtendo lista de funcionários...")
    funcionarios = Funcionario.objects.all()
    funcionarios_list = [
        {
            'id': f.id,
            'fullname': f'{f.nome} {f.sobrenome}',
            'cpf': f.cpf
        } for f in funcionarios
    ]
    print(f"Número de funcionários encontrados: {len(funcionarios_list)}")

    # Criando dicionário de grupos de usuários
    user_groups_dict = {user.id: list(user.groups.values_list('id', flat=True)) for user in usuarios}
    print(f"Dicionário de grupos de usuários criado")

    '''
    Preparação dos dados para formulários de departamento e cargo
    '''
    print("Preparando dados para formulários de departamento e cargo...")
    
    # Obtendo departamentos
    departamentos = Departamento.objects.select_related('grupo').all()
    departamentos_list = [
        {
            'id': dep.id,
            'nome': dep.grupo.name
        } for dep in departamentos
    ]
    print(f"Número de departamentos preparados: {len(departamentos_list)}")

    # Obtendo cargos e níveis
    cargos = Cargo.objects.select_related('grupo').all()
    cargos_list = [
        {
            'id': cargo.id,
            'nome': cargo.grupo.name,
            'nivel': cargo.nivel
        } for cargo in cargos
    ]
    niveis_list = sorted(set(cargo.nivel for cargo in cargos))
    print(f"Número de cargos preparados: {len(cargos_list)}")
    print(f"Níveis de cargo encontrados: {niveis_list}")

    '''
    Preparação do contexto
    '''
    # Montagem do dicionário de contexto com todos os dados obtidos
    context_data = {
        'form_funcionario': form_funcionario,
        'form_usuario': form_usuario,
        'form_grupo': form_grupo,
        'empresas': empresas,
        'cargo_list': cargo_list,
        'departamento_list': departamento_list,
        'horarios': horarios,
        'funcionarios_list': funcionarios_list,
        'funcionarios': funcionarios,
        'departamentos': departamento_list,
        'cargos': cargo_list,
        'lojas': lojas,
        'usuarios': usuarios,
        'groups': all_groups,
        'user_groups': user_groups_dict,
        'departamentos_form': departamentos_list,
        'cargos_form': cargos_list,
        'niveis_cargo': niveis_list,
    }

    print("\n----- Finalizando get_all_forms_and_objects -----\n")
    return context_data

def delete_cargo(cargo_id):
    """Exclui um cargo com base no ID fornecido."""
    print("\n\n----- Iniciando delete_cargo -----\n")
    print(f"Tentando excluir cargo com ID: {cargo_id}")
    
    try:
        cargo = Cargo.objects.select_related('grupo').get(id=cargo_id)
        nome_cargo = cargo.nome
        nivel_cargo = cargo.nivel
        
        # Verifica se existem funcionários usando este cargo
        if Funcionario.objects.filter(cargo=cargo).exists():
            mensagem = {
                'texto': f'Não é possível excluir o cargo pois existem funcionários associados a ele.',
                'classe': 'error'
            }
            print("Erro: Cargo possui funcionários associados")
            return mensagem
        
        # Exclui o grupo associado ao cargo
        if cargo.grupo:
            cargo.grupo.delete()
            print(f"Grupo associado excluído: {cargo.grupo.name}")
        
        # Exclui o cargo
        cargo.delete()
        mensagem = {
            'texto': f'Cargo "{nome_cargo} - {nivel_cargo}" excluído com sucesso!',
            'classe': 'success'
        }
        print("Cargo excluído com sucesso")
        
    except Cargo.DoesNotExist:
        mensagem = {
            'texto': 'Cargo não encontrado.',
            'classe': 'error'
        }
        print("Erro: Cargo não encontrado")
    except Exception as e:
        mensagem = {
            'texto': f'Erro ao excluir cargo: {str(e)}',
            'classe': 'error'
        }
        print(f"Erro ao excluir cargo: {str(e)}")

    print("\n----- Finalizando delete_cargo -----\n")
    return mensagem

# ---------- RENDER ALL FORMS -----------------------
@verificar_autenticacao
@check_access(departamento='RH', nivel_minimo='ESTAGIO')
def render_all_forms(request):
    """
    Renderiza a página com todos os formulários da CIA e processa os formulários enviados.
    Requer autenticação e acesso ao departamento CIA (nível mínimo: ESTAGIO).
    """
    print("\n\n----- Iniciando render_all_forms -----\n")
    
    mensagem = {'texto': '', 'classe': ''}
    
    # Obter todos os formulários e objetos inicialmente
    context_data = get_all_forms_and_objects(request)
    
    print("\nMétodo HTTP:", request.method)

    if request.method == 'POST':
        print("\nProcessando requisição POST...")
        form_type = request.POST.get('form_type')
        print(f"Tipo de formulário: {form_type}")
        print("Dados POST recebidos:", request.POST)
        print("Arquivos recebidos:", request.FILES)

        if form_type == 'cadastro_funcionario':
            print("\nProcessando cadastro de funcionário...")
            funcionario_data = {
                'nome': request.POST.get('nome'),
                'sobrenome': request.POST.get('sobrenome'),
                'cpf': request.POST.get('cpf'),
                'empresa': request.POST.get('empresa'),
                'horario': request.POST.get('horario'),
                'cargo': request.POST.get('cargo'),
                'departamento': request.POST.get('departamento'),
                'loja': request.POST.get('loja'),
                'foto': request.FILES.get('foto'),
            }
            
            mensagem = post_funcionario(funcionario_data)
            print("Resultado do cadastro de funcionário:", mensagem)
        
        elif form_type == 'cadastrar_usuario':
            print("\nProcessando cadastro de usuário...")
            usuario_data = {
                'username': request.POST.get('username'),
                'email': request.POST.get('email'),
                'password': request.POST.get('password'),
                'funcionario': request.POST.get('funcionario'),
            }
            funcionario_id = usuario_data.get('funcionario')
            funcionario_id = int(funcionario_id) if funcionario_id else None

            mensagem = create_user(usuario_data, funcionario_id)
            print("Resultado do cadastro de usuário:", mensagem)
        
        elif form_type == 'criar_empresa':
            print("\nProcessando criação de empresa...")
            empresa_data = {
                'nome': request.POST.get('nome'),
                'cnpj': request.POST.get('cnpj'),
                'endereco': request.POST.get('endereco'),
            }
            mensagem = post_empresa(empresa_data)
            print("Resultado da criação de empresa:", mensagem)
        
        elif form_type == 'criar_horario':
            print("\nProcessando criação de horário...")
            horario_data = {
                'nome': request.POST.get('nome'),
                'horario_entrada': request.POST.get('horario_entrada'),
                'horario_saida': request.POST.get('horario_saida'),
            }
            mensagem = post_horario(horario_data)
            print("Resultado da criação de horário:", mensagem)
        
        elif form_type == 'criar_departamento':
            print("\nProcessando criação de departamento...")
            departamento_data = {
                'nome': request.POST.get('nome'),
            }
            mensagem = post_departamento(departamento_data)
            print("Resultado da criação de departamento:", mensagem)
        
        elif form_type == 'criar_cargo':
            print("\nProcessando criação de cargo...")
            cargo_data = {
                'nome': request.POST.get('nome'),
                'nivel': request.POST.get('nivel'),
            }
            mensagem = post_cargo(cargo_data)
            print("Resultado da criação de cargo:", mensagem)

        elif form_type == 'delete_funcionario':
            print("\nProcessando exclusão de funcionário...")
            funcionario_id = request.POST.get('funcionario_id')
            resultado = delete_funcionario(funcionario_id)
            mensagem = resultado
            print("Resultado da exclusão de funcionário:", mensagem)

        elif form_type == 'criar_loja':
            print("\nProcessando criação de loja...")
            loja_data = {
                'nome': request.POST.get('nome'),
                'empresa': request.POST.get('empresa'),
                'logo': request.FILES.get('logo'),  # Adicionando o campo logo
            }
            mensagem = post_loja(loja_data)
            print("Resultado da criação de loja:", mensagem)

        elif form_type == 'associar_grupos':
            print("\nProcessando associação de grupos...")
            form = UserGroupForm(request.POST)
            mensagem = associar_grupos(form)
            print("Resultado da associação de grupos:", mensagem)

        elif form_type == 'delete_loja':
            print("\nProcessando exclusão de loja...")
            loja_id = request.POST.get('loja_id')
            mensagem = delete_loja(loja_id)
            print("Resultado da exclusão de loja:", mensagem)

        elif form_type == 'excluir_cargo':
            cargo_id = request.POST.get('cargo_id')
            mensagem = delete_cargo(cargo_id)

        # Atualizar context_data após o processamento do formulário
        context_data = get_all_forms_and_objects(request)

    else:
        print("\nRequisição não é POST. Usando dados iniciais...")

    # Adicionar mensagem ao contexto
    context_data['mensagem'] = mensagem

    print("\nContexto final dos dados:")
    print(context_data)

    print("\n----- Finalizando render_all_forms -----\n")
    return render(request, 'funcionarios/all_forms_cia.html', context_data)

def get_lojas_by_empresa(request, empresa_id):
    """Retorna as lojas de uma empresa específica"""
    lojas = Loja.objects.filter(empresa_id=empresa_id).values('id', 'nome')
    return JsonResponse(list(lojas), safe=False)
