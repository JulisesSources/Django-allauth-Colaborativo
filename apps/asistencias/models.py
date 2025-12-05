# apps/asistencias/models.py

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from datetime import date


# =========================================================
#   MODELO PRINCIPAL: REGISTRO DE ASISTENCIA
# =========================================================

class RegistroAsistencia(models.Model):
    """
    Representa un registro diario de asistencia de un trabajador.
    
    Cada registro corresponde a una FECHA + TRABAJADOR.
    Se controla:
        - hora de entrada
        - hora de salida
        - estatus (asistencia, retardo, falta...)
        - auditoría
    """

    # -----------------------------
    #   OPCIONES DE ESTATUS
    # -----------------------------
    ESTATUS_CHOICES = [
        ('ASI', 'Asistencia Normal'),
        ('RET', 'Retardo'),
        ('FAL', 'Falta'),
        ('JUS', 'Falta Justificada'),
    ]

    # -----------------------------
    #   CAMPOS PRINCIPALES
    # -----------------------------
    id_registro = models.AutoField(primary_key=True)

    id_trabajador = models.ForeignKey(
        'trabajadores.Trabajador',
        on_delete=models.CASCADE,
        verbose_name="Trabajador",
        related_name='registros_asistencia'
    )

    fecha = models.DateField(verbose_name="Fecha")

    hora_entrada = models.TimeField(
        null=True,
        blank=True,
        verbose_name="Hora de Entrada"
    )

    hora_salida = models.TimeField(
        null=True,
        blank=True,
        verbose_name="Hora de Salida"
    )

    estatus = models.CharField(
        max_length=3,
        choices=ESTATUS_CHOICES,
        default='FAL',
        verbose_name="Estatus"
    )

    # -----------------------------
    #   CAMPOS DE AUDITORÍA
    # -----------------------------
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Creación"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Actualización"
    )

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

    # -----------------------------
    #   CONFIGURACIÓN META
    # -----------------------------
    class Meta:
        db_table = 'registro_asistencia'
        verbose_name = 'Registro de Asistencia'
        verbose_name_plural = 'Registros de Asistencia'
        ordering = ['-fecha', 'id_trabajador']
        unique_together = [['id_trabajador', 'fecha']]
        # Garantiza: solo un registro por trabajador por día

    # -----------------------------
    #   REPRESENTACIÓN
    # -----------------------------
    def __str__(self):
        return (
            f"{self.id_trabajador.nombre_completo} "
            f"- {self.fecha.strftime('%d/%m/%Y')} "
            f"- {self.get_estatus_display()}"
        )

    # =========================================================
    #   LÓGICA DE CÁLCULO (utils.py)
    # =========================================================

    def calcular_estatus_automatico(self):
        """
        Calcula el estatus del registro en base a las horas
        y la jornada laboral del trabajador.
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

    # -----------------------------
    #   PROPIEDADES CALCULADAS
    # -----------------------------
    @property
    def minutos_retardo(self):
        """
        Regresa los minutos de retardo solo si el estatus es RET.
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
        Indica si el trabajador debía asistir esa fecha
        (según jornada asignada y calendario laboral).
        """
        from apps.asistencias.utils import trabajador_debe_asistir
        debe, _ = trabajador_debe_asistir(self.id_trabajador, self.fecha)
        return debe

    # =========================================================
    #   VALIDACIONES DEL MODELO
    # =========================================================

    def clean(self):
        """Validaciones de coherencia del registro."""
        from apps.asistencias.utils import validar_registro_asistencia

        # Evitar fechas futuras
        if self.fecha and self.fecha > date.today():
            raise ValidationError({
                'fecha': 'No se puede registrar asistencia en fechas futuras'
            })

        # Coherencia entre entrada y salida
        if self.hora_salida and self.hora_entrada:
            if self.hora_salida <= self.hora_entrada:
                raise ValidationError({
                    'hora_salida': 'La hora de salida debe ser posterior a la hora de entrada'
                })

        # No permitir salida sin entrada
        if self.hora_salida and not self.hora_entrada:
            raise ValidationError({
                'hora_entrada': 'Debe registrar hora de entrada antes de la salida'
            })

    # =========================================================
    #   SAVE OVERRIDE
    # =========================================================

    def save(self, *args, **kwargs):
        """
        Override para calcular estatus automáticamente cuando aplique.
        """

        # Si hay hora de entrada pero no se estableció estatus
        if self.hora_entrada and not self.estatus:
            self.calcular_estatus_automatico()

        # Si no hay entrada y no se ha definido estatus → falta
        if not self.hora_entrada and not self.estatus:
            self.estatus = 'FAL'

        super().save(*args, **kwargs)
