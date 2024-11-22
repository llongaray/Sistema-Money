from django.contrib import admin
from django.utils.html import format_html
from .models import Agendamento, LogAlteracao

@admin.register(Agendamento)
class AgendamentoAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'nome_cliente', 'cpf_cliente', 'dia_agendado', 
        'loja_agendada', 'atendente_agendou', 'vendedor_loja', 
        'status_tac', 'tac', 'subsidio', 'tabulacao_atendente', 
        'tabulacao_vendedor'
    )
    list_filter = (
        'dia_agendado', 'loja_agendada', 'tabulacao_atendente', 
        'atendente_agendou', 'status_tac', 'subsidio'
    )
    search_fields = ('nome_cliente', 'cpf_cliente', 'numero_cliente')
    date_hierarchy = 'dia_agendado'

    fieldsets = (
        ('Informações do Cliente', {
            'fields': ('nome_cliente', 'cpf_cliente', 'numero_cliente', 'confirmacao_whatsapp')
        }),
        ('Informações do Agendamento', {
            'fields': ('dia_agendado', 'loja_agendada', 'atendente_agendou', 'tabulacao_atendente')
        }),
        ('Informações de Vendas', {
            'fields': ('vendedor_loja', 'tabulacao_vendedor', 'observacao_vendedor', 'tac', 'subsidio')
        }),
        ('Status do TAC', {
            'fields': ('status_tac', 'data_pagamento_tac')
        }),
        ('Logs de Alteração', {
            'fields': ('logs_alteracao',),
        }),
    )

    readonly_fields = ('logs_alteracao',)

    def logs_alteracao(self, obj):
        logs = LogAlteracao.objects.filter(agendamento_id=str(obj.id)).order_by('-data_hora')
        if not logs:
            return "Nenhum log encontrado."
        
        log_list = [f"<li>{log.data_hora.strftime('%d/%m/%Y %H:%M:%S')} - {log.mensagem}</li>" for log in logs]
        return format_html("<ul>{}</ul>", "".join(log_list))

    logs_alteracao.short_description = "Logs de Alteração"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('loja_agendada', 'atendente_agendou', 'vendedor_loja')

    def has_delete_permission(self, request, obj=None):
        return True  # Permite a exclusão de agendamentos

    def save_model(self, request, obj, form, change):
        # Limpa caracteres especiais do CPF
        if obj.cpf_cliente:
            obj.cpf_cliente = ''.join(filter(str.isdigit, obj.cpf_cliente))
        
        # Limpa caracteres especiais do número de telefone e limita a 15 dígitos
        if obj.numero_cliente:
            obj.numero_cliente = ''.join(filter(str.isdigit, obj.numero_cliente))[:15]
        
        super().save_model(request, obj, form, change)

@admin.register(LogAlteracao)
class LogAlteracaoAdmin(admin.ModelAdmin):
    list_display = ('agendamento_id', 'status', 'data_hora', 'funcionario')
    list_filter = ('status', 'data_hora')
    search_fields = ('mensagem', 'agendamento_id')
    readonly_fields = ('mensagem', 'status', 'data_hora', 'agendamento_id', 'funcionario')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
