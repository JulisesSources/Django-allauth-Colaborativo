from django.db import models
from django.contrib.auth.models import User


class RegistroAsistencia(models.Model):
    """
    Modelo para registrar la asistencia diaria de los trabajadores
    """
    ESTATUS_CHOICES = [
        ('asistencia', 'Asistencia Normal'),
        ('retardo', 'Retardo'),
        ('falta', 'Falta'),
        ('falta_justificada', 'Falta Justificada'),
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
    estatus = models.CharField(max_length=50, choices=ESTATUS_CHOICES, verbose_name="Estatus")
    
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