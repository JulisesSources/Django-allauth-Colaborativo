from django.urls import path
from . import views

app_name = 'asistencias'

urlpatterns = [

    # Lista
    path('', views.AsistenciaListView.as_view(), name='index'),
    path('lista/', views.AsistenciaListView.as_view(), name='lista'),

    # Registro rápido
    path('registro-rapido/', views.RegistroRapidoView.as_view(), name='registro_rapido'),

    # Registro manual
    path('registrar/', views.RegistroAsistenciaCreateView.as_view(), name='registrar'),

    # Detalle
    path('<int:pk>/', views.AsistenciaDetailView.as_view(), name='detalle'),

    # Resumen trabajador
    path(
        'resumen/<str:numero_empleado>/',
        views.ResumenTrabajadorView.as_view(),
        name='resumen'
    ),

    # 👇 CORREGIDO: agregar "views."
    path(
        'mi-registro/',
        views.RegistrarMiAsistenciaView.as_view(),
        name='mi_registro'
    ),
]
