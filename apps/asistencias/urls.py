from django.urls import path
from . import views

app_name = 'asistencias'

urlpatterns = [
    # Lista y filtros
    path('', views.AsistenciaListView.as_view(), name='index'),
    path('lista/', views.AsistenciaListView.as_view(), name='lista'),
    
    # Registro rápido
    path('registro-rapido/', views.RegistroRapidoView.as_view(), name='registro_rapido'),
    
    # Registro completo
    path('registrar/', views.RegistroAsistenciaCreateView.as_view(), name='registrar'),
    
    # Detalle
    path('<int:pk>/', views.AsistenciaDetailView.as_view(), name='detalle'),
    
    # Resumen por trabajador
    path('resumen/<int:trabajador_id>/', views.ResumenTrabajadorView.as_view(), name='resumen_trabajador'),
]