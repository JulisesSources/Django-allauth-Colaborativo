# apps/incidencias/signals.py

from django.db.models.signals import post_migrate
from django.dispatch import receiver
from apps.incidencias.models import TipoIncidencia

@receiver(post_migrate)
def crear_tipos_incidencia(sender, **kwargs):
    # Solo ejecutar para esta app
    if sender.label != 'apps.incidencias':
        return

    tipos_iniciales = [
        "Incapacidad",
        "Permiso con goce",
        "Comisión sindical",
        "Permiso sin goce",
        "Comisión administrativa",
    ]

    for descripcion in tipos_iniciales:
        TipoIncidencia.objects.get_or_create(
            descripcion=descripcion,
            defaults={
                "requiere_autorizacion": True,
                "activo": True
            }
        )
