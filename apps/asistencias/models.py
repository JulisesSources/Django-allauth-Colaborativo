from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from datetime import date


class RegistroAsistencia(models.Model):
    """
    Modelo para registrar la asistencia diaria de los trabajadores
    """
    ESTATUS_CHOICES = [
        ('ASI', 'Asistencia Normal'),
        ('RET', 'Retardo'),
        ('FAL', 'Falta'),
        ('JUS', 'Falta Justificada'),
    ]
    
    id_registro = models.AutoField(primary_key=True)
    
    # Foreign Key
    id_trabajador = models.ForeignKey(
        'trabajadores.Trabajador',
        on_delete=models.CASCADE,
        verbose_name="Trabajador",
        related_name='registros_asistencia'
    )
    
    fecha = models.DateField(verbose_name="Fecha")
    hora_entrada = models.TimeField(null=True, blank=True, verbose_name="Hora de Entrada")
    hora_salida = models.TimeField(null=True, blank=True, verbose_name="Hora de Salida")
    estatus = models.CharField(
        max_length=3, 
        choices=ESTATUS_CHOICES, 
        verbose_name="Estatus",
        default='FAL'
    )
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")
    created_by = models.ForeignKey(
        User, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name='registros_creados',
        verbose_name="Creado por"
    )
    updated_by = models.ForeignKey(
        User, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name='registros_modificados',
        verbose_name="Modificado por"
    )
    
    class Meta:
        db_table = 'registro_asistencia'
        verbose_name = 'Registro de Asistencia'
        verbose_name_plural = 'Registros de Asistencia'
        ordering = ['-fecha', 'id_trabajador']
        unique_together = [['id_trabajador', 'fecha']]
    
    def __str__(self):
        return f"{self.id_trabajador.nombre_completo} - {self.fecha.strftime('%d/%m/%Y')} - {self.get_estatus_display()}"
    
    def calcular_estatus_automatico(self):
        """
        Calcula el estatus basado en la hora de entrada y la jornada del trabajador
        """
        from apps.asistencias.utils import calcular_estatus_asistencia
        
        estatus = calcular_estatus_asistencia(
            self.id_trabajador,
            self.fecha,
            self.hora_entrada,
            self.hora_salida
        )
        self.estatus = estatus
        return estatus
    
    @property
    def minutos_retardo(self):
        """
        Calcula los minutos de retardo si aplica
        """
        if self.estatus != 'RET':
            return 0
        
        from apps.asistencias.utils import calcular_minutos_retardo
        return calcular_minutos_retardo(
            self.id_trabajador,
            self.fecha,
            self.hora_entrada
        )
    
    @property
    def debe_asistir(self):
        """
        Indica si el trabajador debía asistir ese día
        """
        from apps.asistencias.utils import trabajador_debe_asistir
        debe, _ = trabajador_debe_asistir(self.id_trabajador, self.fecha)
        return debe
    
    def clean(self):
        """Validaciones del modelo"""
        from apps.asistencias.utils import validar_registro_asistencia
        
        # Validar que no sea fecha futura
        if self.fecha and self.fecha > date.today():
            raise ValidationError({
                'fecha': 'No se puede registrar asistencia en fechas futuras'
            })
        
        # Validar coherencia de horas
        if self.hora_salida and self.hora_entrada:
            if self.hora_salida <= self.hora_entrada:
                raise ValidationError({
                    'hora_salida': 'La hora de salida debe ser posterior a la hora de entrada'
                })
        
        # Si hay hora de salida, debe haber hora de entrada
        if self.hora_salida and not self.hora_entrada:
            raise ValidationError({
                'hora_entrada': 'Debe registrar hora de entrada antes de la salida'
            })
    
    def save(self, *args, **kwargs):
        """
        Override save para calcular estatus automáticamente si no se especifica
        """
        # Si hay hora de entrada pero no hay estatus, calcularlo
        if self.hora_entrada and not self.estatus:
            self.calcular_estatus_automatico()
        
        # Si no hay hora de entrada y no hay estatus, marcar como falta
        if not self.hora_entrada and not self.estatus:
            self.estatus = 'FAL'
        
        super().save(*args, **kwargs)