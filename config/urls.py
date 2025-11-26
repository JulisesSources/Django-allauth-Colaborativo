"""
URL Configuration for SCA-B123 project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    # Admin de Django
    path('admin/', admin.site.urls),
    
    # URLs de Allauth
    path('accounts/', include('allauth.urls')),
    
    # URLs de las apps del proyecto
    path('trabajadores/', include('apps.trabajadores.urls')),
    path('unidades/', include('apps.unidades.urls')),
    path('jornadas/', include('apps.jornadas_laborales.urls')),
    path('asistencias/', include('apps.asistencias.urls')),
    path('incidencias/', include('apps.incidencias.urls')),
    path('reportes/', include('apps.reportes.urls')),
    
    # Ruta temporal para la home
    path('', TemplateView.as_view(template_name='base.html'), name='home'),
]

# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)