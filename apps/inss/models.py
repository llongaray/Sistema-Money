from django.db import models
from apps.funcionarios.models import Funcionario, Loja, Empresa
from apps.siape.models import Cliente

# Modelo para agendamentos
class Agendamento(models.Model):
    # Informações de Cliente
    nome_cliente = models.CharField(max_length=255)
    cpf_cliente = models.CharField(max_length=14)  # CPF no formato XXX.XXX.XXX-XX
    numero_cliente = models.CharField(max_length=15, blank=True, null=True)  # Número de celular
    confirmacao_whatsapp = models.BooleanField(default=True)  # Confirmação de WhatsApp

    # Informações de Agendamento
    dia_agendado = models.DateTimeField()  # Data do agendamento
    loja_agendada = models.ForeignKey(Loja, on_delete=models.SET_NULL, null=True, blank=True)  # Loja agendada
    atendente_agendou = models.ForeignKey(
        Funcionario, on_delete=models.SET_NULL, null=True, blank=True, related_name='agendamentos'
    )  # Atendente que agendou
    tabulacao_atendente = models.TextField(max_length=200, help_text="Até 8 palavras", blank=True, null=True, default="AGENDADO")  # Tabulação atendente

    # Informações de Vendas
    vendedor_loja = models.ForeignKey(
        Funcionario, on_delete=models.SET_NULL, null=True, blank=True, related_name='vendas'
    )  # Vendedor na loja
    tabulacao_vendedor = models.TextField(max_length=200, help_text="Até 8 palavras", blank=True, null=True)  # Tabulação vendedor
    observacao_vendedor = models.TextField(blank=True, null=True)  # Observação vendedor

    # Novo campo para observação do atendente
    observacao_atendente = models.TextField(blank=True, null=True)  # Observação do atendente

    # Campos para FECHOU NEGOCIO
    tipo_negociacao = models.CharField(max_length=100, blank=True, null=True)
    banco = models.CharField(max_length=100, blank=True, null=True)
    subsidio = models.CharField(max_length=20, blank=True, null=True, 
                              choices=[('VIDEO', 'VIDEO'), ('SELFIE', 'SELFIE')])
    tac = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    acao = models.CharField(max_length=20, blank=True, null=True,
                          choices=[('COM AÇÃO', 'COM AÇÃO'), ('SEM AÇÃO', 'SEM AÇÃO')])
    associacao = models.CharField(max_length=20, blank=True, null=True,
                                choices=[('COM ASSOCIAÇÃO', 'COM ASSOCIAÇÃO'), 
                                       ('SEM ASSOCIAÇÃO', 'SEM ASSOCIAÇÃO')])
    aumento = models.CharField(max_length=20, blank=True, null=True,
                             choices=[('COM AUMENTO', 'COM AUMENTO'), 
                                    ('SEM AUMENTO', 'SEM AUMENTO')])

    # Campo para status do TAC
    STATUS_TAC_CHOICES = [
        ('PAGO', 'PAGO'),
        ('NAO_PAGO', 'NÃO PAGO'),
        ('EM_ESPERA', 'EM ESPERA')
    ]
    status_tac = models.CharField(
        max_length=20,
        choices=STATUS_TAC_CHOICES,
        default='EM_ESPERA',
        blank=True,
        null=True
    )

    # Registro de quando o TAC foi pago
    data_pagamento_tac = models.DateTimeField(null=True, blank=True)

    # Novos campos
    data_confirmacao_loja = models.DateTimeField(null=True, blank=True)  # Data de confirmação da loja
    data_add_tac = models.DateTimeField(null=True, blank=True)  # Data de adição do TAC
    data_tac_paga = models.DateTimeField(null=True, blank=True)  # Data em que o TAC foi pago

    def __str__(self):
        return f'{self.nome_cliente} - {self.loja_agendada} ({self.dia_agendado})'

# Modelo para armazenar logs de alterações
class LogAlteracao(models.Model):
    mensagem = models.TextField()
    status = models.BooleanField(default=False)
    data_hora = models.DateTimeField(auto_now_add=True)
    agendamento_id = models.CharField(max_length=50, help_text="ID do agendamento relacionado")
    funcionario = models.ForeignKey(Funcionario, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f'Log {self.id} - Agendamento {self.agendamento_id} - Status: {self.status}'

    class Meta:
        verbose_name = "Log de Alteração"
        verbose_name_plural = "Logs de Alteração"
