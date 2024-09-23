from django.contrib import admin
from .models import Funcionario

@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    list_display = (
        'nome', 'sobrenome', 'cpf', 'empresa', 
        'departamento', 'cargo', 'data_de_admissao', 'status'
    )
    list_filter = ('empresa', 'departamento', 'status', 'data_de_admissao')
    search_fields = ('nome', 'sobrenome', 'cpf', 'cnpj', 'rg', 'matricula', 'empresa')
    ordering = ('nome', 'sobrenome')
    fieldsets = (
        ('Informações Pessoais', {
            'fields': (
                'usuario', 'nome', 'sobrenome', 'cpf', 'rg', 'pis', 
                'data_de_nascimento', 'cnh', 'categoria_cnh', 'genero',
                'estado_civil', 'nacionalidade', 'naturalidade',
                'nome_do_pai', 'nome_da_mae'
            )
        }),
        ('Endereço e Contato', {
            'fields': (
                'cep', 'endereco', 'bairro', 'cidade', 
                'estado', 'celular', 'celular_sms', 
                'celular_ligacao', 'celular_whatsapp'
            )
        }),
        ('Informações de Trabalho', {
            'fields': (
                'empresa', 'departamento', 'cargo', 
                'data_de_admissao', 'horario', 'status', 
                'superior_direto', 'numero_da_folha', 'matricula', 'ctps'
            )
        }),
        ('Documentos', {
            'fields': (
                'foto', 'identidade', 'carteira_de_trabalho',
                'comprovante_de_escolaridade', 'pdf_contrato', 
                'certidao_de_nascimento'
            )
        }),
    )
    readonly_fields = ('usuario',)
