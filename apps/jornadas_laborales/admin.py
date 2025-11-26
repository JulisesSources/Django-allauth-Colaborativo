from django.contrib import admin
from .models import JornadaLaboral, CalendarioLaboral, TrabajadorJornada


@admin.register(JornadaLaboral)
class JornadaLaboralAdmin(admin.ModelAdmin):
    list_display = ['descripcion', 'hora_entrada', 'hora_salida', 'dias_semana', 'created_at']
    search_fields = ['descripcion']
    list_filter = ['created_at']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    
    fieldsets = (
        ('Información de la Jornada', {
            'fields': ('descripcion', 'hora_entrada', 'hora_salida', 'dias_semana')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CalendarioLaboral)
class CalendarioLaboralAdmin(admin.ModelAdmin):
    list_display = ['fecha', 'es_inhabil', 'descripcion', 'created_at']
    search_fields = ['descripcion']
    list_filter = ['es_inhabil', 'fecha']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    date_hierarchy = 'fecha'
    
    fieldsets = (
        ('Información del Día', {
            'fields': ('fecha', 'es_inhabil', 'descripcion')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TrabajadorJornada)
class TrabajadorJornadaAdmin(admin.ModelAdmin):
    list_display = ['id_trabajador', 'id_jornada', 'fecha_inicio', 'fecha_fin', 'esta_vigente', 'created_at']
    search_fields = ['id_trabajador__nombre', 'id_trabajador__apellido_paterno', 'id_trabajador__numero_empleado']
    list_filter = ['id_jornada', 'fecha_inicio']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by', 'esta_vigente']
    date_hierarchy = 'fecha_inicio'
    
    fieldsets = (
        ('Asignación de Jornada', {
            'fields': ('id_trabajador', 'id_jornada', 'fecha_inicio', 'fecha_fin')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by', 'esta_vigente'),
            'classes': ('collapse',)
        }),
    )