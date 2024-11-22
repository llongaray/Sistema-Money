from django.contrib import admin
from .models import Equipe, MembroEquipe, ProvaGincana, ParticipacaoProva, Pontuacao

@admin.register(Equipe)
class EquipeAdmin(admin.ModelAdmin):
    list_display = ('nome', 'lider', 'status', 'data_criacao')
    search_fields = ('nome', 'lider__nome')
    list_filter = ('status',)

@admin.register(MembroEquipe)
class MembroEquipeAdmin(admin.ModelAdmin):
    list_display = ('funcionario', 'equipe', 'data_entrada', 'ativo')
    search_fields = ('funcionario__nome', 'equipe__nome')
    list_filter = ('ativo', 'equipe')

@admin.register(ProvaGincana)
class ProvaGincanaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'pontos_possiveis', 'data_inicio', 'status')
    search_fields = ('nome',)
    list_filter = ('status',)

@admin.register(ParticipacaoProva)
class ParticipacaoProvaAdmin(admin.ModelAdmin):
    list_display = ('funcionario', 'prova', 'pontos_obtidos', 'data_participacao')
    search_fields = ('funcionario__nome', 'prova__nome')
    list_filter = ('prova',)

@admin.register(Pontuacao)
class PontuacaoAdmin(admin.ModelAdmin):
    list_display = ('funcionario', 'equipe', 'pontos', 'data_registro')
    search_fields = ('funcionario__nome', 'equipe__nome')
    list_filter = ('equipe',)
