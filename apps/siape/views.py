# Django imports
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, F, OuterRef, Q, Subquery, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

# Python built-in imports
import csv
import io
import logging
import os
from datetime import datetime, time, timedelta
from decimal import Decimal

# Third party imports
import pandas as pd

# Local imports
from custom_tags_app.permissions import check_access
from setup.utils import verificar_autenticacao
from .models import *
from apps.inss.models import *
from apps.funcionarios.models import *

# Configurando o logger para registrar atividades e erros no sistema
logger = logging.getLogger(__name__)

# Funções auxiliares
def normalize_cpf(cpf):
    """
    Normaliza o CPF para uma string de 11 dígitos
    """
    try:
        # Se for float, converte para inteiro primeiro para remover decimais
        if isinstance(cpf, float):
            cpf = str(int(cpf))
        else:
            cpf = str(cpf)
        
        # Remove todos os caracteres não numéricos
        cpf_digits = ''.join(filter(str.isdigit, cpf))
        
        # Preenche com zeros à esquerda se necessário
        cpf_normalized = cpf_digits.zfill(11)
        
        # Verifica se tem exatamente 11 dígitos
        if len(cpf_normalized) != 11:
            print(f"Aviso: CPF {cpf} não possui 11 dígitos após normalização.")
            return None
            
        return cpf_normalized
        
    except Exception as e:
        print(f"Erro ao normalizar CPF {cpf}: {str(e)}")
        return None

def parse_float(value):
    """
    Converte um valor string para float, tratando diferentes formatos de número
    """
    try:
        # Se já for float, retorna o valor
        if isinstance(value, float):
            return value
            
        # Remove espaços em branco e verifica se está vazio
        if not value or str(value).strip() in ['', ' ', '-']:
            return 0.0
            
        # Converte para string e substitui vírgula por ponto
        value_str = str(value).strip().replace(',', '.')
        
        # Remove caracteres não numéricos (exceto ponto e sinal negativo)
        value_str = ''.join(c for c in value_str if c.isdigit() or c in '.-')
        
        return float(value_str)
    except (ValueError, TypeError) as e:
        print(f"Aviso: Valor inválido '{value}' convertido para 0.0: {str(e)}")
        return 0.0

def parse_int(value):
    """
    Converte um valor para inteiro puro
    """
    try:
        # Se for float, converte para inteiro
        if isinstance(value, float):
            return int(value)
            
        # Se for string vazia ou traço
        if not value or str(value).strip() in ['', '-']:
            return 0
            
        # Remove espaços e vírgulas
        value_clean = str(value).strip().replace(',', '')
        
        # Converte para inteiro
        return int(float(value_clean))
        
    except (ValueError, TypeError) as e:
        print(f"Aviso: Valor inválido '{value}' convertido para 0: {str(e)}")
        return 0

def parse_date(value):
    try:
        # Tenta converter a data do formato DD-MM-AAAA para YYYY-MM-DD
        day, month, year = value.split('-')
        return datetime(int(year), int(month), int(day)).date()
    except ValueError:
        # Se falhar, tenta outros formatos como backup
        date_formats = ['%d%m%Y', '%Y%m%d', '%d/%m/%Y', '%Y-%m-%d']
        for fmt in date_formats:
            try:
                return datetime.strptime(str(value).strip(), fmt).date()
            except ValueError:
                continue
    print(f"Aviso: Data inválida '{value}'. Usando None.")
    return None
def format_currency(value):
    """Formata o valor para o padrão '1.000,00'."""
    if value is None:
        value = Decimal('0.00')
    value = Decimal(value)
    formatted_value = f'{value:,.2f}'.replace('.', 'X').replace(',', '.').replace('X', ',')
    print(f"Valor formatado: {formatted_value}")
    return formatted_value

# ===== INÍCIO DA SEÇÃO DE FICHA CLIENTE =====

def get_ficha_cliente(request, cpf):
    """
    Obtém os dados da ficha do cliente com base no CPF fornecido e renderiza a página.
    """
    print(f"Iniciando get_ficha_cliente para CPF: {cpf}")
    
    # Normaliza o CPF
    cpf_normalizado = normalize_cpf(cpf)
    if not cpf_normalizado:
        return render(request, 'siape/error.html', {'message': 'CPF inválido.'})

    # Obtém o cliente pelo CPF, ou retorna um erro 404 se não encontrado
    cliente = get_object_or_404(Cliente, cpf=cpf_normalizado)
    print(f"Cliente encontrado: {cliente.nome}")

    # Dicionário com os dados do cliente
    cliente_data = {
        'nome': cliente.nome,
        'cpf': cliente.cpf,
        'uf': cliente.uf,
        'upag': cliente.upag,
        'situacao_funcional': cliente.situacao_funcional,
        'rjur': cliente.rjur,
        'data_nascimento': cliente.data_nascimento,
        'sexo': cliente.sexo,
        'rf_situacao': cliente.rf_situacao,
        'siape_tipo_siape': cliente.siape_tipo_siape,
        'siape_qtd_matriculas': cliente.siape_qtd_matriculas,
        'siape_qtd_contratos': cliente.siape_qtd_contratos,
    }
    print("Dados do cliente coletados")

    # Obtém as informações pessoais mais recentes do cliente
    try:
        info_pessoal = cliente.informacoes_pessoais.latest('data_envio')
        info_pessoal_data = {
            'fne_celular_1': info_pessoal.fne_celular_1,
            'fne_celular_2': info_pessoal.fne_celular_2,
            'end_cidade_1': info_pessoal.end_cidade_1,
            'email_1': info_pessoal.email_1,
            'email_2': info_pessoal.email_2,
            'email_3': info_pessoal.email_3,
        }
        print("Informações pessoais coletadas")
    except InformacoesPessoais.DoesNotExist:
        info_pessoal_data = {}
        print("Nenhuma informação pessoal encontrada")

    # Filtra os débitos e margens associados ao cliente com prazo maior que zero
    debitos_margens = DebitoMargem.objects.filter(cliente=cliente, prazo__gt=0)
    print(f"Total de débitos/margens encontrados: {debitos_margens.count()}")

    debitos_margens_data = []
    for debito_margem in debitos_margens:
        # Cálculo do saldo devedor
        pmt = float(debito_margem.pmt)
        prazo = float(debito_margem.prazo)
        pr_pz = pmt * prazo
        
        if prazo < 10:
            porcentagem = 0
        elif 10 <= prazo <= 39:
            porcentagem = 0.1
        elif 40 <= prazo <= 59:
            porcentagem = 0.2
        elif 60 <= prazo <= 71:
            porcentagem = 0.25
        elif 72 <= prazo <= 83:
            porcentagem = 0.3
        elif 84 <= prazo <= 96:
            porcentagem = 0.35
        else:
            porcentagem = 0
        
        desconto = pr_pz * porcentagem
        saldo_devedor = round(pr_pz - desconto, 2)
        
        # Cálculo da margem
        margem = round(float(debito_margem.saldo_35), 2)  # Assumindo que saldo_35 representa a margem
        
        debitos_margens_data.append({
            'matricula': debito_margem.matricula,
            'banco': debito_margem.banco,
            'orgao': debito_margem.orgao,
            'pmt': debito_margem.pmt,
            'prazo': debito_margem.prazo,
            'contrato': debito_margem.contrato,
            'margem': margem,
            'saldo_devedor': saldo_devedor,
        })
    print(f"Processados {len(debitos_margens_data)} débitos/margens")

    context = {
        'cliente': cliente_data,
        'informacoes_pessoais': info_pessoal_data,
        'debitos_margens': debitos_margens_data,
    }
    
    print("Contexto da ficha do cliente montado")
    print("Renderizando página da ficha do cliente")
    return render(request, 'siape/ficha_cliente.html', context)

# ===== FIM DA SEÇÃO DE FICHA CLIENTE =====

# ===== INÍCIO DA SEÇÃO DOS POSTS =====
def post_addMeta(form_data):
    """Processa a adição de uma nova meta em RegisterMeta."""
    print("\n\n----- Iniciando post_addMeta -----\n")
    mensagem = {'texto': '', 'classe': ''}

    try:
        valor = Decimal(str(form_data.get('valor')).replace(',', '.'))
        tipo = form_data.get('tipo')
        setor = form_data.get('setor') if tipo == 'EQUIPE' else None
        loja = form_data.get('loja') if setor == 'INSS' else None
        
        meta = RegisterMeta.objects.create(
            titulo=form_data.get('titulo'),
            valor=valor,
            tipo=tipo,
            setor=setor,
            loja=loja,
            range_data_inicio=form_data.get('range_data_inicio'),
            range_data_final=form_data.get('range_data_final'),
            status=form_data.get('status') == 'True',
            descricao=form_data.get('descricao')
        )
        
        mensagem['texto'] = f'Meta "{meta.titulo}" adicionada com sucesso!'
        mensagem['classe'] = 'success'
        print(f"Meta adicionada: {meta}")

    except ValueError as e:
        mensagem['texto'] = 'Erro: Valor inválido para a meta'
        mensagem['classe'] = 'error'
        print(f"Erro de valor: {str(e)}")
    except Exception as e:
        mensagem['texto'] = f'Erro ao adicionar meta: {str(e)}'
        mensagem['classe'] = 'error'
        print(f"Erro: {str(e)}")

    return mensagem

def post_addMoney(form_data):
    """Processa a adição de um novo registro em RegisterMoney."""
    print("\n\n----- Iniciando post_addMoney -----\n")
    mensagem = {'texto': '', 'classe': ''}

    try:
        funcionario_id = form_data.get('funcionario_id')
        cpf_cliente = form_data.get('cpf_cliente')
        valor_est = form_data.get('valor_est')
        status = form_data.get('status') == 'True'  # Converte o valor do status para booleano
        data_atual = timezone.now()  # Data e hora atuais

        # Cria um novo registro em RegisterMoney
        registro = RegisterMoney.objects.create(
            funcionario_id=funcionario_id,
            cpf_cliente=cpf_cliente,
            valor_est=valor_est,
            status=status, 
            data=data_atual  # Usando a data e hora atuais
        )
        mensagem['texto'] = 'Registro adicionado com sucesso!'
        mensagem['classe'] = 'success'
        print(f"Registro adicionado: {registro}")

    except Exception as e:
        mensagem['texto'] = f'Erro ao adicionar registro: {str(e)}'
        mensagem['classe'] = 'error'
        print(f"Erro: {str(e)}")

    print(f"Mensagem final: {mensagem}\n\n")
    print("\n----- Finalizando post_addMoney -----\n")
    return mensagem

# View para criar uma nova campanha
def post_criar_campanha(form_data):
    """Processa a criação de uma nova campanha."""
    print("\n\n----- Iniciando post_criar_campanha -----\n")
    mensagem = {'texto': '', 'classe': ''}

    try:
        nome_campanha = form_data.get('nome_campanha')
        departamento = form_data.get('departamento')

        if nome_campanha and departamento:
            campanha = Campanha.objects.create(
                nome=nome_campanha,
                departamento=departamento,
                data_criacao=timezone.now(),
                status=True  # Status padrão é Ativo
            )
            mensagem['texto'] = f'Campanha "{campanha.nome}" criada com sucesso!'
            mensagem['classe'] = 'success'
            print(f"Campanha criada: {campanha.nome}")
        else:
            mensagem['texto'] = 'Por favor, preencha todos os campos obrigatórios.'
            mensagem['classe'] = 'error'
            print("Erro: Campos obrigatórios não preenchidos.")

    except Exception as e:
        mensagem['texto'] = f'Erro ao criar a campanha: {str(e)}'
        mensagem['classe'] = 'error'
        print(f"Erro ao criar a campanha: {str(e)}")

    print(f"Mensagem final: {mensagem}\n\n")
    print("\n----- Finalizando post_criar_campanha -----\n")
    return mensagem

def importar_dados_csv(request):
    print("Iniciando função importar_dados_csv")

    if 'csv_file' not in request.FILES:
        message = 'Nenhum arquivo CSV foi enviado. Por favor, selecione um arquivo CSV para importar.'
        messages.warning(request, message)
        print(f"Aviso: {message}")
        return redirect('siape:all_forms')

    print("Arquivo CSV recebido")
    csv_file = request.FILES['csv_file']
    campanha_id = request.POST.get('campanha_id', '0')  # Captura o ID da campanha
    data_hora = request.POST.get('data_hora', '2001-01-01')  # Captura a data e hora do formulário
    print(f"ID da campanha: {campanha_id}, Data e Hora: {data_hora}")

    if not csv_file.name.endswith(('.csv', '.xlsx', '.xls')):
        message = 'O arquivo deve ser um CSV ou Excel. Por favor, selecione um arquivo com extensão .csv, .xlsx ou .xls.'
        messages.warning(request, message)
        print(f"Aviso: {message}")
        return redirect('siape:all_forms')

    print("Lendo arquivo")
    if csv_file.name.endswith('.csv'):
        df = pd.read_csv(csv_file, encoding='utf-8-sig', sep=';')
        print("Arquivo CSV lido com sucesso")
    else:
        df = pd.read_excel(csv_file)
        print("Arquivo Excel lido com sucesso")

    # Verifica se a campanha existe
    try:
        campanha = Campanha.objects.get(id=campanha_id)
        print(f"Campanha encontrada: {campanha.nome}")
    except Campanha.DoesNotExist:
        message = f'Campanha com ID {campanha_id} não encontrada.'
        messages.warning(request, message)
        print(f"Aviso: {message}")
        return redirect('siape:all_forms')

    # Obter os campos do modelo Cliente
    cliente_fields = {field.name for field in Cliente._meta.get_fields()}
    informacoes_fields = {field.name for field in InformacoesPessoais._meta.get_fields()}

    # Processamento dos dados
    erros_processamento = 0
    linhas_com_erro = []
    clientes_criados = 0
    clientes_atualizados = 0

    print("Iniciando processamento de dados")
    for index, row in df.iterrows():
        print(f"\nProcessando linha {index + 1}")

        # Normaliza o CPF
        cpf_cliente = normalize_cpf(row['CPF'])
        if not cpf_cliente:
            print(f"CPF inválido na linha {index + 1}. Pulando linha.")
            continue  # Pula para a próxima linha se o CPF for inválido

        # 1. Verificar se o cliente já existe
        try:
            print(f"Verificando cliente com CPF: {cpf_cliente}")
            cliente, created = Cliente.objects.update_or_create(
                cpf=cpf_cliente,
                defaults={
                    'nome': str(row.get('NOME', 'nao existe')).strip() or "nao existe",
                    'uf': str(row.get('UF', 'nao existe')).strip() or "nao existe",
                    'upag': str(row.get('UPAG', 'nao existe')).strip() or "nao existe",
                    'situacao_funcional': str(row.get('Situacao Funcional', 'nao existe')).strip() or "nao existe",
                    'data_nascimento': parse_date(row.get('data_nascimento', '2001-01-01')),
                    'sexo': str(row.get('sexo', 'nao existe')).strip() or "nao existe",
                    'rf_situacao': str(row.get('rf_situacao', 'nao existe')).strip() or "nao existe",
                    'numero_beneficio_1': str(row.get('numero_beneficio_1', 'nao existe')).strip() or "nao existe",
                    'especie_beneficio_1': str(row.get('especie_beneficio_1', 'nao existe')).strip() or "nao existe",
                    'siape_tipo_siape': str(row.get('siape_TipoSIAPE', 'nao existe')).strip() or "nao existe",
                    'siape_qtd_matriculas': parse_int(row.get('siape_Qtd_Matriculas', '0')),
                    'siape_qtd_contratos': parse_int(row.get('siape_Qtd_Contratos', '0')),
                    'flg_nao_perturbe': str(row.get('flg_NaoPerturbe_DoNotCall', '0')).lower() in ['1', 'true', 'sim', 'yes'],
                }
            )

            cliente_id = cliente.id
            print(f"ID do cliente: {cliente_id}")

            if created:
                print(f"Cliente não encontrado. Criando cliente: {cliente.nome} (ID: {cliente_id})")
                clientes_criados += 1
            else:
                print(f"Cliente encontrado: {cliente.nome} (ID: {cliente_id}). Atualizando cliente.")
                # Atualiza os campos do cliente existente
                for field in cliente_fields:
                    if field in row:
                        setattr(cliente, field, str(row[field]).strip() or "nao existe")
                cliente.save()
                clientes_atualizados += 1

        except Exception as e:
            erros_processamento += 1
            erro_msg = f"Erro ao verificar cliente na linha {index + 1}, CPF: {cpf_cliente}: {str(e)}"
            linhas_com_erro.append(erro_msg)
            print(erro_msg)
            continue  # Continua para a próxima linha

        # 2. Verificar informações pessoais
        try:
            print("Verificando informações pessoais")
            informacoes_pessoais, created = InformacoesPessoais.objects.update_or_create(
                cliente=cliente,
                defaults={
                    'uf': row.get('UF', "nao existe") or "nao existe",
                    'fne_celular_1': row.get('fne_celular_1', "nao existe") or "nao existe",
                    'fne_celular_1_flg_whats': str(row.get('fne_celular_1_flg_whats', '0')).lower() in ['1', 'true', 'sim', 'yes'],
                    'fne_celular_2': row.get('fne_celular_2', "nao existe") or "nao existe",
                    'fne_celular_2_flg_whats': str(row.get('fne_celular_2_flg_whats', '0')).lower() in ['1', 'true', 'sim', 'yes'],
                    'end_cidade_1': row.get('end_cidade_1', "nao existe") or "nao existe",
                    'email_1': row.get('email_1', "nao existe") or "nao existe",
                    'email_2': row.get('email_2', "nao existe") or "nao existe",
                    'email_3': row.get('email_3', "nao existe") or "nao existe",
                }
            )
            print(f"Informações pessoais {'criadas' if created else 'atualizadas'} para o cliente: {cliente.nome}.")

        except Exception as e:
            erros_processamento += 1
            erro_msg = f"Erro ao adicionar informações pessoais na linha {index + 1}, CPF: {cpf_cliente}: {str(e)}"
            linhas_com_erro.append(erro_msg)
            print(erro_msg)
            continue  # Continua para a próxima linha

        # 3. Verificar débito/margem
        try:
            print("Verificando débito/margem")
            
            # Preparar os valores numéricos
            pmt_valor = parse_float(row.get('PMT', '0'))  # Se não existir, usa 0
            prazo_valor = parse_int(row.get('PRAZO', '0'))  # Se não existir, usa 0
            bruta_35_valor = parse_float(row.get('Bruta 35', '0'))  # Se não existir, usa 0
            
            print(f"Valores após parse: PMT={pmt_valor}, Prazo={prazo_valor}, Bruta 35={bruta_35_valor}")

            # Verificar se já existe um débito/margem para o cliente com o mesmo PMT e prazo
            existing_debito = DebitoMargem.objects.filter(cliente=cliente, pmt=pmt_valor, prazo=prazo_valor).first()

            if existing_debito:
                print(f"Débito/margem já existe para o cliente {cliente.nome} com PMT={pmt_valor} e prazo={prazo_valor}. Pulando criação.")
            else:
                # Criar um novo dicionário com os dados do débito/margem
                debito_data = {
                    'cliente': cliente,
                    'campanha': campanha,
                    'banco': str(row.get('BANCO', 'nao existe')).strip() or "nao existe",
                    'orgao': str(row.get('ORGAO', 'nao existe')).strip() or "nao existe",
                    'matricula': str(row.get('MATRICULA', 'nao existe')).strip() or "nao existe",
                    'upag': parse_int(row.get('UPAG', '0')),  # Se não existir, usa 0
                    'pmt': pmt_valor,
                    'prazo': prazo_valor,
                    'contrato': str(row.get('CONTRATO', 'nao existe')).strip() or "nao existe",
                    'saldo_5': parse_float(row.get('Saldo 5', '0')),  # Se não existir, usa 0
                    'beneficio_5': parse_float(row.get('Beneficio5', '0')),  # Se não existir, usa 0
                    'benef_util_5': parse_float(row.get('BenefUtil5', '0')),  # Se não existir, usa 0
                    'benef_saldo_5': parse_float(row.get('BenefSaldo5', '0')),  # Se não existir, usa 0
                    'bruta_35': bruta_35_valor,
                    'util_35': parse_float(row.get('Util.35', '0')),  # Se não existir, usa 0
                    'saldo_35': parse_float(row.get('Saldo 35', '0')),  # Se não existir, usa 0
                    'bruta_70': parse_float(row.get('Bruta 70', '0')),  # Se não existir, usa 0
                    'saldo_70': parse_float(row.get('Saldo 70', '0')),  # Se não existir, usa 0
                    'rend_bruto': parse_float(row.get('Rend.Bruto', '0')),  # Se não existir, usa 0
                    'data_envio': data_hora  # Usa diretamente o data_hora do formulário
                }

                # Criar e salvar o novo registro de débito/margem
                debito = DebitoMargem(**debito_data)
                debito.save()
                print(f"Débito/margem criado com sucesso: ID={debito.id}")

                # Se debitos_margens é um ManyToManyField, adicione o débito ao cliente
                if hasattr(cliente, 'debitos_margens'):
                    cliente.debitos_margens.add(debito)

        except Exception as e:
            erros_processamento += 1
            erro_msg = f"Erro ao adicionar débito/margem na linha {index + 1}, CPF: {cpf_cliente}: {str(e)}"
            linhas_com_erro.append(erro_msg)
            print(erro_msg)
            continue  # Continua para a próxima linha

        print(f"Linha {index + 1} processada com sucesso")

    message = f'Dados importados com sucesso! Campanha: {campanha.nome}. {clientes_criados} novos clientes criados, {clientes_atualizados} clientes atualizados e {erros_processamento} erros de processamento.'
    messages.success(request, message)
    print(f"Sucesso: {message}")

    if linhas_com_erro:
        error_message = "Erros encontrados nas seguintes linhas:\n" + "\n".join(linhas_com_erro)
        messages.warning(request, error_message)
        print(error_message)

    print("Finalizando função importar_dados_csv")
    return redirect('siape:all_forms')

# Antes de get_all_forms()
def post_deleteMoney(registro_id):
    """Processa a exclusão de um registro em RegisterMoney."""
    print("\n\n----- Iniciando post_deleteMoney -----\n")
    mensagem = {'texto': '', 'classe': ''}

    try:
        registro = RegisterMoney.objects.get(id=registro_id)
        registro.delete()
        mensagem['texto'] = 'Registro excluído com sucesso!'
        mensagem['classe'] = 'success'
        print(f"Registro excluído: {registro_id}")

    except RegisterMoney.DoesNotExist:
        mensagem['texto'] = 'Registro não encontrado.'
        mensagem['classe'] = 'error'
        print(f"Erro: Registro {registro_id} não encontrado")
    except Exception as e:
        mensagem['texto'] = f'Erro ao excluir registro: {str(e)}'
        mensagem['classe'] = 'error'
        print(f"Erro: {str(e)}")

    print(f"Mensagem final: {mensagem}\n\n")
    print("\n----- Finalizando post_deleteMoney -----\n")
    return mensagem

def post_csv_money(form_data):
    """Processa a importação de registros em RegisterMoney a partir de um arquivo CSV."""
    print("\n\n----- Iniciando post_csv_money -----\n")
    mensagem = {'texto': '', 'classe': ''}

    try:
        # Obtém o arquivo CSV do form_data
        csv_file = form_data.get('csv_file')
        if not csv_file:
            raise ValueError("Nenhum arquivo CSV fornecido.")

        # Lê o arquivo CSV
        df = pd.read_csv(csv_file, sep=';', encoding='utf-8-sig')

        for index, row in df.iterrows():
            funcionario_id = row['funcionario_id']
            cpf_cliente = row['cpf_cliente']
            valor_est = parse_float(row['valor_est'])
            data = parse_date(row['data'])

            # Cria um novo registro em RegisterMoney
            RegisterMoney.objects.create(
                funcionario_id=funcionario_id,
                cpf_cliente=cpf_cliente,
                valor_est=valor_est,
                status=True,
                data=data
            )
            print(f"Registro adicionado: Funcionario ID={funcionario_id}, CPF={cpf_cliente}, Valor={valor_est}")

        mensagem['texto'] = 'Registros importados com sucesso!'
        mensagem['classe'] = 'success'

    except Exception as e:
        mensagem['texto'] = f'Erro ao importar registros: {str(e)}'
        mensagem['classe'] = 'error'
        print(f"Erro: {str(e)}")

    return mensagem

# ===== FIM DA SEÇÃO DOS POSTS =====

# ===== INÍCIO DA SEÇÃO DE ALL FORMS =====

def get_all_forms():
    """
    Obtém todos os parâmetros de models e forms necessários para all_forms.
    """
    campanhas_queryset = Campanha.objects.all()  # Obtém todas as campanhas
    campanhas = {}  # Inicializa um dicionário para armazenar as campanhas
    debitos_por_campanha = {}  # Dicionário para armazenar a contagem de débitos por campanha
    funcionarios = Funcionario.objects.all()  # Obtém todos os funcionários
    registros = []  # Inicializa uma lista para armazenar os registros de RegisterMoney

    # Preenche o dicionário com as campanhas e conta os débitos
    for campanha in campanhas_queryset:
        campanhas[campanha.id] = {
            'id': campanha.id,  # Adiciona o ID da campanha
            'nome': campanha.nome,
            'departamento': campanha.departamento,
            'data_criacao': campanha.data_criacao,
            'status': 'Ativo' if campanha.status else 'Inativo'
        }
        
        # Contar quantos débitos estão associados a esta campanha
        debitos_count = DebitoMargem.objects.filter(campanha=campanha).count()
        debitos_por_campanha[campanha.id] = debitos_count

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

    # Modificando a obtenção dos registros de RegisterMoney
    registros = []
    for registro in RegisterMoney.objects.select_related('funcionario').all():
        # Tenta encontrar o cliente pelo CPF
        try:
            cliente = Cliente.objects.get(cpf=registro.cpf_cliente)
            nome_ou_cpf = cliente.nome
        except Cliente.DoesNotExist:
            nome_ou_cpf = registro.cpf_cliente

        registros.append({
            'id': registro.id,
            'nome': registro.funcionario.nome,
            'valor': registro.valor_est,
            'cliente': nome_ou_cpf,
            'data': registro.data
        })

    # Adicionar metas ao contexto
    metas = RegisterMeta.objects.all().order_by('-range_data_inicio')
    
    # Buscar todas as lojas do INSS
    lojas = Loja.objects.all().order_by('nome')
    
    context = {
        'campanhas': campanhas,  # Adiciona o dicionário de campanhas ao contexto
        'departamentos': departamento_list,  # Adiciona a lista de departamentos ao contexto
        'debitos_por_campanha': debitos_por_campanha,  # Adiciona a contagem de débitos por campanha
        'funcionarios': funcionarios,  # Adiciona a lista de funcionários ao contexto
        'registros': registros,        # Adiciona a lista de registros ao contexto
        'metas': metas,  # Adicionando metas ao contexto
        'lojas': lojas,  # Adicionando todas as lojas ao contexto
    }
    return context

@verificar_autenticacao
@check_access(departamento='SIAPE', nivel_minimo='ESTAGIO')
def all_forms(request):
    """
    Renderiza a página com todos os formulários do SIAPE e processa os formulários enviados.
    Requer autenticação e acesso ao departamento SIAPE (nível mínimo: ESTAGIO).
    """
    print("Iniciando função all_forms")
    
    # Inicializa a mensagem
    mensagem = {'texto': '', 'classe': ''}
    
    if request.method == 'POST':
        print("Request é POST. Processando formulário...")
        form_type = request.POST.get('form_type')
        print(f"Formulário recebido: {form_type}")
        
        if form_type == 'consulta_cliente':
            cpf_cliente = request.POST.get('cpf_cliente')
            print(f"CPF recebido para consulta: {cpf_cliente}")
            if not cpf_cliente:
                mensagem = {'texto': 'CPF não fornecido. Por favor, insira um CPF válido.', 'classe': 'warning'}
                print("Aviso: CPF não fornecido")
            else:
                cpf_cliente_limpo = normalize_cpf(cpf_cliente)
                print(f"CPF normalizado: {cpf_cliente_limpo}")
                try:
                    cliente = Cliente.objects.get(cpf=cpf_cliente_limpo)
                    print(f"Cliente encontrado: {cliente.nome}")
                    return get_ficha_cliente(request, cliente.id)
                except Cliente.DoesNotExist:
                    mensagem = {'texto': f"Cliente com CPF {cpf_cliente} não encontrado na base de dados.", 'classe': 'warning'}
                    print(f"Aviso: Cliente com CPF {cpf_cliente} não encontrado")
                except Exception as e:
                    mensagem = {'texto': f"Ocorreu um erro ao processar sua solicitação: {str(e)}", 'classe': 'error'}
                    print(f"Erro: {str(e)}")
        
        elif form_type == 'importar_csv':
            print("Iniciando importação de CSV")
            importar_dados_csv(request)

        elif form_type == 'criar_campanha':
            form_data = {
                'nome_campanha': request.POST.get('nome_campanha'),
                'departamento': request.POST.get('departamento')
            }
            mensagem = post_criar_campanha(form_data)

        elif form_type == 'adicionar_registro':
            mensagem = post_addMoney(request.POST)
        
        elif form_type == 'excluir_registro':
            registro_id = request.POST.get('registro_id')
            mensagem = post_deleteMoney(registro_id)
        
        elif form_type == 'alterar_status_campanha':
            campanha_id = request.POST.get('campanha_id')
            campanha = get_object_or_404(Campanha, id=campanha_id)
            campanha.status = not campanha.status
            campanha.save()
            mensagem = {'texto': f'Status da campanha "{campanha.nome}" alterado com sucesso!', 'classe': 'success'}
        
        elif form_type == 'adicionar_meta':
            mensagem = post_addMeta(request.POST)
        
        elif form_type == 'alterar_status_meta':
            meta_id = request.POST.get('meta_id')
            meta = get_object_or_404(RegisterMeta, id=meta_id)
            meta.status = not meta.status
            meta.save()
            mensagem = {'texto': f'Status da meta "{meta.titulo}" alterado com sucesso!', 'classe': 'success'}
        
        elif form_type == 'excluir_meta':
            try:
                meta_id = request.POST.get('meta_id')
                meta = get_object_or_404(RegisterMeta, id=meta_id)
                titulo = meta.titulo
                meta.delete()
                mensagem = {
                    'texto': f'Meta "{titulo}" excluída com sucesso!',
                    'classe': 'success'
                }
            except Exception as e:
                mensagem = {
                    'texto': f'Erro ao excluir meta: {str(e)}',
                    'classe': 'error'
                }
        
        elif form_type == 'importar_csv_money':
            print("Iniciando importação de CSV para RegisterMoney")
            mensagem = post_csv_money(request.FILES)
    
    # Obtém o contexto atualizado APÓS processar o POST
    context = get_all_forms()
    context['title'] = 'SIAPE - Todos os Formulários'
    context['mensagem'] = mensagem
    
    print("Renderizando página all_forms")
    return render(request, 'siape/all_forms.html', context)

# ===== FIM DA SEÇÃO DE ALL FORMS =====

# ===== INÍCIO DA SEÇÃO DE RANKING =====

def get_cards(periodo='mes'):
    print("\n----- Iniciando get_cards -----\n")
    
    hoje = timezone.now()
    
    # Busca a meta geral ativa
    meta_geral = RegisterMeta.objects.filter(
        tipo='GERAL',
        status=True,
        range_data_inicio__lte=hoje.date(),
        range_data_final__gte=hoje.date()
    ).first()
    
    # Busca a meta da equipe SIAPE ativa
    meta_equipe = RegisterMeta.objects.filter(
        tipo='EQUIPE',
        status=True,
        range_data_inicio__lte=hoje.date(),
        range_data_final__gte=hoje.date()
    ).first()
    
    # Define o período de análise para a meta geral
    if meta_geral:
        primeiro_dia_geral = meta_geral.range_data_inicio
        ultimo_dia_geral = datetime.combine(meta_geral.range_data_final, time(23, 59, 59))
    else:
        primeiro_dia_geral = hoje.replace(day=1)
        ultimo_dia_geral = datetime.combine((hoje.replace(day=1, month=hoje.month + 1) - timezone.timedelta(days=1)), time(23, 59, 59))
    
    # Busca os registros financeiros no período da meta geral (sem filtro de departamento)
    valores_range = RegisterMoney.objects.filter(
        data__range=[primeiro_dia_geral, ultimo_dia_geral]
    ).select_related('funcionario')  # Removido o filtro de departamento
    print(f"Valores range encontrados: {valores_range.count()}")
    
    # Calcula faturamentos para a meta geral
    faturamento_total = Decimal('0')
    for valor in valores_range:
        valor_decimal = Decimal(str(valor.valor_est))
        faturamento_total += valor_decimal
    
    # Define o período de análise para a meta SIAPE
    if meta_equipe:
        primeiro_dia_siape = meta_equipe.range_data_inicio
        ultimo_dia_siape = datetime.combine(meta_equipe.range_data_final, time(23, 59, 59))
        
        # Busca os registros financeiros dentro do intervalo da meta EQUIPE (com filtro de departamento e setor)
        valores_siape_range = RegisterMoney.objects.filter(
            data__range=[primeiro_dia_siape, ultimo_dia_siape],
            funcionario__departamento__grupo__name='SIAPE'  # Filtro adicionado para o departamento SIAPE
        ).select_related('funcionario', 'funcionario__departamento', 'funcionario__departamento__grupo')
        
        # Calcula faturamento para a meta SIAPE
        faturamento_siape = Decimal('0')
        for valor in valores_siape_range:
            valor_decimal = Decimal(str(valor.valor_est))
            faturamento_siape += valor_decimal
    else:
        faturamento_siape = Decimal('0')  # Se não houver meta_equipe, faturamento_siape é 0
    
    # Calcula percentuais
    percentual_geral = 0
    if meta_geral and meta_geral.valor is not None and meta_geral.valor > 0:
        percentual_geral = round((faturamento_total / meta_geral.valor) * 100, 2)
        
    percentual_siape = 0  
    if meta_equipe and meta_equipe.valor is not None and meta_equipe.valor > 0:
        percentual_siape = round((faturamento_siape / meta_equipe.valor) * 100, 2)
    
    context = {
        'meta_geral': {
            'valor_total': format_currency(faturamento_total),
            'percentual': percentual_geral,
            'valor_meta': format_currency(meta_geral.valor) if meta_geral else "R$ 0,00"
        },
        'meta_siape': {
            'valor_total': format_currency(faturamento_siape),
            'percentual': percentual_siape,
            'valor_meta': format_currency(meta_equipe.valor) if meta_equipe else "R$ 0,00"
        }
    }
    
    print(f"Faturamento Geral: {context['meta_geral']['valor_total']}")
    print(f"Percentual Meta Geral: {context['meta_geral']['percentual']}%")
    print(f"Faturamento SIAPE: {context['meta_siape']['valor_total']}")
    print(f"Percentual Meta SIAPE: {context['meta_siape']['percentual']}%")
    print("\n----- Finalizando get_cards -----\n")
    return context

def get_podium(periodo='mes'):
    """
    Calcula o pódio dos funcionários baseado nos valores registrados no RegisterMoney
    usando o período da meta ativa do SIAPE
    """
    print("\n----- Iniciando get_podium -----\n")
    
    hoje = timezone.now().date()
    
    # Busca meta ativa do SIAPE
    meta_siape = RegisterMeta.objects.filter(
        status=True,
        tipo='EQUIPE',
        setor='SIAPE',
        range_data_inicio__lte=hoje,
        range_data_final__gte=hoje
    ).first()
    
    # Se encontrou meta ativa, usa o range de datas dela
    if meta_siape:
        print(f"Meta SIAPE ativa encontrada: {meta_siape.titulo}")
        primeiro_dia = meta_siape.range_data_inicio
        ultimo_dia = meta_siape.range_data_final
    else:
        print("Nenhuma meta SIAPE ativa encontrada, usando mês atual")
        primeiro_dia = hoje.replace(day=1)
        ultimo_dia = (hoje.replace(day=1, month=hoje.month + 1) - timezone.timedelta(days=1))
    
    print(f"Período do pódio: {primeiro_dia} até {ultimo_dia}")
    
    # Busca todos os registros de valores no período
    valores_range = RegisterMoney.objects.filter(
        data__range=[primeiro_dia, ultimo_dia]
    )
    
    # Obtém os IDs dos funcionários com registros
    funcionarios_ids = valores_range.values_list('funcionario_id', flat=True).distinct()
    
    # Busca funcionários do departamento SIAPE
    funcionarios = Funcionario.objects.filter(
        id__in=funcionarios_ids,
        departamento__grupo__name='SIAPE'
    ).select_related('departamento')
    
    # Dicionário para armazenar valores por funcionário
    valores_por_funcionario = {}
    
    # Processa os valores
    for venda in valores_range:
        funcionario = next((f for f in funcionarios if f.id == venda.funcionario_id), None)
        if not funcionario:
            continue
            
        funcionario_id = funcionario.id
        if funcionario_id not in valores_por_funcionario:
            valores_por_funcionario[funcionario_id] = {
                'id': funcionario_id,
                'nome': funcionario.nome,
                'logo': funcionario.foto.url if funcionario.foto else '/static/img/default-store.png',
                'total_fechamentos': Decimal('0')
            }
        
        valores_por_funcionario[funcionario_id]['total_fechamentos'] += Decimal(str(venda.valor_est))

    # Converte para lista e ordena
    podium = sorted(
        valores_por_funcionario.values(),
        key=lambda x: x['total_fechamentos'],
        reverse=True
    )[:5]  # Pega os 5 primeiros

    # Adiciona posição no pódio e formata os valores
    for i, funcionario in enumerate(podium):
        funcionario['posicao'] = i + 1
        funcionario['total_fechamentos'] = f"R$ {funcionario['total_fechamentos']:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')

    print(f"Total de funcionários no pódio: {len(podium)}")
    print("\n----- Finalizando get_podium -----\n")
    
    return {
        'podium': podium,
        'periodo': {
            'inicio': primeiro_dia,
            'fim': ultimo_dia
        }
    }

def get_ranking(request):
    """
    Obtém os dados do ranking e retorna o contexto
    """
    print("\n----- Iniciando get_ranking -----\n")
    
    # Obtém dados do podium (se necessário) e os dados dos cards
    dados_podium = get_podium()
    dados_cards = get_cards()
    
    # Cria o contexto a ser retornado
    context_data = {
        'podium': dados_podium['podium'],  # Certifique-se de que dados_podium tenha a chave correta
        'meta_geral': dados_cards['meta_geral'],  # Adiciona os dados da meta geral
        'meta_siape': dados_cards['meta_siape'],  # Adiciona os dados da meta SIAPE
    }
    
    print("\n----- Finalizando get_ranking -----\n")
    return context_data

@verificar_autenticacao
@check_access(departamento='SIAPE', nivel_minimo='ESTAGIO')
def render_ranking(request):
    """
    Renderiza a página de ranking com os dados necessários.
    Requer autenticação e acesso ao departamento SIAPE (nível mínimo: ESTAGIO).
    """
    print("\n----- Iniciando render_ranking -----\n")
    
    # Verifica se o usuário está logado e obtém o funcionário associado
    funcionario_logado = None
    if request.user.is_authenticated:
        try:
            funcionario_logado = Funcionario.objects.get(usuario=request.user)
        except Funcionario.DoesNotExist:
            print("Usuário logado não tem funcionário associado")
    
    # Obtém os dados do ranking
    context = get_ranking(request)
    
    # Adiciona o funcionário logado ao contexto
    context['funcionario_logado'] = funcionario_logado
    
    print("\n----- Finalizando render_ranking -----\n")
    return render(request, 'siape/ranking.html', context)





