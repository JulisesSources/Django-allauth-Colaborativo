from django.db import models
from django.contrib.auth.models import User


class PerfilUsuario(models.Model):
    """
    Modelo para extender User de Django con información adicional
    Relaciona usuarios con trabajadores y define roles
    """
    ROLES = [
        ('admin', 'Administrador del Sistema'),
        ('jefe', 'Jefe de Área/Supervisor'),
        ('trabajador', 'Trabajador'),
    ]
    
    id_perfil = models.AutoField(primary_key=True)
    
    # Relación 1:1 con User de Django
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='perfil',
        verbose_name="Usuario"
    )
    
    # Relación opcional con Trabajador
    id_trabajador = models.OneToOneField(
        'trabajadores.Trabajador',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='perfil_usuario',
        verbose_name="Trabajador Asociado"
    )
    
    rol = models.CharField(max_length=50, choices=ROLES, verbose_name="Rol")
    
    # Auditoría (solo timestamps, no created_by/updated_by para evitar recursión)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")
    
    class Meta:
        db_table = 'perfil_usuario'
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuario'
        ordering = ['user__username']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_rol_display()}"