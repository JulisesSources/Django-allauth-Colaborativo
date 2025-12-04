# accounts/models.py

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class PerfilUsuario(models.Model):
    """
    Modelo para extender User de Django con información adicional
    Relaciona usuarios con trabajadores y define roles
    """
    ROLES = [
        ('admin', 'Administrador del Sistema'),
        ('jefe', 'Jefe de Área/Supervisor'),
        ('trabajador', 'Trabajador'),
        ('espera', 'en espera')
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
    
    rol = models.CharField(
        max_length=50, 
        choices=ROLES, 
        default='espera',
        verbose_name="Rol"
    )
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")
    
    class Meta:
        db_table = 'perfil_usuario'
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuario'
        ordering = ['user__username']
    
    def __str__(self):
        email = self.user.email if self.user.email else self.user.username
        return f"{email} - {self.get_rol_display()}"
    
    def es_admin(self):
        """Verifica si el usuario es administrador"""
        return self.rol == 'admin'
    
    def es_jefe(self):
        """Verifica si el usuario es jefe"""
        return self.rol == 'jefe'
    
    def es_trabajador(self):
        """Verifica si el usuario es trabajador"""
        return self.rol == 'trabajador'
    
    def es_espera(self):
        """Verifica si el usuario es en espera"""
        return self.rol == 'espera'
    
    def puede_autorizar_incidencias(self):
        """Verifica si puede autorizar incidencias"""
        return self.rol in ['admin', 'jefe']
    
    def puede_ver_reportes(self):
        """Verifica si puede ver reportes"""
        return self.rol in ['admin', 'jefe']


# Señal para crear automáticamente el perfil cuando se crea un usuario
@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    """Crea automáticamente un perfil cuando se crea un usuario"""
    if created:
        PerfilUsuario.objects.create(user=instance, rol='espera')


@receiver(post_save, sender=User)
def guardar_perfil_usuario(sender, instance, **kwargs):
    """Guarda el perfil cuando se guarda el usuario"""
    if hasattr(instance, 'perfil'):
        instance.perfil.save()