from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

def check_access(level, setor=None):
    def decorator(view_func):
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            user = request.user
            
            # Nível 0: Acesso livre para todos os usuários autenticados
            if level == 0:
                return view_func(request, *args, **kwargs)

            # Verificar o grupo de acordo com o nível
            if level == 1:
                allowed_groups = ['Administrador(a)', 'Suporte', 'Supervisor(a)', 'Atendente']
            elif level == 2:
                allowed_groups = ['Administrador(a)', 'Suporte', 'Supervisor(a)']
            elif level == 3:
                allowed_groups = ['Administrador(a)', 'Suporte']
            elif level == 4:
                if user.is_superuser:
                    return view_func(request, *args, **kwargs)
                allowed_groups = ['Administrador(a)']
            else:
                return HttpResponse("Nível de acesso não definido corretamente.", status=403)

            # Verificar se o usuário pertence a um dos grupos permitidos
            if not user.groups.filter(name__in=allowed_groups).exists():
                return HttpResponse("Usuário não tem o nível de acesso necessário.", status=403)

            # Verificação de setor, exceto para 'Administrador(a)' ou 'Suporte'
            if setor and not user.groups.filter(name__in=['Administrador(a)', 'Suporte']).exists():
                if not user.groups.filter(name=setor).exists():
                    return HttpResponse(f"Você não pertence ao setor '{setor}' necessário para acessar essa página!", status=403)

            return view_func(request, *args, **kwargs)

        return _wrapped_view
    return decorator
