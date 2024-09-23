from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin, GroupAdmin as BaseGroupAdmin
from django.utils.translation import gettext_lazy as _

# Personalize o admin de User como antes
class UserAdmin(BaseUserAdmin):
    list_display = ('id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'is_superuser', 'groups')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'first_name', 'last_name'),
        }),
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('id', 'username')
    filter_horizontal = ('groups', 'user_permissions')

# Personalize o admin de Group
class CustomGroupAdmin(BaseGroupAdmin):
    list_display = ('id', 'name')  # Mostra o ID e o nome do grupo na lista
    search_fields = ('name',)
    ordering = ('id', 'name')

# Primeiro, desregistre o modelo Group existente
admin.site.unregister(Group)

# Em seguida, registre-o novamente com a customização
admin.site.register(Group, CustomGroupAdmin)

# Não se esqueça de também registrar o User com sua personalização
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
