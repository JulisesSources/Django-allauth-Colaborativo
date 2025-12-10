# accounts/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import PerfilUsuario


class PerfilUsuarioInline(admin.StackedInline):
    model = PerfilUsuario
    can_delete = False
    verbose_name = 'Perfil de Usuario'
    verbose_name_plural = 'Perfil de Usuario'
    fk_name = 'user'


class UserAdmin(BaseUserAdmin):
    inlines = (PerfilUsuarioInline,)
    list_display = ('username', 'email', 'get_rol', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'perfil__rol')
    
    def get_rol(self, obj):
        return obj.perfil.get_rol_display() if hasattr(obj, 'perfil') else 'Sin perfil'
    get_rol.short_description = 'Rol'


# Re-registrar UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('user', 'rol', 'id_trabajador', 'created_at')
    list_filter = ('rol', 'created_at')
    search_fields = ('user__username', 'user__email')
    raw_id_fields = ('id_trabajador',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Información del Usuario', {
            'fields': ('user', 'rol')
        }),
        ('Relación con Trabajador', {
            'fields': ('id_trabajador',)
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )