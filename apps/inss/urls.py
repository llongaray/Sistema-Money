from django.urls import path
from .views import *

app_name = 'inss'

urlpatterns = [
    path('agendamentos/', render_all_forms, name='all_forms'),
    path('ranking/', render_ranking, name='ranking'),  # Nova URL para o ranking
]
