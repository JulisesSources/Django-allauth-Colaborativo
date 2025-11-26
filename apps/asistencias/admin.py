from django.contrib import admin
from .models import RegistroAsistencia


@admin.register(RegistroAsistencia)
class RegistroAsistenciaAdmin(admin.ModelAdmin):
    list_display = ['id_trabajador', 'fecha', 'hora_entrada', 'hora_salida', 'estatus', 'created_at']
    search_fields = ['id_trabajador__nombre', 'id_trabajador__apellido_paterno', 'id_trabajador__numero_empleado']
    list_filter = ['estatus', 'fecha', 'created_at']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    date_hierarchy = 'fecha'
    
    fieldsets = (
        ('Información del Registro', {
            'fields': ('id_trabajador', 'fecha', 'hora_entrada', 'hora_salida', 'estatus')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )