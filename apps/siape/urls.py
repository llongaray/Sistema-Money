from django.urls import path
from . import views

app_name = 'siape'

urlpatterns = [
    # Rota para a dashboard do SIAPE
    #path('dashboard-siape/', views.dash_siape, name='dash_siape'),

    # Rota para a consulta de cliente
    path('consulta-cliente/', views.consulta_cliente, name='consulta_cliente'),

    #ranking
    path('update/', views.update_ranking, name='update_ranking'),

    # Rota para a ficha de cliente
    path('ficha-cliente/<int:id>/', views.ficha_cliente, name='ficha_cliente'),

    # Rota para a confirmação de pagamentos
    #path('aprovacao-valores/', views.aprov_valores, name='aprov_valores'),

    # Rota para o registro de valores/pagamentos
    #path('registro-valores/', views.registro_valores, name='registro_valores'),

    # Rota para o ranking
    path('', views.ranking, name='ranking'),
]
