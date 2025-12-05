from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone


# ============================================================
#   MODELO: TipoIncidencia
# ============================================================
class TipoIncidencia(models.Model):
    """
    Catálogo de tipos de incidencias.
    """
    id_tipo_incidencia = models.AutoField(primary_key=True)

    descripcion = models.CharField(
        max_length=200,
        verbose_name="Descripción",
        help_text="Ej: Incapacidad, Permiso con goce, etc."
    )

    requiere_autorizacion = models.BooleanField(
        default=True,
        verbose_name="Requiere autorización"
    )

    activo = models.BooleanField(default=True)

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="tipos_incidencia_creados"
    )
    updated_by = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="tipos_incidencia_modificados"
    )

    class Meta:
        db_table = "tipo_incidencia"
        verbose_name = "Tipo de Incidencia"
        verbose_name_plural = "Tipos de Incidencia"
        ordering = ["descripcion"]

    def __str__(self):
        return self.descripcion


# ============================================================
#   MODELO: Incidencia
# ============================================================
class Incidencia(models.Model):
    """
    Registro de incidencias de trabajadores.
    """

    ESTADO_CHOICES = [
        ("pendiente", "Pendiente de Autorización"),
        ("autorizada", "Autorizada"),
        ("rechazada", "Rechazada"),
    ]

    id_incidencia = models.AutoField(primary_key=True)

    id_trabajador = models.ForeignKey(
        "trabajadores.Trabajador",
        on_delete=models.CASCADE,
        related_name="incidencias",
        verbose_name="Trabajador"
    )

    id_tipo_incidencia = models.ForeignKey(
        TipoIncidencia,
        on_delete=models.PROTECT,
        related_name="incidencias",
        verbose_name="Tipo de Incidencia"
    )

    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    observaciones = models.TextField(blank=True)

    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default="pendiente"
    )

    autorizada_por = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="incidencias_autorizadas"
    )

    fecha_autorizacion = models.DateTimeField(null=True, blank=True)
    comentario_autorizacion = models.TextField(blank=True)

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="incidencias_creadas"
    )
    updated_by = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="incidencias_modificadas"
    )

    class Meta:
        db_table = "incidencia"
        verbose_name = "Incidencia"
        verbose_name_plural = "Incidencias"
        ordering = ["-fecha_inicio", "-created_at"]

    def __str__(self):
        return f"{self.id_trabajador.nombre_completo} - {self.id_tipo_incidencia.descripcion}"

    # ============================================================
    #   PERMISOS DE ACCESO
    # ============================================================

    def usuario_puede_ver(self, user):
        perfil = user.perfil

        if perfil.es_admin():
            return True

        if perfil.es_jefe():
            return self.id_trabajador.id_unidad == perfil.id_trabajador.id_unidad

        if perfil.es_trabajador():
            return self.id_trabajador == perfil.id_trabajador

        return False

    def usuario_puede_editar(self, user):
        perfil = user.perfil

        if self.estado != "pendiente":
            return False

        if perfil.es_admin():
            return True

        if perfil.es_jefe():
            return self.id_trabajador.id_unidad == perfil.id_trabajador.id_unidad

        if perfil.es_trabajador():
            return self.id_trabajador == perfil.id_trabajador

        return False

    def usuario_puede_autorizar(self, user):
        perfil = user.perfil

        if self.estado != "pendiente":
            return False

        if perfil.es_admin():
            return True

        if perfil.es_jefe():
            return self.id_trabajador.id_unidad == perfil.id_trabajador.id_unidad

        return False

    def usuario_puede_eliminar(self, user):
        perfil = user.perfil

        if perfil.es_admin():
            return True

        if perfil.es_trabajador() and self.created_by == user and self.estado == "pendiente":
            return True

        return False

    # ============================================================
    #   VALIDACIONES DEL MODELO
    # ============================================================

    def clean(self):
        # Validar fechas
        if self.fecha_fin < self.fecha_inicio:
            raise ValidationError("La fecha final no puede ser anterior a la fecha inicial.")

        # Solapamiento
        qs = Incidencia.objects.filter(
            id_trabajador=self.id_trabajador,
            estado__in=["pendiente", "autorizada"]
        ).exclude(id_incidencia=self.id_incidencia)

        for inc in qs:
            if self.fecha_inicio <= inc.fecha_fin and self.fecha_fin >= inc.fecha_inicio:
                raise ValidationError(
                    f"Ya existe una incidencia en el periodo {inc.fecha_inicio} → {inc.fecha_fin}."
                )

        # Seguridad: jefe no puede registrar incidencias fuera de su unidad
        if self.created_by and hasattr(self.created_by, "perfil"):
            perfil = self.created_by.perfil
            if perfil.es_jefe():
                if perfil.id_trabajador and perfil.id_trabajador.id_unidad:
                    if self.id_trabajador.id_unidad != perfil.id_trabajador.id_unidad:
                        raise ValidationError("No puedes registrar incidencias para trabajadores fuera de tu unidad.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    # ============================================================
    #   FUNCIONES DE ESTADO
    # ============================================================

    @property
    def duracion_dias(self):
        return (self.fecha_fin - self.fecha_inicio).days + 1

    @property
    def puede_ser_autorizada(self):
        return self.estado == "pendiente"

    @property
    def puede_ser_editada(self):
        return self.estado == "pendiente"

    def autorizar(self, usuario, comentario=""):
        self.estado = "autorizada"
        self.autorizada_por = usuario
        self.fecha_autorizacion = timezone.now()
        self.comentario_autorizacion = comentario
        self.updated_by = usuario
        self.save()

    def rechazar(self, usuario, comentario=""):
        self.estado = "rechazada"
        self.autorizada_por = usuario
        self.fecha_autorizacion = timezone.now()
        self.comentario_autorizacion = comentario
        self.updated_by = usuario
        self.save()
