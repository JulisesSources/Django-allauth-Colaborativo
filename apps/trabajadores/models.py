from django.db import models
from django.contrib.auth.models import User


# ------------------------------
#   PUESTO
# ------------------------------
class Puesto(models.Model):
    id_puesto = models.AutoField(primary_key=True)
    nombre_puesto = models.CharField(max_length=200, verbose_name="Nombre del Puesto")
    nivel = models.CharField(max_length=100, verbose_name="Nivel",
                             help_text="Ej: Docente, Administrativo, Directivo")

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")
    created_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='puestos_creados',
        verbose_name="Creado por"
    )
    updated_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='puestos_modificados',
        verbose_name="Modificado por"
    )

    class Meta:
        db_table = 'puesto'
        verbose_name = 'Puesto'
        verbose_name_plural = 'Puestos'
        ordering = ['nombre_puesto']

    def __str__(self):
        return f"{self.nombre_puesto} ({self.nivel})"


# ------------------------------
#   TIPO DE NOMBRAMIENTO
# ------------------------------
class TipoNombramiento(models.Model):
    id_tipo_nombramiento = models.AutoField(primary_key=True)
    descripcion = models.CharField(max_length=150, verbose_name="Descripción",
                                   help_text="Ej: Base, Confianza, Interino")

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")
    created_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='tipos_nombramiento_creados',
        verbose_name="Creado por"
    )
    updated_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='tipos_nombramiento_modificados',
        verbose_name="Modificado por"
    )

    class Meta:
        db_table = 'tipo_nombramiento'
        verbose_name = 'Tipo de Nombramiento'
        verbose_name_plural = 'Tipos de Nombramiento'
        ordering = ['descripcion']

    def __str__(self):
        return self.descripcion


# ------------------------------
#   TRABAJADOR
# ------------------------------
class Trabajador(models.Model):
    id_trabajador = models.AutoField(primary_key=True)
    numero_empleado = models.CharField(max_length=20, unique=True, verbose_name="Número de Empleado")

    nombre = models.CharField(max_length=150, verbose_name="Nombre(s)")
    apellido_paterno = models.CharField(max_length=150, verbose_name="Apellido Paterno")
    apellido_materno = models.CharField(max_length=150, verbose_name="Apellido Materno")

    rfc = models.CharField(max_length=13, verbose_name="RFC")
    curp = models.CharField(max_length=18, verbose_name="CURP")

    # Relaciones
    id_unidad = models.ForeignKey(
        'unidades.UnidadAdministrativa',
        on_delete=models.PROTECT,
        verbose_name="Unidad Administrativa",
        related_name='trabajadores'
    )
    id_puesto = models.ForeignKey(
        Puesto,
        on_delete=models.PROTECT,
        verbose_name="Puesto",
        related_name='trabajadores'
    )
    id_tipo_nombramiento = models.ForeignKey(
        TipoNombramiento,
        on_delete=models.PROTECT,
        verbose_name="Tipo de Nombramiento",
        related_name='trabajadores'
    )

    activo = models.BooleanField(default=True, verbose_name="Activo")

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")
    created_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='trabajadores_creados',
        verbose_name="Creado por"
    )
    updated_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='trabajadores_modificados',
        verbose_name="Modificado por"
    )

    class Meta:
        db_table = 'trabajador'
        verbose_name = 'Trabajador'
        verbose_name_plural = 'Trabajadores'
        ordering = ['apellido_paterno', 'apellido_materno', 'nombre']

    def __str__(self):
        return f"{self.numero_empleado} - {self.nombre} {self.apellido_paterno} {self.apellido_materno}"

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido_paterno} {self.apellido_materno}"