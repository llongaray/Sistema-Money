from django.contrib import admin
from .models import Empresa, Loja, Horario, Departamento, Cargo, Funcionario

# Classe para customizar a exibição da Empresa no admin
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cnpj', 'endereco')  # Campos que serão exibidos na lista de empresas
    search_fields = ('nome', 'cnpj')  # Campos pelos quais será possível buscar empresas
    list_filter = ('nome',)  # Filtro pelo nome

# Classe para customizar a exibição da Loja no admin
class LojaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'empresa')  # Exibir nome da loja e a empresa associada
    search_fields = ('nome', 'empresa__nome')  # Permite buscar pelo nome da loja e da empresa
    list_filter = ('empresa',)  # Filtro pela empresa

# Classe para customizar a exibição de Horário no admin
class HorarioAdmin(admin.ModelAdmin):
    list_display = ('nome', 'horario_entrada', 'horario_saida')  # Exibir nome e horários de entrada e saída
    search_fields = ('nome',)  # Busca pelo nome do horário
    list_filter = ('nome',)  # Filtro pelo nome

# Classe para customizar a exibição de Departamento no admin
class DepartamentoAdmin(admin.ModelAdmin):
    list_display = ('get_nome',)
    search_fields = ('grupo__name',)

    def get_nome(self, obj):
        return obj.grupo.name.replace('Departamento - ', '')
    get_nome.short_description = 'Nome'

# Classe para customizar a exibição de Cargo no admin
class CargoAdmin(admin.ModelAdmin):
    list_display = ('get_nome', 'nivel')
    search_fields = ('grupo__name', 'nivel')

    def get_nome(self, obj):
        return obj.grupo.name.replace('Cargo - ', '')
    get_nome.short_description = 'Nome'

# Classe para customizar a exibição de Funcionário no admin
class FuncionarioAdmin(admin.ModelAdmin):
    list_display = ('nome', 'sobrenome', 'cpf', 'empresa', 'loja', 'cargo', 'status')  # Exibir principais campos
    search_fields = ('nome', 'sobrenome', 'cpf', 'empresa__nome', 'loja__nome')  # Permite busca por nome, CPF, empresa e loja
    list_filter = ('status', 'empresa', 'loja', 'cargo')  # Filtros por status, empresa, loja e cargo
    fieldsets = (
        ('Informações Pessoais', {
            'fields': ('nome', 'sobrenome', 'cpf', 'data_de_nascimento', 'foto')
        }),
        ('Contato', {
            'fields': ('cep', 'endereco', 'bairro', 'cidade', 'estado', 'celular', 'celular_whatsapp')
        }),
        ('Empresa e Cargo', {
            'fields': ('empresa', 'loja', 'horario', 'departamento', 'cargo', 'superior_direto')
        }),
        ('Documentos', {
            'fields': ('identidade', 'carteira_de_trabalho', 'comprovante_de_escolaridade', 'pdf_contrato', 'certidao_de_nascimento')
        }),
        ('Outros', {
            'fields': ('status', 'data_de_admissao')
        }),
    )

# Registrando os modelos no admin com suas classes customizadas
admin.site.register(Empresa, EmpresaAdmin)
admin.site.register(Loja, LojaAdmin)
admin.site.register(Horario, HorarioAdmin)
admin.site.register(Departamento, DepartamentoAdmin)
admin.site.register(Cargo, CargoAdmin)
admin.site.register(Funcionario, FuncionarioAdmin)
