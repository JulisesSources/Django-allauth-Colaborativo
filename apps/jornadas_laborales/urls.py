from django.urls import path
from . import views

app_name = 'jornadas'

urlpatterns = [
    # ========== JORNADAS LABORALES ==========
    # Lista y detalle
    path('', views.JornadaListView.as_view(), name='list'),
    path('<int:pk>/', views.JornadaDetailView.as_view(), name='detail'),
    
    # CRUD Jornadas (Jefe + Admin)
    path('crear/', views.JornadaCreateView.as_view(), name='create'),
    path('<int:pk>/editar/', views.JornadaUpdateView.as_view(), name='update'),
    path('<int:pk>/eliminar/', views.JornadaDeleteView.as_view(), name='delete'),
    
    # ========== CALENDARIO LABORAL ==========
    # Lista (todos los roles)
    path('calendario/', views.CalendarioListView.as_view(), name='calendario'),
    
    # CRUD Calendario (Jefe + Admin)
    path('calendario/crear/', views.CalendarioCreateView.as_view(), name='calendario_crear'),
    path('calendario/<int:pk>/editar/', views.CalendarioUpdateView.as_view(), name='calendario_editar'),
    path('calendario/<int:pk>/eliminar/', views.CalendarioDeleteView.as_view(), name='calendario_eliminaxr'),
    
    # ========== ASIGNACIONES DE JORNADAS ==========
    # Lista y CRUD (Jefe + Admin)
    path('asignaciones/', views.AsignacionListView.as_view(), name='asignaciones'),
    path('asignaciones/crear/', views.AsignacionCreateView.as_view(), name='asignacion_crear'),
    path('asignaciones/<int:pk>/editar/', views.AsignacionUpdateView.as_view(), name='asignacion_editar'),
    path('asignaciones/<int:pk>/eliminar/', views.AsignacionDeleteView.as_view(), name='asignacion_eliminar'),
    
    # ========== MI JORNADA (Trabajador) ==========
    path('mi-jornada/', views.MiJornadaView.as_view(), name='mi_jornada'),
]