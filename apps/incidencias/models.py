from django.db import models
from django.contrib.auth.models import User


class TipoIncidencia(models.Model):
    """
    Modelo para tipos de incidencias
    """
    id_tipo_incidencia = models.AutoField(primary_key=True)
    descripcion = models.CharField(max_length=200, verbose_name="Descripción",
                                   help_text="Ej: Incapacidad, Permiso con goce, Comisión sindical")
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")
    created_by = models.ForeignKey(
        User, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name='tipos_incidencia_creados',
        verbose_name="Creado por"
    )
    updated_by = models.ForeignKey(
        User, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name='tipos_incidencia_modificados',
        verbose_name="Modificado por"
    )
    
    class Meta:
        db_table = 'tipo_incidencia'
        verbose_name = 'Tipo de Incidencia'
        verbose_name_plural = 'Tipos de Incidencias'
        ordering = ['descripcion']
    
    def __str__(self):
        return self.descripcion


class Incidencia(models.Model):
    """
    Modelo para registrar incidencias de trabajadores
    """
    id_incidencia = models.AutoField(primary_key=True)
    
    # Foreign Keys
    id_trabajador = models.ForeignKey(
        'trabajadores.Trabajador',
        on_delete=models.CASCADE,
        verbose_name="Trabajador",
        related_name='incidencias'
    )
    id_tipo_incidencia = models.ForeignKey(
        TipoIncidencia,
        on_delete=models.PROTECT,
        verbose_name="Tipo de Incidencia",
        related_name='incidencias'
    )
    
    fecha_inicio = models.DateField(verbose_name="Fecha de Inicio")
    fecha_fin = models.DateField(verbose_name="Fecha de Fin")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")
    
    # Usuario que autorizó la incidencia
    autorizada_por = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='incidencias_autorizadas',
        verbose_name="Autorizada por"
    )
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")
    created_by = models.ForeignKey(
        User, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name='incidencias_creadas',
        verbose_name="Creado por"
    )
    updated_by = models.ForeignKey(
        User, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name='incidencias_modificadas',
        verbose_name="Modificado por"
    )
    
    class Meta:
        db_table = 'incidencia'
        verbose_name = 'Incidencia'
        verbose_name_plural = 'Incidencias'
        ordering = ['-fecha_inicio']
    
    def __str__(self):
        return f"{self.id_trabajador.nombre_completo} - {self.id_tipo_incidencia.descripcion} ({self.fecha_inicio.strftime('%d/%m/%Y')})"
    
    @property
    def duracion_dias(self):
        """Calcula la duración de la incidencia en días"""
        return (self.fecha_fin - self.fecha_inicio).days + 1