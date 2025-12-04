from django.db import models
from django.contrib.auth.models import User


class UnidadAdministrativa(models.Model):
    """
    Modelo para unidades administrativas (departamentos, academias, áreas)
    SIN jerarquías.
    """
    id_unidad = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=200, verbose_name="Nombre de la Unidad")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")
    created_by = models.ForeignKey(
        User, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name='unidades_creadas',
        verbose_name="Creado por"
    )
    updated_by = models.ForeignKey(
        User, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name='unidades_modificadas',
        verbose_name="Modificado por"
    )

    class Meta:
        db_table = 'unidad_administrativa'
        verbose_name = 'Unidad Administrativa'
        verbose_name_plural = 'Unidades Administrativas'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre
