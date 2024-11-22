from django.urls import path
from .views import *

app_name = 'geral'

urlpatterns = [
    path('', render_ranking, name='ranking'),
    path('forms/', all_forms, name='all_forms'),
]

