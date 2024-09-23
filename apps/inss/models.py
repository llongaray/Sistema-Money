from django.db import models
from apps.funcionarios.models import Funcionario

# Modelo para agendamentos
class Agendamento(models.Model):
    # Opções para as lojas onde o agendamento pode ser feito
    LOJAS_CHOICES = [
        ('Porto Alegre', 'Porto Alegre'),
        ('São Leopoldo', 'São Leopoldo'),
        ('Santa Maria', 'Santa Maria'),
    ]
    
    # Nome do cliente
    nome_cliente = models.CharField(max_length=255)
    
    # CPF do cliente (no formato XXX.XXX.XXX-XX)
    cpf_cliente = models.CharField(max_length=14)
    
    # Número de celular para contato
    numero_celular = models.CharField(max_length=15, blank=True, null=True)
    
    # Confirma se o cliente tem WhatsApp
    tem_whatsapp = models.BooleanField(default=False)
    
    # Data do agendamento
    data = models.DateField()
    
    # Loja onde o agendamento será realizado
    loja_agendada = models.CharField(max_length=50, choices=LOJAS_CHOICES)
    
    # Funcionário responsável pelo agendamento
    funcionario = models.ForeignKey(Funcionario, on_delete=models.SET_NULL, null=True, blank=True, related_name='agendamentos')
    
    # Funcionário responsável pelo atendimento na loja
    funcionario_atendimento = models.ForeignKey(Funcionario, on_delete=models.SET_NULL, null=True, blank=True, related_name='atendimentos')
    
    # Confirmação do agendamento (campo booleano)
    confirmacao_agem = models.BooleanField(default=False)
    
    # Data de confirmação do agendamento
    data_confim = models.DateField(null=True, blank=True)
    
    # Comparecimento do cliente (campo booleano)
    comparecimento = models.BooleanField(default=False)
    
    # Indica se o negócio foi fechado (campo booleano)
    negocio_fechado = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.nome_cliente} - {self.loja_agendada} ({self.data})'
