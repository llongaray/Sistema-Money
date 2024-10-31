from django.urls import path
from .views import *

app_name = 'funcionarios'

urlpatterns = [
    # Rota para a página de cadastro de funcionário
    path('all-forms/', render_all_forms, name='all_forms'),
    
    path('<int:id>-<slug:nome_sobrenome>/', render_ficha_funcionario, name='render_ficha_funcionario'),
    path('update/funcionario/<int:id>/', update_funcionario, name='update_funcionario'),
    path('update/user/<int:id>/', update_user, name='update_user'),
   
    path('api/lojas/<int:empresa_id>/', get_lojas_by_empresa, name='get_lojas_by_empresa'),
]
