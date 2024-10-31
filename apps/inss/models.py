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
