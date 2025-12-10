# accounts/models.py

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class PerfilUsuario(models.Model):
    """
    Extiende User con asignación a trabajador y rol del sistema.
    Roles controlan el alcance de inciencias, reportes y acciones.
    """

    ROLES = [
        ('admin', 'Administrador del Sistema'),
        ('jefe', 'Jefe de Área/Supervisor'),
        ('trabajador', 'Trabajador'),
        ('espera', 'En espera'),
    ]

    id_perfil = models.AutoField(primary_key=True)

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='perfil',
        verbose_name="Usuario"
    )

    id_trabajador = models.OneToOneField(
        'trabajadores.Trabajador',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='perfil_usuario',
        verbose_name="Trabajador Asociado"
    )

    rol = models.CharField(
        max_length=50,
        choices=ROLES,
        default='espera',
        verbose_name="Rol"
    )

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'perfil_usuario'
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuario'
        ordering = ['user__username']

    def __str__(self):
        email = self.user.email or self.user.username
        return f"{email} - {self.get_rol_display()}"

    # ============================================================
    #   VERIFICACIÓN DE ROLES
    # ============================================================
    def es_admin(self):
        return self.rol == 'admin'

    def es_jefe(self):
        return self.rol == 'jefe'

    def es_trabajador(self):
        return self.rol == 'trabajador'

    def es_espera(self):
        return self.rol == 'espera'

    # ============================================================
    #   UTILIDADES PARA CONTROL POR UNIDAD (MUY IMPORTANTE)
    # ============================================================
    @property
    def tiene_trabajador(self):
        """Evita errores si el perfil no tiene un trabajador asociado."""
        return self.id_trabajador is not None

    @property
    def unidad(self):
        """Accede de forma segura a la unidad del perfil."""
        if self.id_trabajador and hasattr(self.id_trabajador, "id_unidad"):
            return self.id_trabajador.id_unidad
        return None

    @property
    def puede_autorizar_incidencias(self):
        """Admin y jefe pueden autorizar incidencias."""
        return self.rol in ['admin', 'jefe']

    def puede_ver_reportes(self):
        return self.rol in ['admin', 'jefe']

    def pertenece_a_su_unidad(self, trabajador):
        """
        Verifica si un trabajador dado pertenece a la unidad del jefe.
        Previene errores y evita accesos indebidos.
        """
        if not self.es_jefe():
            return False

        if not self.tiene_trabajador:
            return False

        return trabajador.id_unidad == self.unidad


# ============================================================
#   SEÑALES - creación automática de perfil
# ============================================================

@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    """Crea automáticamente un perfil cuando se crea un usuario."""
    if created:
        PerfilUsuario.objects.create(user=instance, rol='espera')


@receiver(post_save, sender=User)
def guardar_perfil_usuario(sender, instance, **kwargs):
    """Guarda también el perfil cuando el usuario se guarda."""
    if hasattr(instance, 'perfil'):
        instance.perfil.save()
