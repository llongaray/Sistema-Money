from django.db import models
from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.utils import timezone
from apps.funcionarios.models import *

class Cliente(models.Model):
    """
    Modelo que representa um cliente, que pode estar associado a uma ou mais matrículas de débitos.
    """
    nome = models.CharField(max_length=100, verbose_name="Nome", blank=True, null=True)  # Nome completo do cliente, permite vazio
    cpf = models.CharField(max_length=11, unique=True, validators=[RegexValidator(r'^\d{11}$')], verbose_name="CPF", blank=True, null=True)  # CPF do cliente, deve ser único, permite vazio
    uf = models.CharField(max_length=2, verbose_name="UF", blank=True, null=True)  # Unidade Federativa (estado) onde o cliente reside, permite vazio
    upag = models.CharField(max_length=50, verbose_name="UPAG", blank=True, null=True)  # Unidade pagadora associada ao cliente, permite vazio
    matricula_instituidor = models.CharField(max_length=50, blank=True, null=True)  # Matrícula do instituidor, caso aplicável, permite vazio
    situacao_funcional = models.CharField(max_length=50, verbose_name="Situação Funcional", blank=True, null=True)  # Situação funcional do cliente (ativo, aposentado, etc.), permite vazio
    rjur = models.CharField(max_length=50, blank=True, null=True)  # Representação jurídica ou setor jurídico associado ao cliente, permite vazio
    data_nascimento = models.DateField(verbose_name="Data de Nascimento", blank=True, null=True)  # Data de nascimento do cliente, permite vazio
    sexo = models.CharField(max_length=1, choices=[('M', 'Masculino'), ('F', 'Feminino')], verbose_name="Sexo", blank=True, null=True)  # Sexo do cliente, permite vazio
    rf_situacao = models.CharField(max_length=50, blank=True, null=True, verbose_name="Situação RF")  # Opcional, permite vazio
    numero_beneficio_1 = models.CharField(max_length=20, blank=True, null=True, verbose_name="Número do Benefício 1")  # Permite vazio
    especie_beneficio_1 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Espécie do Benefício 1")  # Permite vazio
    siape_tipo_siape = models.CharField(max_length=50, blank=True, null=True, verbose_name="Tipo SIAPE")  # Opcional, permite vazio
    siape_qtd_matriculas = models.PositiveIntegerField(default=0, null=True, blank=True, verbose_name="Quantidade de Matrículas SIAPE")  # Opcional, permite vazio
    siape_qtd_contratos = models.PositiveIntegerField(default=0, null=True, blank=True, verbose_name="Quantidade de Contratos SIAPE")  # Opcional, permite vazio
    flg_nao_perturbe = models.BooleanField(default=False, verbose_name="Não Perturbe")
    
    def __str__(self):
        return f"{self.nome} - {self.cpf}"

class Campanha(models.Model):
    nome = models.CharField(max_length=100, verbose_name="Nome da Campanha", blank=True, null=True)
    data_criacao = models.DateTimeField(default=timezone.now, verbose_name="Data de Criação", blank=True, null=True)
    departamento = models.CharField(max_length=100, verbose_name="Departamento", blank=True, null=True)
    status = models.BooleanField(default=True, verbose_name="Status", blank=True, null=True)  # True para Ativo, False para Inativo

    def __str__(self):
        return f"{self.nome} - {'Ativo' if self.status else 'Inativo'}"

class InformacoesPessoais(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='informacoes_pessoais')
    uf = models.CharField(max_length=2, verbose_name="UF", blank=True, null=True)
    fne_celular_1 = models.CharField(max_length=20, blank=True, null=True, verbose_name="Celular 1")
    fne_celular_1_flg_whats = models.BooleanField(default=False, verbose_name="Celular 1 tem WhatsApp", blank=True, null=True)
    fne_celular_2 = models.CharField(max_length=20, blank=True, null=True, verbose_name="Celular 2")
    fne_celular_2_flg_whats = models.BooleanField(default=False, verbose_name="Celular 2 tem WhatsApp", blank=True, null=True)
    end_cidade_1 = models.CharField(max_length=100, verbose_name="Cidade", blank=True, null=True)
    email_1 = models.EmailField(blank=True, null=True, verbose_name="Email 1")
    email_2 = models.EmailField(blank=True, null=True, verbose_name="Email 2")
    email_3 = models.EmailField(blank=True, null=True, verbose_name="Email 3")
    data_envio = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Informações de {self.cliente.nome} - {self.data_envio}"

    class Meta:
        ordering = ['-data_envio']  # Ordena do mais recente para o mais antigo

class DebitoMargem(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='debitos_margens')
    campanha = models.ForeignKey(Campanha, on_delete=models.CASCADE, related_name='debitos_margens')  # Nova chave estrangeira
    banco = models.CharField(max_length=100, verbose_name="Banco", blank=True, null=True)
    orgao = models.CharField(max_length=50, verbose_name="Órgão", blank=True, null=True)
    matricula = models.CharField(max_length=50, verbose_name="Matrícula", blank=True, null=True)
    upag = models.PositiveIntegerField(verbose_name="UPAG", blank=True, null=True)
    pmt = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], verbose_name="PMT", blank=True, null=True)
    prazo = models.PositiveIntegerField(verbose_name="Prazo", blank=True, null=True)
    contrato = models.CharField(max_length=50, verbose_name="Contrato", blank=True, null=True)
    saldo_5 = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Saldo 5", blank=True, null=True)
    beneficio_5 = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Benefício 5", blank=True, null=True)
    benef_util_5 = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Benefício Utilizado 5", blank=True, null=True)
    benef_saldo_5 = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Saldo Benefício 5", blank=True, null=True)
    bruta_35 = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Bruta 35", blank=True, null=True)
    util_35 = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Utilizado 35", blank=True, null=True)
    saldo_35 = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Saldo 35", blank=True, null=True)
    bruta_70 = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Bruta 70", blank=True, null=True)
    saldo_70 = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Saldo 70", blank=True, null=True)
    rend_bruto = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Rendimento Bruto")
    data_envio = models.DateTimeField(blank=True, null=True)  # Remover auto_now_add

    def __str__(self):
        return f"Débito/Margem de {self.cliente.nome} - {self.contrato}"

    class Meta:
        ordering = ['-data_envio']  # Ordena do mais recente para o mais antigo

class RegisterMoney(models.Model):
    funcionario = models.ForeignKey('funcionarios.Funcionario', on_delete=models.CASCADE)  # Referência correta
    cpf_cliente = models.CharField(max_length=11, blank=True, null=True)
    valor_est = models.FloatField(blank=True, null=True)
    status = models.BooleanField(default=True, blank=True, null=True)
    data = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f'{self.funcionario.nome} - {self.cpf_cliente} - {self.valor_est}'  # Atualizado para usar funcionario.nome

class RegisterMeta(models.Model):
    TIPO_CHOICES = [
        ('GERAL', 'Geral - Todas as equipes'),
        ('EQUIPE', 'Equipe - Setor específico')
    ]
    
    titulo = models.TextField(max_length=100, default="Ranking Geral", blank=True, null=True)
    valor = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    tipo = models.CharField(max_length=6, choices=TIPO_CHOICES, default='GERAL', blank=True, null=True)
    setor = models.CharField(max_length=100, null=True, blank=True)
    loja = models.CharField(max_length=100, null=True, blank=True)  # Novo campo
    range_data_inicio = models.DateField(blank=True, null=True)
    range_data_final = models.DateField(blank=True, null=True)
    status = models.BooleanField(default=False, blank=True, null=True)
    descricao = models.TextField(blank=True, null=True)

    def __str__(self):
        if self.tipo == 'GERAL':
            return f'Meta Geral: {self.valor:.2f}'
        return f'Meta {self.setor} {self.loja or ""}: {self.valor:.2f}'
