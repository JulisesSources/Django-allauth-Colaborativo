# incidencias/admin.py

from django.contrib import admin
from .models import TipoIncidencia, Incidencia


@admin.register(TipoIncidencia)
class TipoIncidenciaAdmin(admin.ModelAdmin):
    list_display = ('descripcion', 'requiere_autorizacion', 'activo', 'created_at')
    list_filter = ('requiere_autorizacion', 'activo', 'created_at')
    search_fields = ('descripcion',)
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    
    fieldsets = (
        ('Información General', {
            'fields': ('descripcion', 'requiere_autorizacion', 'activo')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Incidencia)
class IncidenciaAdmin(admin.ModelAdmin):
    list_display = (
        'id_trabajador', 
        'id_tipo_incidencia', 
        'fecha_inicio', 
        'fecha_fin', 
        'duracion_dias',
        'estado', 
        'autorizada_por',
        'created_at'
    )
    list_filter = ('estado', 'id_tipo_incidencia', 'fecha_inicio', 'created_at')
    search_fields = (
        'id_trabajador__nombre', 
        'id_trabajador__apellido_paterno',
        'id_trabajador__apellido_materno',
        'id_trabajador__numero_empleado',
        'observaciones'
    )
    readonly_fields = (
        'duracion_dias',
        'created_at', 
        'updated_at', 
        'created_by', 
        'updated_by',
        'fecha_autorizacion'
    )
    date_hierarchy = 'fecha_inicio'
    
    fieldsets = (
        ('Información de la Incidencia', {
            'fields': (
                'id_trabajador',
                'id_tipo_incidencia',
                'fecha_inicio',
                'fecha_fin',
                'observaciones'
            )
        }),
        ('Estado y Autorización', {
            'fields': (
                'estado',
                'autorizada_por',
                'fecha_autorizacion',
                'comentario_autorizacion'
            )
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)