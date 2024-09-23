from django.urls import path
from . import views

app_name = 'gerenciamento'

urlpatterns = [
    # Rota para a dashboard geral
    #path('dashboard/', views.dash_gen, name='dash_gen'),

    # Rota para o gerenciador de funcionários
    path('funcionarios/', views.gen_funcionarios, name='gen_funcionarios'),
    path('inss/', views.gen_inss, name='gen_inss'),

    # Rota para o gerenciador de ranking
    #path('ranking/', views.gen_ranking, name='gen_ranking'),
]
