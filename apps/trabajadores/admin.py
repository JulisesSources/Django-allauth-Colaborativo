from django.contrib import admin
from .models import Trabajador, Puesto, TipoNombramiento


@admin.register(Puesto)
class PuestoAdmin(admin.ModelAdmin):
    list_display = ['nombre_puesto', 'nivel', 'created_at']
    search_fields = ['nombre_puesto', 'nivel']
    list_filter = ['nivel', 'created_at']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']


@admin.register(TipoNombramiento)
class TipoNombramientoAdmin(admin.ModelAdmin):
    list_display = ['descripcion', 'created_at']
    search_fields = ['descripcion']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']


@admin.register(Trabajador)
class TrabajadorAdmin(admin.ModelAdmin):
    list_display = ['numero_empleado', 'nombre_completo', 'id_puesto', 'activo', 'created_at']
    search_fields = ['numero_empleado', 'nombre', 'apellido_paterno', 'apellido_materno', 'rfc', 'curp']
    list_filter = ['activo', 'id_puesto', 'id_tipo_nombramiento', 'created_at']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    
    fieldsets = (
        ('Información Personal', {
            'fields': ('numero_empleado', 'nombre', 'apellido_paterno', 'apellido_materno')
        }),
        ('Información Fiscal', {
            'fields': ('rfc', 'curp')
        }),
        ('Información Laboral', {
            'fields': ('id_unidad', 'id_puesto', 'id_tipo_nombramiento', 'activo')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )