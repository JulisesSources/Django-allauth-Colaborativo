# apps/asistencias/urls.py

from django.urls import path
from . import views

app_name = 'asistencias'

urlpatterns = [

    # ========== LISTA DE ASISTENCIAS ==========
    path('', views.AsistenciaListView.as_view(), name='index'),
    path('lista/', views.AsistenciaListView.as_view(), name='lista'),

    # ===================== REGISTRO RÁPIDO =====================
    # Checador simplificado: selecciona trabajador y registra
    # Detecta automáticamente si es entrada o salida
    path('registro-rapido/', views.RegistroRapidoView.as_view(), name='registro_rapido'),

    # ===================== REGISTRO MANUAL =====================
    # Formulario completo con todos los campos
    # Permite especificar fecha, horas y estatus
    path('registrar/', views.RegistroAsistenciaCreateView.as_view(), name='registrar'),

    # ===================== DETALLE =====================
    # Vista de detalle de un registro específico
    # Muestra información completa y auditoría
    path('<int:pk>/', views.AsistenciaDetailView.as_view(), name='detalle'),

    # ===================== RESUMEN TRABAJADOR =====================
    # Estadísticas de asistencia de un trabajador
    # Muestra: asistencias, retardos, faltas, porcentajes
    path('resumen/<str:numero_empleado>/', views.ResumenTrabajadorView.as_view(),name='resumen'),

    # ===================== MI REGISTRO =====================
    # Vista personal del trabajador para registrar su asistencia
    # Muestra estado actual y permite registrar entrada/salida
    path('mi-registro/', views.RegistrarMiAsistenciaView.as_view(), name='mi_registro'),
]
