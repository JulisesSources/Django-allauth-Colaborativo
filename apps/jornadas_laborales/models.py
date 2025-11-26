from django.db import models
from django.contrib.auth.models import User


class JornadaLaboral(models.Model):
    """
    Modelo para definir jornadas laborales (horarios de trabajo)
    """
    id_jornada = models.AutoField(primary_key=True)
    descripcion = models.CharField(max_length=200, verbose_name="Descripción",
                                   help_text="Ej: Jornada Matutina, Jornada Vespertina")
    hora_entrada = models.TimeField(verbose_name="Hora de Entrada")
    hora_salida = models.TimeField(verbose_name="Hora de Salida")
    dias_semana = models.CharField(max_length=20, verbose_name="Días de la Semana",
                                   help_text="Ej: L-V, L-S, o 1,2,3,4,5")
    
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
        return f"{self.descripcion} ({self.hora_entrada.strftime('%H:%M')} - {self.hora_salida.strftime('%H:%M')})"


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


class TrabajadorJornada(models.Model):
    """
    Modelo para asignar jornadas laborales a trabajadores
    (relación N:M entre Trabajador y JornadaLaboral con fechas)
    """
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