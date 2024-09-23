from django.db import models
from decimal import Decimal

class Cliente(models.Model):
    """
    Modelo que representa um cliente, que pode estar associado a uma ou mais matrículas de débitos.
    """
    nome = models.CharField(max_length=100)  # Nome completo do cliente
    cpf = models.CharField(max_length=11, unique=True)  # CPF do cliente, deve ser único
    uf = models.CharField(max_length=2)  # Unidade Federativa (estado) onde o cliente reside
    upag = models.CharField(max_length=50)  # Unidade pagadora associada ao cliente
    matricula_instituidor = models.CharField(max_length=50, blank=True, null=True)  # Matrícula do instituidor, caso aplicável
    situacao_funcional = models.CharField(max_length=50)  # Situação funcional do cliente (ativo, aposentado, etc.)
    rjur = models.CharField(max_length=50)  # Representação jurídica ou setor jurídico associado ao cliente
    
    def __str__(self):
        # Retorna o nome do cliente como representação em string do objeto
        return self.nome


class MatriculaDebitos(models.Model):
    """
    Modelo que representa as informações de débitos associados a uma matrícula de um cliente.
    """
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='matriculas')
    # Relacionamento com o modelo Cliente, cada matrícula está associada a um cliente
    matricula = models.CharField(max_length=50, null=True, blank=True)  # Número da matrícula associada ao débito
    rubrica = models.CharField(max_length=50, null=True, blank=True)  # Rubrica relacionada ao débito
    banco = models.CharField(max_length=100, null=True, blank=True)  # Nome do banco associado ao débito
    orgao = models.CharField(max_length=100, null=True, blank=True)  # Órgão associado ao débito
    pmt = models.FloatField(null=True, blank=True)  # Valor do pagamento
    prazo = models.CharField(max_length=50, null=True, blank=True)  # Prazo associado ao contrato ou débito
    tipo_contrato = models.CharField(max_length=50, null=True, blank=True)  # Tipo de contrato (ex.: consignado, pessoal)
    contrato = models.CharField(max_length=50, null=True, blank=True)  # Número do contrato associado ao débito
    exc_soma = models.FloatField(null=True, blank=True)  # Valor de exclusão de soma, se aplicável
    margem = models.FloatField(null=True, blank=True)  # Margem disponível associada ao débito
    base_calc = models.FloatField(null=True, blank=True)  # Base de cálculo para o débito
    bruta_5 = models.FloatField(null=True, blank=True)  # Valor bruto da margem de 5%
    utilz_5 = models.FloatField(null=True, blank=True)  # Valor utilizado da margem de 5%
    saldo_5 = models.FloatField(null=True, blank=True)  # Saldo disponível na margem de 5%
    beneficio_bruta_5 = models.FloatField(null=True, blank=True)  # Valor bruto do benefício na margem de 5%
    beneficio_utilizado_5 = models.FloatField(null=True, blank=True)  # Valor utilizado do benefício na margem de 5%
    beneficio_saldo_5 = models.FloatField(null=True, blank=True)  # Saldo disponível do benefício na margem de 5%
    bruta_35 = models.FloatField(null=True, blank=True)  # Valor bruto da margem de 35%
    utilz_35 = models.FloatField(null=True, blank=True)  # Valor utilizado da margem de 35%
    saldo_35 = models.FloatField(null=True, blank=True)  # Saldo disponível na margem de 35%
    bruta_70 = models.FloatField(null=True, blank=True)  # Valor bruto da margem de 70%
    utilz_70 = models.FloatField(null=True, blank=True)  # Valor utilizado da margem de 70%
    saldo_70 = models.FloatField(null=True, blank=True)  # Saldo disponível na margem de 70%
    creditos = models.FloatField(null=True, blank=True)  # Valor total de créditos associados ao débito
    debitos = models.FloatField(null=True, blank=True)  # Valor total de débitos associados à matrícula
    liquido = models.FloatField(null=True, blank=True)  # Valor líquido após créditos e débitos
    arq_upag = models.CharField(max_length=50, null=True, blank=True)  # Arquivo da unidade pagadora relacionado ao débito
    exc_qtd = models.IntegerField(null=True, blank=True)  # Quantidade de exclusões aplicadas ao débito
    
    def __str__(self):
        # Retorna uma representação em string que inclui o cliente, a matrícula e a rubrica
        return f"{self.cliente} - {self.matricula} - {self.rubrica}"

class RegisterMoney(models.Model):
    funcionario_id = models.PositiveIntegerField()  # Substitua por ForeignKey se tiver o modelo de Funcionario
    cpf_cliente = models.CharField(max_length=11, blank=True, null=True)
    valor_est = models.FloatField()
    status = models.BooleanField(default=False)
    data = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f'{self.funcionario_id} - {self.cpf_cliente} - {self.valor_est}'

class RegisterMeta(models.Model):
    titulo = models.TextField(max_length=100, default="Ranking Geral")
    valor = models.DecimalField(max_digits=10, decimal_places=2)  # Float com duas casas decimais (R$ {valor:.2f})
    setor = models.CharField(max_length=100)  # Não aceita espaços, apenas uma palavra
    range_data_inicio = models.DateField()  # Armazena o primeiro dia/data que a meta está valendo
    range_data_final = models.DateField()  # Armazena o dia/data final que a meta está valendo
    status = models.BooleanField(default=False)
    descricao = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'{self.valor:.2f} - {self.setor}'