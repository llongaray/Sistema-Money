from django.db import models
from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.utils import timezone
from apps.funcionarios.models import *

class Cliente(models.Model):
    """
    Modelo que representa um cliente, que pode estar associado a uma ou mais matrículas de débitos.
    """
    nome = models.CharField(max_length=100, verbose_name="Nome")  # Nome completo do cliente
    cpf = models.CharField(max_length=11, unique=True, validators=[RegexValidator(r'^\d{11}$')], verbose_name="CPF")  # CPF do cliente, deve ser único
    uf = models.CharField(max_length=2, verbose_name="UF")  # Unidade Federativa (estado) onde o cliente reside
    upag = models.CharField(max_length=50, verbose_name="UPAG")  # Unidade pagadora associada ao cliente
    matricula_instituidor = models.CharField(max_length=50, blank=True, null=True)  # Matrícula do instituidor, caso aplicável
    situacao_funcional = models.CharField(max_length=50, verbose_name="Situação Funcional")  # Situação funcional do cliente (ativo, aposentado, etc.)
    rjur = models.CharField(max_length=50)  # Representação jurídica ou setor jurídico associado ao cliente
    data_nascimento = models.DateField(verbose_name="Data de Nascimento")  # Data de nascimento do cliente
    sexo = models.CharField(max_length=1, choices=[('M', 'Masculino'), ('F', 'Feminino')], verbose_name="Sexo")  # Sexo do cliente
    rf_situacao = models.CharField(max_length=50, blank=True, null=True, verbose_name="Situação RF")  # Opcional
    numero_beneficio_1 = models.CharField(max_length=20, blank=True, null=True, verbose_name="Número do Benefício 1")
    especie_beneficio_1 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Espécie do Benefício 1")
    siape_tipo_siape = models.CharField(max_length=50, blank=True, null=True, verbose_name="Tipo SIAPE")  # Opcional
    siape_qtd_matriculas = models.PositiveIntegerField(default=0, null=True, blank=True, verbose_name="Quantidade de Matrículas SIAPE")  # Opcional
    siape_qtd_contratos = models.PositiveIntegerField(default=0, null=True, blank=True, verbose_name="Quantidade de Contratos SIAPE")  # Opcional
    flg_nao_perturbe = models.BooleanField(default=False, verbose_name="Não Perturbe")
    
    def __str__(self):
        return f"{self.nome} - {self.cpf}"

class Campanha(models.Model):
    nome = models.CharField(max_length=100, verbose_name="Nome da Campanha")
    data_criacao = models.DateTimeField(default=timezone.now, verbose_name="Data de Criação")
    departamento = models.CharField(max_length=100, verbose_name="Departamento")
    status = models.BooleanField(default=True, verbose_name="Status")  # True para Ativo, False para Inativo

    def __str__(self):
        return f"{self.nome} - {'Ativo' if self.status else 'Inativo'}"

class InformacoesPessoais(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='informacoes_pessoais')
    uf = models.CharField(max_length=2, verbose_name="UF")
    fne_celular_1 = models.CharField(max_length=20, blank=True, null=True, verbose_name="Celular 1")
    fne_celular_1_flg_whats = models.BooleanField(default=False, verbose_name="Celular 1 tem WhatsApp")
    fne_celular_2 = models.CharField(max_length=20, blank=True, null=True, verbose_name="Celular 2")
    fne_celular_2_flg_whats = models.BooleanField(default=False, verbose_name="Celular 2 tem WhatsApp")
    end_cidade_1 = models.CharField(max_length=100, verbose_name="Cidade")
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
    banco = models.CharField(max_length=100, verbose_name="Banco")
    orgao = models.CharField(max_length=50, verbose_name="Órgão")
    matricula = models.CharField(max_length=50, verbose_name="Matrícula")
    upag = models.PositiveIntegerField(verbose_name="UPAG")
    pmt = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], verbose_name="PMT")
    prazo = models.PositiveIntegerField(verbose_name="Prazo")
    contrato = models.CharField(max_length=50, verbose_name="Contrato")
    saldo_5 = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Saldo 5")
    beneficio_5 = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Benefício 5")
    benef_util_5 = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Benefício Utilizado 5")
    benef_saldo_5 = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Saldo Benefício 5")
    bruta_35 = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Bruta 35")
    util_35 = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Utilizado 35")
    saldo_35 = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Saldo 35")
    bruta_70 = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Bruta 70")
    saldo_70 = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Saldo 70")
    rend_bruto = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Rendimento Bruto")
    data_envio = models.DateTimeField(blank=True, null=True)  # Remover auto_now_add

    def __str__(self):
        return f"Débito/Margem de {self.cliente.nome} - {self.contrato}"

    class Meta:
        ordering = ['-data_envio']  # Ordena do mais recente para o mais antigo

class RegisterMoney(models.Model):
    funcionario = models.ForeignKey('funcionarios.Funcionario', on_delete=models.CASCADE)  # Referência correta
    cpf_cliente = models.CharField(max_length=11, blank=True, null=True)
    valor_est = models.FloatField()
    status = models.BooleanField(default=True)
    data = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f'{self.funcionario.nome} - {self.cpf_cliente} - {self.valor_est}'  # Atualizado para usar funcionario.nome

class RegisterMeta(models.Model):
    TIPO_CHOICES = [
        ('GERAL', 'Geral - Todas as equipes'),
        ('EQUIPE', 'Equipe - Setor específico')
    ]
    
    titulo = models.TextField(max_length=100, default="Ranking Geral")
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    tipo = models.CharField(max_length=6, choices=TIPO_CHOICES, default='GERAL')
    setor = models.CharField(max_length=100, null=True, blank=True)
<<<<<<< HEAD
    loja = models.CharField(max_length=100, null=True, blank=True)  # Novo campo
=======
>>>>>>> 8c9bdec505c96e6d36a28aa15689b2584d325ac5
    range_data_inicio = models.DateField()
    range_data_final = models.DateField()
    status = models.BooleanField(default=False)
    descricao = models.TextField(blank=True, null=True)

    def __str__(self):
        if self.tipo == 'GERAL':
            return f'Meta Geral: {self.valor:.2f}'
<<<<<<< HEAD
        return f'Meta {self.setor} {self.loja or ""}: {self.valor:.2f}'
=======
        return f'Meta {self.setor}: {self.valor:.2f}'
>>>>>>> 8c9bdec505c96e6d36a28aa15689b2584d325ac5
