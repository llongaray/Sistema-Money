from django.urls import path
from .views import *

app_name = 'siape'

urlpatterns = [
    # Rota para a dashboard do SIAPE
    #path('dashboard-siape/', dash_siape, name='dash_siape'),

    # Rota para a consulta de cliente
    # path('consulta-cliente/', consulta_cliente, name='consulta_cliente'),


    # Rota para a ficha de cliente
    path('ficha-cliente/<int:id>/', get_ficha_cliente, name='ficha_cliente'),

    # Rota para a confirmação de pagamentos
    #path('aprovacao-valores/', aprov_valores, name='aprov_valores'),

    # Rota para o registro de valores/pagamentos
    #path('registro-valores/', registro_valores, name='registro_valores'),

    # Rota para o ranking
    path('', render_ranking, name='ranking'),
    path('all-forms/', all_forms, name='all_forms'),
]