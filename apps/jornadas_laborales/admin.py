from django.contrib import admin
from .models import JornadaLaboral, JornadaDias, CalendarioLaboral, TrabajadorJornada


class JornadaDiasInline(admin.TabularInline):
    """Inline para agregar días dentro de la jornada"""
    model = JornadaDias
    extra = 1
    fields = ['numero_dia']
    verbose_name = "Día"
    verbose_name_plural = "Días de la Jornada"


@admin.register(JornadaLaboral)
class JornadaLaboralAdmin(admin.ModelAdmin):
    list_display = ['descripcion', 'hora_entrada', 'hora_salida', 'get_dias', 'created_at']
    search_fields = ['descripcion']
    list_filter = ['created_at', 'dias__numero_dia']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by', 'dias_texto']
    inlines = [JornadaDiasInline]
    
    def get_dias(self, obj):
        """Mostrar días en formato corto en la lista"""
        return obj.dias_cortos
    get_dias.short_description = 'Días'
    
    fieldsets = (
        ('Información de la Jornada', {
            'fields': ('descripcion', 'hora_entrada', 'hora_salida')
        }),
        ('Días Asignados', {
            'fields': ('dias_texto',),
            'description': 'Los días se gestionan en la sección inferior'
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(JornadaDias)
class JornadaDiasAdmin(admin.ModelAdmin):
    list_display = ['id_jornada', 'get_dia_nombre', 'numero_dia']
    list_filter = ['numero_dia', 'id_jornada']
    search_fields = ['id_jornada__descripcion']
    
    def get_dia_nombre(self, obj):
        return obj.get_numero_dia_display()
    get_dia_nombre.short_description = 'Día'


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
    list_display = ['id_trabajador', 'id_jornada', 'fecha_inicio', 'fecha_fin', 'get_esta_vigente', 'created_at']
    search_fields = ['id_trabajador__nombre', 'id_trabajador__apellido_paterno', 'id_trabajador__numero_empleado']
    list_filter = ['id_jornada', 'fecha_inicio']  # ← QUITAR 'esta_vigente'
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    date_hierarchy = 'fecha_inicio'
    
    def get_esta_vigente(self, obj):
        """Mostrar si la jornada está vigente en la lista"""
        if obj.esta_vigente:
            return "✅ Vigente"
        return "❌ Finalizada"
    get_esta_vigente.short_description = 'Estado'
    
    fieldsets = (
        ('Asignación de Jornada', {
            'fields': ('id_trabajador', 'id_jornada', 'fecha_inicio', 'fecha_fin')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )