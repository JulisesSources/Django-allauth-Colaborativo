from django.contrib import admin
from .models import TipoIncidencia, Incidencia


@admin.register(TipoIncidencia)
class TipoIncidenciaAdmin(admin.ModelAdmin):
    list_display = ['descripcion', 'created_at']
    search_fields = ['descripcion']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']


@admin.register(Incidencia)
class IncidenciaAdmin(admin.ModelAdmin):
    list_display = ['id_trabajador', 'id_tipo_incidencia', 'fecha_inicio', 'fecha_fin', 'duracion_dias', 'autorizada_por']
    search_fields = ['id_trabajador__nombre', 'id_trabajador__apellido_paterno', 'observaciones']
    list_filter = ['id_tipo_incidencia', 'fecha_inicio', 'autorizada_por']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by', 'duracion_dias']
    date_hierarchy = 'fecha_inicio'
    
    fieldsets = (
        ('Información de la Incidencia', {
            'fields': ('id_trabajador', 'id_tipo_incidencia', 'fecha_inicio', 'fecha_fin', 'observaciones')
        }),
        ('Autorización', {
            'fields': ('autorizada_por',)
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by', 'duracion_dias'),
            'classes': ('collapse',)
        }),
    )