from django.contrib import admin
from .models import RegistroAsistencia


@admin.register(RegistroAsistencia)
class RegistroAsistenciaAdmin(admin.ModelAdmin):
    list_display = [
        'id_trabajador', 
        'fecha', 
        'hora_entrada', 
        'hora_salida', 
        'get_estatus_display_custom',
        'get_minutos_retardo',
        'created_at'
    ]
    search_fields = [
        'id_trabajador__nombre', 
        'id_trabajador__apellido_paterno', 
        'id_trabajador__numero_empleado'
    ]
    list_filter = ['estatus', 'fecha', 'created_at']
    readonly_fields = [
        'created_at', 
        'updated_at', 
        'created_by', 
        'updated_by',
        'minutos_retardo',
        'debe_asistir'
    ]
    date_hierarchy = 'fecha'
    
    def get_estatus_display_custom(self, obj):
        """Mostrar estatus con color"""
        colores = {
            'ASI': '🟢',
            'RET': '🟡',
            'FAL': '🔴',
            'JUS': '🔵'
        }
        return f"{colores.get(obj.estatus, '')} {obj.get_estatus_display()}"
    get_estatus_display_custom.short_description = 'Estatus'
    
    def get_minutos_retardo(self, obj):
        """Mostrar minutos de retardo"""
        if obj.estatus == 'RET':
            return f"{obj.minutos_retardo} min"
        return "-"
    get_minutos_retardo.short_description = 'Retardo'
    
    fieldsets = (
        ('Información del Registro', {
            'fields': ('id_trabajador', 'fecha', 'hora_entrada', 'hora_salida', 'estatus')
        }),
        ('Información Calculada', {
            'fields': ('minutos_retardo', 'debe_asistir'),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['calcular_estatus_automatico']
    
    def calcular_estatus_automatico(self, request, queryset):
        """Acción para recalcular estatus de registros seleccionados"""
        count = 0
        for registro in queryset:
            registro.calcular_estatus_automatico()
            registro.save()
            count += 1
        self.message_user(request, f"{count} registro(s) actualizados")
    calcular_estatus_automatico.short_description = "Recalcular estatus automáticamente"