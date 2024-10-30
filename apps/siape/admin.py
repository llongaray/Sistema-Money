from django.contrib import admin
from .models import *

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cpf', 'uf', 'upag', 'situacao_funcional', 'sexo', 'siape_tipo_siape')
    search_fields = ('nome', 'cpf', 'upag', 'situacao_funcional', 'numero_beneficio_1')
    list_filter = ('uf', 'situacao_funcional', 'sexo', 'siape_tipo_siape')
    ordering = ('nome',)

@admin.register(InformacoesPessoais)
class InformacoesPessoaisAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'uf', 'end_cidade_1', 'fne_celular_1', 'fne_celular_1_flg_whats', 'data_envio')
    search_fields = ('cliente__nome', 'cliente__cpf', 'end_cidade_1', 'fne_celular_1', 'email_1')
    list_filter = ('uf', 'fne_celular_1_flg_whats', 'fne_celular_2_flg_whats')
    ordering = ('-data_envio',)

@admin.register(DebitoMargem)
class DebitoMargemAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'campanha', 'banco', 'orgao', 'matricula', 'pmt', 'prazo', 'contrato')
    search_fields = ('cliente__nome', 'cliente__cpf', 'banco', 'orgao', 'matricula', 'contrato', 'campanha__nome')
    list_filter = ('banco', 'orgao', 'campanha')
    ordering = ('-data_envio', 'cliente')

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

@admin.register(Campanha)
class CampanhaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'data_criacao', 'departamento', 'status')
    search_fields = ('nome', 'departamento')
    list_filter = ('status',)
    ordering = ('-data_criacao',)
