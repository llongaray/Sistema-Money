from django.urls import path
from . import views

app_name = 'funcionarios'

urlpatterns = [
    # Rota para a página de cadastro de funcionário
    path('all-forms/', views.render_all_forms, name='all_forms'),
    
    path('<int:id>-<slug:nome_sobrenome>/', views.render_ficha_funcionario, name='render_ficha_funcionario'),
    path('update/funcionario/<int:id>/', views.update_funcionario, name='update_funcionario'),
    path('update/user/<int:id>/', views.update_user, name='update_user'),
   
]
