from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('siape/', include('apps.siape.urls')),  # Página principal
    path('inss/', include('apps.inss.urls')),
    path('rh/', include('apps.funcionarios.urls')),
    path('gerenciamento/', include('apps.gerenciamento.urls')),
    path('autenticacao/', include('apps.usuarios.urls')),
]


# Adiciona a configuração para servir arquivos de mídia durante o desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)