# apps/jornadas_laborales/urls.py

from django.urls import path
from . import views

app_name = 'jornadas'

urlpatterns = [

    # ========== JORNADAS LABORALES ==========
    path('', views.JornadaListView.as_view(), name='list'),
    path('<int:pk>/', views.JornadaDetailView.as_view(), name='detail'),
    path('crear/', views.JornadaCreateView.as_view(), name='create'),
    path('<int:pk>/editar/', views.JornadaUpdateView.as_view(), name='update'),
    path('<int:pk>/eliminar/', views.JornadaDeleteView.as_view(), name='delete'),

    # ========== CALENDARIO LABORAL ==========
    path('calendario/', views.CalendarioListView.as_view(), name='calendario'),
    path('calendario/crear/', views.CalendarioCreateView.as_view(), name='calendario_crear'),
    path('calendario/<int:pk>/editar/', views.CalendarioUpdateView.as_view(), name='calendario_editar'),
    path('calendario/<int:pk>/eliminar/', views.CalendarioDeleteView.as_view(), name='calendario_eliminar'),

    # ========== ASIGNACIONES ==========
    path('asignaciones/', views.AsignacionListView.as_view(), name='asignaciones'),
    path('asignaciones/crear/', views.AsignacionCreateView.as_view(), name='asignacion_crear'),
    path('asignaciones/<int:pk>/editar/', views.AsignacionUpdateView.as_view(), name='asignacion_editar'),
    path('asignaciones/<int:pk>/eliminar/', views.AsignacionDeleteView.as_view(), name='asignacion_eliminar'),

    # ========== MI JORNADA (Trabajador) ==========
    path('mi-jornada/', views.MiJornadaView.as_view(), name='mi_jornada'),
]