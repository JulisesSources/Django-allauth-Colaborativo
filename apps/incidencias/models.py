# incidencias/models.py

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone


class TipoIncidencia(models.Model):
    """
    Modelo para tipos de incidencias
    """
    id_tipo_incidencia = models.AutoField(primary_key=True)
    descripcion = models.CharField(
        max_length=200, 
        verbose_name="Descripción",
        help_text="Ej: Incapacidad, Permiso con goce, Comisión sindical"
    )
    requiere_autorizacion = models.BooleanField(
        default=True,
        verbose_name="Requiere Autorización",
        help_text="Define si este tipo de incidencia requiere autorización de un superior"
    )
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo"
    )
    
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
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente de Autorización'),
        ('autorizada', 'Autorizada'),
        ('rechazada', 'Rechazada'),
    ]
    
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
    
    # Estado de la incidencia
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='pendiente',
        verbose_name="Estado"
    )
    
    # Usuario que autorizó la incidencia
    autorizada_por = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='incidencias_autorizadas',
        verbose_name="Autorizada por"
    )
    fecha_autorizacion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de Autorización"
    )
    comentario_autorizacion = models.TextField(
        blank=True,
        verbose_name="Comentario de Autorización"
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
        ordering = ['-fecha_inicio', '-created_at']
    
    def __str__(self):
        return f"{self.id_trabajador.nombre_completo} - {self.id_tipo_incidencia.descripcion} ({self.fecha_inicio.strftime('%d/%m/%Y')})"
    
    def clean(self):
        """Validaciones personalizadas"""
        if self.fecha_fin < self.fecha_inicio:
            raise ValidationError('La fecha de fin no puede ser anterior a la fecha de inicio.')
        
        # Validar que no haya solapamiento de fechas para el mismo trabajador
        if self.id_trabajador:
            incidencias_existentes = Incidencia.objects.filter(
                id_trabajador=self.id_trabajador,
                estado__in=['pendiente', 'autorizada']
            ).exclude(id_incidencia=self.id_incidencia)
            
            for inc in incidencias_existentes:
                if (self.fecha_inicio <= inc.fecha_fin and self.fecha_fin >= inc.fecha_inicio):
                    raise ValidationError(
                        f'Ya existe una incidencia para este trabajador en el periodo seleccionado: '
                        f'{inc.id_tipo_incidencia.descripcion} ({inc.fecha_inicio} - {inc.fecha_fin})'
                    )
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def duracion_dias(self):
        """Calcula la duración de la incidencia en días"""
        return (self.fecha_fin - self.fecha_inicio).days + 1
    
    @property
    def nombre_completo(self):
        """Alias para compatibilidad"""
        return self.id_trabajador.nombre_completo if self.id_trabajador else "Sin trabajador"
    
    def puede_ser_autorizada(self):
        """Verifica si la incidencia puede ser autorizada"""
        return self.estado == 'pendiente'
    
    def puede_ser_editada(self):
        """Verifica si la incidencia puede ser editada"""
        return self.estado == 'pendiente'
    
    def autorizar(self, usuario, comentario=''):
        """Autoriza la incidencia"""
        self.estado = 'autorizada'
        self.autorizada_por = usuario
        self.fecha_autorizacion = timezone.now()
        self.comentario_autorizacion = comentario
        self.updated_by = usuario
        self.save()
    
    def rechazar(self, usuario, comentario=''):
        """Rechaza la incidencia"""
        self.estado = 'rechazada'
        self.autorizada_por = usuario
        self.fecha_autorizacion = timezone.now()
        self.comentario_autorizacion = comentario
        self.updated_by = usuario
        self.save()