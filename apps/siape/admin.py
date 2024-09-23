from django.contrib import admin
from .models import Cliente, MatriculaDebitos, RegisterMoney, RegisterMeta

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cpf', 'uf', 'upag', 'situacao_funcional', 'rjur')
    search_fields = ('nome', 'cpf', 'upag', 'situacao_funcional', 'rjur')
    list_filter = ('uf', 'situacao_funcional')
    ordering = ('nome',)

@admin.register(MatriculaDebitos)
class MatriculaDebitosAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'matricula', 'rubrica', 'orgao', 'tipo_contrato', 'pmt', 'liquido')
    search_fields = ('cliente__nome', 'matricula', 'rubrica', 'orgao', 'tipo_contrato')
    list_filter = ('orgao', 'tipo_contrato')
    ordering = ('cliente', 'matricula')

@admin.register(RegisterMoney)
class RegisterMoneyAdmin(admin.ModelAdmin):
    list_display = ('funcionario_id', 'cpf_cliente', 'valor_est', 'status', 'data')
    search_fields = ('funcionario_id', 'cpf_cliente')
    list_filter = ('status', 'data')
    ordering = ('-data', 'funcionario_id')

@admin.register(RegisterMeta)
class RegisterMetaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'valor', 'setor', 'range_data_inicio', 'range_data_final', 'status')
    search_fields = ('titulo', 'setor')
    list_filter = ('setor', 'status', 'range_data_inicio', 'range_data_final')
    ordering = ('-range_data_inicio', 'setor')
