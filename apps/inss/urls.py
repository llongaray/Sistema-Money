from django.urls import path
from . import views

app_name = 'inss'

urlpatterns = [
    path('agendamento/', views.agendamento, name='agendamento'),
    path('confirmacao_agem/', views.confirmacao_agem, name='confirmacao_agem'),
    path('relise_clientes/', views.relise_clientes, name='relise_clientes'),
    path('loja_poa/', views.loja_poa, name='loja_poa'),
    path('loja_sle/', views.loja_sle, name='loja_sle'),
    path('loja_sm/', views.loja_sm, name='loja_sm'),
    path('save_cliente/', views.save_cliente, name='save_cliente'),
]
