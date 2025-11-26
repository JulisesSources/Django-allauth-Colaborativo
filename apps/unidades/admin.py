from django.contrib import admin
from .models import UnidadAdministrativa


@admin.register(UnidadAdministrativa)
class UnidadAdministrativaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'id_unidad_padre', 'created_at']
    search_fields = ['nombre', 'descripcion']
    list_filter = ['id_unidad_padre', 'created_at']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    
    fieldsets = (
        ('Información de la Unidad', {
            'fields': ('nombre', 'descripcion', 'id_unidad_padre')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )