# apps/jornadas_laborales/models.py

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


# =========================================================
#   JORNADA LABORAL (Horarios de trabajo)
# =========================================================

class JornadaLaboral(models.Model):
    """
    Modelo para definir jornadas laborales (horarios de trabajo)
    """
    TIPO_JORNADA = [
        ('MAT', 'Jornada Matutina'),
        ('VES', 'Jornada Vespertina'),
        ('NOC', 'Jornada Nocturna'),
        ('COM', 'Jornada Completa'),
        ('MED', 'Media Jornada'),
        ('INT', 'Jornada Intermitente'),
        ('ESP', 'Jornada Especial'),
    ]
    
    id_jornada = models.AutoField(primary_key=True)
    
    # Campo estandarizado con choices
    descripcion = models.CharField(
        max_length=3,
        choices=TIPO_JORNADA,
        verbose_name="Tipo de Jornada",
        help_text="Seleccione el tipo de jornada laboral"
    )
    
    hora_entrada = models.TimeField(verbose_name="Hora de Entrada")
    hora_salida = models.TimeField(verbose_name="Hora de Salida")
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")
    created_by = models.ForeignKey(
        User, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name='jornadas_creadas',
        verbose_name="Creado por"
    )
    updated_by = models.ForeignKey(
        User, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name='jornadas_modificadas',
        verbose_name="Modificado por"
    )
    
    class Meta:
        db_table = 'jornada_laboral'
        verbose_name = 'Jornada Laboral'
        verbose_name_plural = 'Jornadas Laborales'
        ordering = ['descripcion']
    
    def __str__(self):
        return f"{self.get_descripcion_display()} ({self.hora_entrada.strftime('%H:%M')} - {self.hora_salida.strftime('%H:%M')})"
    
    @property
    def descripcion_texto(self):
        """Mantener compatibilidad con código existente"""
        return self.get_descripcion_display()
    
    @property
    def dias_texto(self):
        """Retorna los días en formato texto legible"""
        dias = self.dias.all().order_by('numero_dia')
        if not dias.exists():
            return "Sin días asignados"
        return ', '.join([dia.get_numero_dia_display() for dia in dias])
    
    @property
    def dias_cortos(self):
        """Retorna los días en formato corto"""
        dias = self.dias.all().order_by('numero_dia').values_list('numero_dia', flat=True)
        if not dias:
            return "-"
        
        dias_list = list(dias)
        
        # Si son días consecutivos L-V
        if dias_list == [1, 2, 3, 4, 5]:
            return "L-V"
        elif dias_list == [1, 2, 3, 4, 5, 6]:
            return "L-S"
        elif dias_list == [1, 2, 3, 4, 5, 6, 7]:
            return "L-D"
        else:
            nombres_cortos = {1: 'L', 2: 'M', 3: 'Mi', 4: 'J', 5: 'V', 6: 'S', 7: 'D'}
            return ', '.join([nombres_cortos[d] for d in dias_list])
    
    def clean(self):
        """Validaciones del modelo"""
        from django.core.exceptions import ValidationError
        if self.hora_salida <= self.hora_entrada:
            raise ValidationError({
                'hora_salida': 'La hora de salida debe ser mayor a la hora de entrada'
            })


# =========================================================
#   DÍAS DE LA JORNADA (L, M, Mi, J, V, S, D)
# =========================================================

class JornadaDias(models.Model):
    """
    Modelo para asignar días de la semana a una jornada laboral
    """
    DIAS_SEMANA = [
        (1, 'Lunes'),
        (2, 'Martes'),
        (3, 'Miércoles'),
        (4, 'Jueves'),
        (5, 'Viernes'),
        (6, 'Sábado'),
        (7, 'Domingo'),
    ]
    
    id_jornada_dia = models.AutoField(primary_key=True)
    id_jornada = models.ForeignKey(
        JornadaLaboral, 
        on_delete=models.CASCADE,
        related_name='dias',
        verbose_name="Jornada Laboral"
    )
    numero_dia = models.IntegerField(
        choices=DIAS_SEMANA,
        verbose_name="Día de la Semana"
    )
    
    class Meta:
        db_table = 'jornada_dias'
        verbose_name = 'Día de Jornada'
        verbose_name_plural = 'Días de Jornadas'
        unique_together = [['id_jornada', 'numero_dia']]
        ordering = ['numero_dia']
    
    def __str__(self):
        return f"{self.id_jornada.descripcion} - {self.get_numero_dia_display()}"


# =========================================================
#   CALENDARIO LABORAL (Días festivos/inhábiles)
# =========================================================

class CalendarioLaboral(models.Model):
    """
    Modelo para el calendario laboral (días inhábiles, festivos, etc.)
    """
    id_calendario = models.AutoField(primary_key=True)
    fecha = models.DateField(unique=True, verbose_name="Fecha")
    es_inhabil = models.BooleanField(default=False, verbose_name="¿Es día inhábil?")
    descripcion = models.CharField(max_length=200, blank=True, verbose_name="Descripción",
                                   help_text="Ej: Día festivo, Vacaciones, etc.")
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")
    created_by = models.ForeignKey(
        User, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name='calendarios_creados',
        verbose_name="Creado por"
    )
    updated_by = models.ForeignKey(
        User, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name='calendarios_modificados',
        verbose_name="Modificado por"
    )
    
    class Meta:
        db_table = 'calendario_laboral'
        verbose_name = 'Día del Calendario Laboral'
        verbose_name_plural = 'Calendario Laboral'
        ordering = ['fecha']
    
    def __str__(self):
        estado = "Inhábil" if self.es_inhabil else "Hábil"
        return f"{self.fecha.strftime('%d/%m/%Y')} - {estado}"


# =========================================================
#   ASIGNACIÓN TRABAJADOR-JORNADA (Quién trabaja en qué horario)
# =========================================================

class TrabajadorJornada(models.Model):
    id_trabajador_jornada = models.AutoField(primary_key=True)
    
    # Foreign Keys
    id_trabajador = models.ForeignKey(
        'trabajadores.Trabajador',
        on_delete=models.CASCADE,
        verbose_name="Trabajador",
        related_name='jornadas_asignadas'
    )
    id_jornada = models.ForeignKey(
        JornadaLaboral,
        on_delete=models.PROTECT,
        verbose_name="Jornada Laboral",
        related_name='trabajadores_asignados'
    )
    
    fecha_inicio = models.DateField(verbose_name="Fecha de Inicio")
    fecha_fin = models.DateField(null=True, blank=True, verbose_name="Fecha de Fin",
                                 help_text="Dejar vacío si es vigente actualmente")
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")
    created_by = models.ForeignKey(
        User, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name='trabajador_jornadas_creadas',
        verbose_name="Creado por"
    )
    updated_by = models.ForeignKey(
        User, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name='trabajador_jornadas_modificadas',
        verbose_name="Modificado por"
    )
    
    class Meta:
        db_table = 'trabajador_jornada'
        verbose_name = 'Asignación de Jornada'
        verbose_name_plural = 'Asignaciones de Jornadas'
        ordering = ['-fecha_inicio']
        unique_together = [['id_trabajador', 'fecha_inicio']]
    
    def __str__(self):
        return f"{self.id_trabajador.nombre_completo} - {self.id_jornada.descripcion}"
    
    @property
    def esta_vigente(self):
        """Indica si la jornada está vigente (sin fecha_fin o fecha_fin futura)"""
        from django.utils import timezone
        if not self.fecha_fin:
            return True
        return self.fecha_fin >= timezone.now().date()
    
    def clean(self):
        """Validaciones del modelo"""
        if self.fecha_fin and self.fecha_fin < self.fecha_inicio:
            raise ValidationError({
                'fecha_fin': 'La fecha de fin no puede ser anterior a la fecha de inicio'
            })